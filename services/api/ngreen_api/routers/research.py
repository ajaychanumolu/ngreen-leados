import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ngreen_api.contact_research import business_emails, business_phones, discover_public_contacts
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_importer
from ngreen_api.models import (
    Company,
    EvidenceClaim,
    Industry,
    Product,
    ResearchAssessment,
    ResearchCandidate,
    ResearchQuery,
    ResearchRun,
    Source,
)
from ngreen_api.research_jobs import (
    dispatch,
    promote_candidate,
    record_review_audit,
    research_is_limited,
)
from ngreen_api.research_search import CANDIDATE_LABEL, ProviderOutage, mentioned_plastic
from ngreen_api.settings import get_settings

router = APIRouter(prefix="/api/v1/research", tags=["research"])


class RunBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    industry_id: uuid.UUID | None = None
    geography: str = Field(default="", max_length=120)
    limit_companies: int = Field(default=5, ge=1, le=25)
    max_queries: int = Field(default=3, ge=1, le=10)


class ReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str = Field(pattern="^(approve|reject|merge)$")
    target_company_id: uuid.UUID | None = None


class SourceOut(BaseModel):
    id: uuid.UUID
    provider: str
    canonical_url: str
    page_title: str
    domain: str
    snippet: str
    retrieved_at: datetime


class ClaimOut(BaseModel):
    quote: str
    kind: str


class AssessmentOut(BaseModel):
    fit_total: int
    reasons: list[str]
    industry_alignment: int
    product_fit: int
    operational_scale: int
    geography_supply: int
    buyer_relevant_evidence: int
    source_freshness: int
    contradiction: bool
    dropped_claims: int
    provider: str
    model_name: str
    prompt_version: str
    claims: list[ClaimOut]


class CandidateOut(BaseModel):
    id: uuid.UUID
    display_name: str
    canonical_domain: str | None
    status: str
    review_label: str
    duplicate_company_id: uuid.UUID | None
    company_id: uuid.UUID | None
    plastic_items: list[str] = Field(default_factory=list)
    snippet_emails: list[str] = Field(default_factory=list)
    snippet_phones: list[str] = Field(default_factory=list)
    sources: list[SourceOut]
    assessment: AssessmentOut | None = None


class QueryOut(BaseModel):
    id: uuid.UUID
    position: int
    query_text: str
    status: str
    result_count: int
    known_skipped: int
    seller_skipped: int = 0
    error: str | None


class RunOut(BaseModel):
    id: uuid.UUID
    status: str
    mode: str
    worker: str
    geography: str
    product_name: str
    industry_filter: str | None
    limit_companies: int
    max_queries: int
    budget_credits: int
    spent_credits: int
    queries_total: int
    queries_done: int
    error_summary: str | None
    created_at: datetime
    queries: list[QueryOut] = Field(default_factory=list)
    candidates: list[CandidateOut] = Field(default_factory=list)


class RunPage(BaseModel):
    items: list[RunOut]
    page: int
    page_size: int
    total: int


class CandidatePage(BaseModel):
    items: list[CandidateOut]
    page: int
    page_size: int
    total: int


