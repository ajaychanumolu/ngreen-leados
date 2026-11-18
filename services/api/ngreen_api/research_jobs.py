"""Execute one research run. Queries are saved before the provider is called."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from ngreen_api.catalog_seed import open_research_opportunity
from ngreen_api.db import get_session_factory
from ngreen_api.models import (
    Company,
    CompanyProductNeed,
    EvidenceClaim,
    Industry,
    Product,
    ResearchAssessment,
    ResearchCandidate,
    ResearchQuery,
    ResearchRun,
    Source,
    UsageEvent,
)
from ngreen_api.records import audit
from ngreen_api.research_extract import assess_sources
from ngreen_api.research_search import (
    DemoProvider,
    Hit,
    ProviderOutage,
    content_hash,
    looks_like_packaging_seller,
    plan_queries,
    provider_for,
    public_domain,
)
from ngreen_api.settings import get_settings
from ngreen_contracts.taxonomy import normalize_company_name

_lock = threading.Lock()
_hits: dict[str, list[float]] = {}


def research_is_limited(key: str, *, limit: int = 5, window: float = 60) -> bool:
    import time

    now = time.monotonic()
    with _lock:
        recent = [stamp for stamp in _hits.get(key, []) if now - stamp < window]
        if len(recent) >= limit:
            _hits[key] = recent
            return True
        recent.append(now)
        _hits[key] = recent
        return False


def reset_research_limits() -> None:
    with _lock:
        _hits.clear()


def dispatch(run_id: str) -> str:
    worker = get_settings().research_worker
    if worker == "sync":
        execute_run(run_id)
        return "sync"
    if worker == "redis":
        try:
            from ngreen_api.research_broker import send_run

            send_run(run_id)
            return "redis"
        except Exception:
            worker = "inline"
    threading.Thread(target=execute_run, args=(run_id,), daemon=True).start()
    return worker


def execute_run(run_id: str) -> None:
    db = get_session_factory()()
    try:
        run = db.get(ResearchRun, uuid.UUID(run_id))
        if run is None or run.status in {"cancelled", "completed", "failed", "capped"}:
            return
        product = db.get(Product, run.product_id)
        industry = db.get(Industry, run.industry_id) if run.industry_id else None
        if product is None:
            _finish(db, run, "failed", "Product is missing.")
            return
        queries = _ensure_queries(db, run, product.name, industry.name if industry else None)
        provider = provider_for(get_settings().serper_api_key)
        run.status = "running"
        run.mode = "demo" if isinstance(provider, DemoProvider) else "live"
        run.started_at = run.started_at or datetime.now(UTC)
        db.commit()
        for query in queries:
            db.expire_all()
            current = db.get(ResearchRun, run.id)
            if current is None or current.status == "cancelled":
                return
            if current.spent_credits >= current.budget_credits:
                _finish(db, current, "capped", "Spend cap reached before the next query.")
                return
            if _candidate_count(db, current) >= current.limit_companies:
                _finish(db, current, "completed", None)
                return
            if query.status == "ok":
                continue
            try:
                hits = provider.search(query.query_text, current.max_results_per_query)
            except ProviderOutage as exc:
                query.status = "error"
                query.error = str(exc)[:500]
                _finish(db, current, "failed", str(exc)[:500])
                return
            db.expire_all()
            current = db.get(ResearchRun, run.id)
            query = db.get(ResearchQuery, query.id)
            if current is None or query is None:
                return
            if current.status == "cancelled":
                query.status = "skipped"
                current.spent_credits += 1
                current.queries_done += 1
                current.finished_at = datetime.now(UTC)
                db.commit()
                return
            stored, skipped, sellers = _store_hits(db, current, query, provider.name, hits)
            _refresh_assessments(db, current, product.name, industry.name if industry else None)
            current.spent_credits += 1
            current.queries_done += 1
            query.status = "ok"
            query.result_count = stored
            query.known_skipped = skipped
            query.seller_skipped = sellers
            db.add(
                UsageEvent(
                    organization_id=current.organization_id,
                    run_id=current.id,
                    kind="search",
                    units=1,
                    mode=current.mode,
                )
            )
            db.commit()
        db.expire_all()
        finished = db.get(ResearchRun, run.id)
        if finished is not None and finished.status == "running":
            _finish(db, finished, "completed", None)
    finally:
        db.close()


def _ensure_queries(
    db: Session, run: ResearchRun, product: str, industry: str | None
) -> list[ResearchQuery]:
    existing = db.scalars(
        select(ResearchQuery)
        .where(ResearchQuery.run_id == run.id)
        .order_by(ResearchQuery.position)
    ).all()
    if existing:
        return list(existing)
    drafted = plan_queries(product, run.geography, industry, run.max_queries)
    rows: list[ResearchQuery] = []
    for position, text in enumerate(drafted, start=1):
        row = ResearchQuery(
            organization_id=run.organization_id,
            run_id=run.id,
            position=position,
            query_text=text,
            status="pending",
        )
        db.add(row)
        rows.append(row)
    run.queries_total = len(rows)
    db.commit()
    return rows


def _store_hits(
    db: Session, run: ResearchRun, query: ResearchQuery, provider_name: str, hits: list[Hit]
) -> tuple[int, int, int]:
    stored = 0
    skipped = 0
    sellers = 0
    for hit in hits:
        if _candidate_count(db, run) >= run.limit_companies:
            return stored, skipped, sellers
        domain = public_domain(hit.url)
        if domain is None:
            continue
        if looks_like_packaging_seller(hit.title, hit.snippet, domain):
            sellers += 1
            continue
        title = " ".join(hit.title.split())[:200] or domain
        try:
            normalized = normalize_company_name(title)
        except ValueError:
            continue
        identity = f"demo:{normalized}" if provider_name == "demo" else domain
        if _known_lead(db, run, normalized, identity):
            skipped += 1
            continue
        candidate = db.scalar(
            select(ResearchCandidate).where(
                ResearchCandidate.run_id == run.id,
                ResearchCandidate.identity_key == identity,
            )
        )
        if candidate is None:
            candidate = ResearchCandidate(
                organization_id=run.organization_id,
                run_id=run.id,
                display_name=title,
                normalized_name=normalized,
                canonical_domain=None if provider_name == "demo" else domain,
                identity_key=identity,
                status="pending",
                duplicate_company_id=_duplicate_id(db, run, normalized, domain, provider_name),
            )
            db.add(candidate)
            db.flush()
            stored += 1
        already = db.scalar(
            select(Source).where(
                Source.candidate_id == candidate.id,
                Source.canonical_url == hit.url[:500],
            )
        )
        if already is None:
            db.add(
                Source(
                    organization_id=run.organization_id,
                    candidate_id=candidate.id,
                    query_id=query.id,
                    provider=provider_name,
                    canonical_url=hit.url[:500],
                    page_title=title[:300],
                    domain=domain,
                    snippet=hit.snippet[:2000],
                    content_hash=content_hash(hit.url, hit.snippet),
                )
            )
    return stored, skipped, sellers


def _known_lead(db: Session, run: ResearchRun, normalized: str, identity: str) -> bool:
    company = db.scalar(
        select(Company.id).where(
            Company.organization_id == run.organization_id,
            Company.normalized_name == normalized,
        )
    )
    if company is not None:
        return True
    prior = db.scalar(
        select(ResearchCandidate.id).where(
            ResearchCandidate.organization_id == run.organization_id,
            ResearchCandidate.run_id != run.id,
            or_(
                ResearchCandidate.identity_key == identity,
                ResearchCandidate.normalized_name == normalized,
            ),
        )
    )
    return prior is not None


def _refresh_assessments(db: Session, run: ResearchRun, product: str, industry: str | None) -> None:
    candidates = db.scalars(
        select(ResearchCandidate).where(ResearchCandidate.run_id == run.id)
    ).all()
    for candidate in candidates:
        sources = db.scalars(select(Source).where(Source.candidate_id == candidate.id)).all()
        snippets = [source.snippet for source in sources]
        score, accepted, dropped, contradiction, extracted = assess_sources(
            snippets,
            product=product,
            geography=run.geography,
            industry=industry,
        )
        db.execute(delete(EvidenceClaim).where(EvidenceClaim.candidate_id == candidate.id))
        db.execute(
            delete(ResearchAssessment).where(ResearchAssessment.candidate_id == candidate.id)
        )
        db.add(
            ResearchAssessment(
                organization_id=run.organization_id,
                candidate_id=candidate.id,
                provider=extracted.provider,
                model_name=extracted.model,
                prompt_version=extracted.prompt_version,
                fit_total=score.total,
                reasons_json=json_reasons(score.reasons),
                industry_alignment=score.breakdown.industry_alignment,
                product_fit=score.breakdown.product_fit,
                operational_scale=score.breakdown.operational_scale,
                geography_supply=score.breakdown.geography_supply,
                buyer_relevant_evidence=score.breakdown.buyer_relevant_evidence,
                source_freshness=score.breakdown.source_freshness,
                contradiction=contradiction,
                dropped_claims=dropped,
                input_tokens=extracted.input_tokens,
                output_tokens=extracted.output_tokens,
                error=extracted.error,
            )
        )
        for claim in accepted:
            source_id = next(
                (
                    source.id
                    for source in sources
                    if claim.quote.casefold() in " ".join(source.snippet.split()).casefold()
                ),
                None,
            )
            db.add(
                EvidenceClaim(
                    organization_id=run.organization_id,
                    candidate_id=candidate.id,
                    source_id=source_id,
                    quote=claim.quote[:2000],
                    kind=claim.kind,
                    supported=True,
                )
            )
        if extracted.input_tokens or extracted.output_tokens:
            db.add(
                UsageEvent(
                    organization_id=run.organization_id,
                    run_id=run.id,
                    kind="model",
                    units=extracted.input_tokens + extracted.output_tokens,
                    mode=extracted.provider,
                )
            )


def json_reasons(reasons: list[str]) -> str:
    return json.dumps(reasons)


def _duplicate_id(
    db: Session, run: ResearchRun, normalized: str, domain: str, provider_name: str
) -> uuid.UUID | None:
    by_name = db.scalar(
        select(Company).where(
            Company.organization_id == run.organization_id,
            Company.normalized_name == normalized,
        )
    )
    if by_name is not None:
        return by_name.id
    if provider_name == "demo":
        return None
    by_domain = db.scalar(
        select(Company).where(
            Company.organization_id == run.organization_id,
            Company.canonical_domain == domain,
        )
    )
    return by_domain.id if by_domain is not None else None


def _candidate_count(db: Session, run: ResearchRun) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ResearchCandidate)
            .where(ResearchCandidate.run_id == run.id)
        )
        or 0
    )


def _finish(db: Session, run: ResearchRun, status: str, error: str | None) -> None:
    run.status = status
    run.error_summary = error
    run.finished_at = datetime.now(UTC)
    leftover = db.scalars(
        select(ResearchQuery).where(
            ResearchQuery.run_id == run.id,
            ResearchQuery.status == "pending",
        )
    ).all()
    for query in leftover:
        query.status = "skipped"
    db.commit()


def promote_candidate(
    db: Session,
    candidate: ResearchCandidate,
    actor_user_id: uuid.UUID,
    *,
    merge_target: Company | None,
) -> Company:
    run = db.get(ResearchRun, candidate.run_id)
    if run is None:
        raise ValueError("missing run")
    if merge_target is not None:
        company = merge_target
        candidate.status = "merged"
    else:
        company = Company(
            organization_id=candidate.organization_id,
            display_name=candidate.display_name,
            normalized_name=candidate.normalized_name,
            canonical_domain=candidate.canonical_domain,
            country="India",
            business_unit="",
            source_origin="web_research",
            review_status="approved",
            review_label="Research candidate – not a verified buyer",
            industry_id=None,
            notes="Accepted from a research run. Not a verified buyer.",
        )
        db.add(company)
        db.flush()
        open_research_opportunity(db, company, actor_user_id, from_sheet=False)
        candidate.status = "approved"
    product_id = run.product_id
    exists = db.scalar(
        select(CompanyProductNeed).where(
            CompanyProductNeed.company_id == company.id,
            CompanyProductNeed.product_id == product_id,
        )
    )
    if exists is None:
        db.add(
            CompanyProductNeed(
                organization_id=company.organization_id,
                company_id=company.id,
                product_id=product_id,
                need_status="hypothesis",
                evidence_note=None,
                source_origin="web_research",
            )
        )
    candidate.company_id = company.id
    return company


def record_review_audit(db: Session, actor, candidate: ResearchCandidate, action: str) -> None:
    audit(
        db,
        actor,
        "research_candidate",
        str(candidate.id),
        action,
        f"Research candidate {action}",
    )