@router.get("/runs", response_model=RunPage)
def list_runs(
    page: int = 1,
    page_size: int = 25,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> RunPage:
    _page(page, page_size)
    base = select(ResearchRun).where(ResearchRun.organization_id == actor.organization_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(ResearchRun.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return RunPage(
        items=[_run_out(db, row, nested=False) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.post("/runs", response_model=RunOut, status_code=201)
def create_run(
    body: RunBody,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> RunOut:
    settings = get_settings()
    if body.max_queries > settings.research_budget_credits:
        raise ApiError(
            422,
            "budget_exceeded",
            "That search asks for more queries than the spend cap allows.",
        )
    if research_is_limited(str(actor.organization_id)):
        raise ApiError(429, "rate_limited", "Too many research runs. Wait a minute and retry.")
    product = _product(db, actor, body.product_id)
    industry = _industry(db, actor, body.industry_id)
    mode = "live" if settings.serper_api_key else "demo"
    run = ResearchRun(
        organization_id=actor.organization_id,
        actor_user_id=actor.user.id,
        product_id=product.id,
        industry_id=industry.id if industry else None,
        geography=body.geography.strip() or "India",
        limit_companies=body.limit_companies,
        max_queries=body.max_queries,
        max_results_per_query=5,
        budget_credits=settings.research_budget_credits,
        spent_credits=0,
        status="queued",
        mode=mode,
        worker=settings.research_worker,
        queries_total=0,
        queries_done=0,
    )
    db.add(run)
    db.commit()
    dispatch(str(run.id))
    db.expire_all()
    stored = db.get(ResearchRun, run.id)
    if stored is None:
        raise ApiError(404, "not_found", "Research run not found.")
    return _run_out(db, stored, nested=True)


@router.get("/runs/{run_id}", response_model=RunOut)
def get_run(
    run_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> RunOut:
    return _run_out(db, _owned_run(db, actor, run_id), nested=True)


@router.post("/runs/{run_id}/cancel", response_model=RunOut)
def cancel_run(
    run_id: uuid.UUID,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> RunOut:
    run = _owned_run(db, actor, run_id)
    if run.status == "cancelled":
        return _run_out(db, run, nested=True)
    if run.status not in {"queued", "running"}:
        raise ApiError(409, "not_cancellable", "This run is already finished.")
    run.status = "cancelled"
    run.error_summary = "Cancelled by staff."
    run.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(run)
    return _run_out(db, run, nested=True)


@router.post("/runs/{run_id}/retry", response_model=RunOut)
def retry_run(
    run_id: uuid.UUID,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> RunOut:
    run = _owned_run(db, actor, run_id)
    if run.status not in {"failed", "cancelled", "capped"}:
        raise ApiError(
            409,
            "not_retryable",
            "Only a failed, cancelled, or capped run can be retried.",
        )
    if research_is_limited(str(actor.organization_id)):
        raise ApiError(429, "rate_limited", "Too many research runs. Wait a minute and retry.")
    run.status = "queued"
    run.error_summary = None
    run.finished_at = None
    for query in db.scalars(select(ResearchQuery).where(ResearchQuery.run_id == run.id)).all():
        if query.status != "ok":
            query.status = "pending"
            query.error = None
    db.commit()
    dispatch(str(run.id))
    db.expire_all()
    stored = db.get(ResearchRun, run.id)
    if stored is None:
        raise ApiError(404, "not_found", "Research run not found.")
    return _run_out(db, stored, nested=True)


@router.get("/candidates", response_model=CandidatePage)
def list_candidates(
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> CandidatePage:
    _page(page, page_size)
    base = select(ResearchCandidate).where(
        ResearchCandidate.organization_id == actor.organization_id
    )
    if status:
        if status not in {"pending", "approved", "rejected", "merged"}:
            raise ApiError(422, "validation_error", "Unknown candidate status.")
        base = base.where(ResearchCandidate.status == status)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(ResearchCandidate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return CandidatePage(
        items=[_candidate_out(db, row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.post("/candidates/{candidate_id}/review", response_model=CandidateOut)
def review_candidate(
    candidate_id: uuid.UUID,
    body: ReviewBody,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> CandidateOut:
    candidate = _owned_candidate(db, actor, candidate_id)
    if candidate.status != "pending":
        raise ApiError(409, "already_reviewed", "This candidate was already reviewed.")
    if body.action == "reject":
        candidate.status = "rejected"
        record_review_audit(db, actor, candidate, "reject")
        db.commit()
        db.refresh(candidate)
        return _candidate_out(db, candidate)
    target: Company | None = None
    if body.action == "merge":
        if body.target_company_id is None:
            raise ApiError(422, "validation_error", "Merge needs a target account.")
        target = db.get(Company, body.target_company_id)
        if target is None or target.organization_id != actor.organization_id:
            raise ApiError(404, "not_found", "Account not found.")
    elif candidate.duplicate_company_id is not None:
        raise ApiError(
            409,
            "duplicate_account",
            "This candidate matches an account. Merge it instead of creating another.",
        )
    try:
        company = promote_candidate(db, candidate, actor.user.id, merge_target=target)
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409, "duplicate_account", "An account with this name already exists."
        ) from exc
    try:
        discover_public_contacts(db, company, actor.user.id)
    except ProviderOutage:
        pass
    record_review_audit(db, actor, candidate, body.action)
    db.commit()
    db.refresh(candidate)
    return _candidate_out(db, candidate)


def _page(page: int, page_size: int) -> None:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")


def _product(db: Session, actor: Actor, product_id: uuid.UUID) -> Product:
    product = db.get(Product, product_id)
    if product is None or product.organization_id != actor.organization_id:
        raise ApiError(422, "validation_error", "Unknown product.")
    return product


def _industry(db: Session, actor: Actor, industry_id: uuid.UUID | None) -> Industry | None:
    if industry_id is None:
        return None
    industry = db.get(Industry, industry_id)
    if industry is None or industry.organization_id != actor.organization_id:
        raise ApiError(422, "validation_error", "Unknown industry.")
    return industry


def _owned_run(db: Session, actor: Actor, run_id: uuid.UUID) -> ResearchRun:
    run = db.get(ResearchRun, run_id)
    if run is None or run.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Research run not found.")
    return run


def _owned_candidate(db: Session, actor: Actor, candidate_id: uuid.UUID) -> ResearchCandidate:
    candidate = db.get(ResearchCandidate, candidate_id)
    if candidate is None or candidate.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Research candidate not found.")
    return candidate


def _run_out(db: Session, run: ResearchRun, *, nested: bool) -> RunOut:
    product = db.get(Product, run.product_id)
    industry = db.get(Industry, run.industry_id) if run.industry_id else None
    queries: list[QueryOut] = []
    candidates: list[CandidateOut] = []
    if nested:
        for query in db.scalars(
            select(ResearchQuery)
            .where(ResearchQuery.run_id == run.id)
            .order_by(ResearchQuery.position)
        ).all():
            queries.append(
                QueryOut(
                    id=query.id,
                    position=query.position,
                    query_text=query.query_text,
                    status=query.status,
                    result_count=query.result_count,
                    known_skipped=query.known_skipped,
                    seller_skipped=query.seller_skipped,
                    error=query.error,
                )
            )
        for candidate in db.scalars(
            select(ResearchCandidate)
            .where(ResearchCandidate.run_id == run.id)
            .order_by(ResearchCandidate.display_name)
        ).all():
            candidates.append(_candidate_out(db, candidate))
    return RunOut(
        id=run.id,
        status=run.status,
        mode=run.mode,
        worker=run.worker,
        geography=run.geography,
        product_name=product.name if product else "",
        industry_filter=industry.name if industry else None,
        limit_companies=run.limit_companies,
        max_queries=run.max_queries,
        budget_credits=run.budget_credits,
        spent_credits=run.spent_credits,
        queries_total=run.queries_total,
        queries_done=run.queries_done,
        error_summary=run.error_summary,
        created_at=run.created_at,
        queries=queries,
        candidates=candidates,
    )


def _candidate_out(db: Session, candidate: ResearchCandidate) -> CandidateOut:
    sources = [
        SourceOut(
            id=source.id,
            provider=source.provider,
            canonical_url=source.canonical_url,
            page_title=source.page_title,
            domain=source.domain,
            snippet=source.snippet,
            retrieved_at=source.retrieved_at,
        )
        for source in db.scalars(
            select(Source)
            .where(Source.candidate_id == candidate.id)
            .order_by(Source.retrieved_at)
        ).all()
    ]
    plastic: list[str] = []
    emails: list[str] = []
    phones: list[str] = []
    for source in sources:
        for item in mentioned_plastic(f"{source.page_title} {source.snippet}"):
            if item not in plastic:
                plastic.append(item)
        for email in business_emails(
            source.page_title,
            source.snippet,
            source.canonical_url,
            candidate.display_name,
            candidate.canonical_domain,
        ):
            if email not in emails:
                emails.append(email)
        for phone in business_phones(
            source.page_title,
            source.snippet,
            source.canonical_url,
            candidate.display_name,
            candidate.canonical_domain,
        ):
            if phone not in phones:
                phones.append(phone)
    return CandidateOut(
        id=candidate.id,
        display_name=candidate.display_name,
        canonical_domain=candidate.canonical_domain,
        status=candidate.status,
        review_label=CANDIDATE_LABEL,
        duplicate_company_id=candidate.duplicate_company_id,
        company_id=candidate.company_id,
        plastic_items=plastic,
        snippet_emails=emails,
        snippet_phones=phones,
        sources=sources,
        assessment=_assessment_out(db, candidate.id),
    )


def _assessment_out(db: Session, candidate_id: uuid.UUID) -> AssessmentOut | None:
    row = db.scalar(
        select(ResearchAssessment).where(ResearchAssessment.candidate_id == candidate_id)
    )
    if row is None:
        return None
    try:
        reasons = json.loads(row.reasons_json)
    except json.JSONDecodeError:
        reasons = []
    if not isinstance(reasons, list):
        reasons = []
    claims = [
        ClaimOut(quote=claim.quote, kind=claim.kind)
        for claim in db.scalars(
            select(EvidenceClaim).where(EvidenceClaim.candidate_id == candidate_id)
        ).all()
    ]
    return AssessmentOut(
        fit_total=row.fit_total,
        reasons=[str(item) for item in reasons],
        industry_alignment=row.industry_alignment,
        product_fit=row.product_fit,
        operational_scale=row.operational_scale,
        geography_supply=row.geography_supply,
        buyer_relevant_evidence=row.buyer_relevant_evidence,
        source_freshness=row.source_freshness,
        contradiction=row.contradiction,
        dropped_claims=row.dropped_claims,
        provider=row.provider,
        model_name=row.model_name,
        prompt_version=row.prompt_version,
        claims=claims,
    )
