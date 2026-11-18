"""CSV preview and commit. Preview does not write. Export neutralizes formulas."""

from __future__ import annotations

import csv
import io
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ngreen_api.catalog_seed import open_research_opportunity
from ngreen_api.deps import Actor, ApiError
from ngreen_api.models import (
    Company,
    CompanyProductNeed,
    CompanyTag,
    ImportBatch,
    ImportRow,
    Industry,
    IndustryAlias,
    Membership,
    Opportunity,
    Product,
    User,
)
from ngreen_contracts.taxonomy import (
    CANONICAL_INDUSTRIES,
    JSON_INDUSTRY_ALIASES,
    normalize_company_name,
)

MAX_CHARS = 500_000
MAX_ROWS = 500
_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")


@dataclass
class ParsedRow:
    row_number: int
    display_name: str
    city: str | None
    state: str | None
    country: str
    notes: str | None
    products: list[str]
    tags: list[str]
    owner_email: str | None
    industry_raw: str | None
    status: str
    message: str
    match_id: uuid.UUID | None = None


def csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(_DANGEROUS):
        return "'" + text
    return text


def render_csv(headers: list[str], rows: list[list[object]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([csv_cell(cell) for cell in row])
    return buffer.getvalue()


def preview_csv(db: Session, actor: Actor, csv_text: str) -> list[ParsedRow]:
    raw_rows = _read(csv_text)
    seen: dict[str, int] = {}
    parsed: list[ParsedRow] = []
    for row_number, raw in raw_rows:
        item = _interpret(db, actor, row_number, raw, seen)
        parsed.append(item)
    return parsed


def commit_csv(
    db: Session, actor: Actor, csv_text: str, update_rows: set[int]
) -> tuple[ImportBatch, list[ParsedRow]]:
    planned = preview_csv(db, actor, csv_text)
    batch = ImportBatch(
        organization_id=actor.organization_id,
        actor_user_id=actor.user.id,
        created_count=0,
        updated_count=0,
        skipped_count=0,
        failed_count=0,
    )
    db.add(batch)
    db.flush()
    results: list[ParsedRow] = []
    for item in planned:
        outcome = _apply(db, actor, item, update_rows)
        results.append(outcome)
        db.add(
            ImportRow(
                import_id=batch.id,
                row_number=outcome.row_number,
                status=outcome.status,
                message=outcome.message[:500],
                company_id=outcome.match_id,
            )
        )
        if outcome.status == "created":
            batch.created_count += 1
        elif outcome.status == "updated":
            batch.updated_count += 1
        elif outcome.status == "skipped":
            batch.skipped_count += 1
        else:
            batch.failed_count += 1
    return batch, results


def _read(csv_text: str) -> list[tuple[int, dict[str, str]]]:
    if len(csv_text) > MAX_CHARS:
        raise ApiError(422, "validation_error", "CSV is too large.")
    sample = csv_text.lstrip("\ufeff").strip()
    if not sample:
        raise ApiError(422, "validation_error", "CSV is empty.")
    reader = csv.DictReader(io.StringIO(sample))
    if reader.fieldnames is None:
        raise ApiError(422, "validation_error", "CSV must include a display_name column.")
    fields = {(name or "").strip().casefold() for name in reader.fieldnames}
    if "display_name" not in fields:
        raise ApiError(422, "validation_error", "CSV must include a display_name column.")
    rows: list[tuple[int, dict[str, str]]] = []
    for offset, raw in enumerate(reader, start=2):
        if len(rows) >= MAX_ROWS:
            raise ApiError(422, "validation_error", "CSV is limited to 500 data rows.")
        cleaned = {
            (key or "").strip().casefold(): (value or "").strip() for key, value in raw.items()
        }
        if not any(cleaned.values()):
            continue
        rows.append((offset, cleaned))
    return rows


def _interpret(
    db: Session,
    actor: Actor,
    row_number: int,
    raw: dict[str, str],
    seen: dict[str, int],
) -> ParsedRow:
    name = raw.get("display_name", "")
    products = _split(raw.get("products", ""))
    tags = _split(raw.get("tags", ""))
    item = ParsedRow(
        row_number=row_number,
        display_name=name,
        city=_blank(raw.get("city")),
        state=_blank(raw.get("state")),
        country=_blank(raw.get("country")) or "India",
        notes=_blank(raw.get("notes")),
        products=products,
        tags=tags,
        owner_email=_blank(raw.get("owner_email")),
        industry_raw=_blank(raw.get("industry")),
        status="ready",
        message="Ready to create.",
    )
    if not name:
        return _fail(item, "Company name is empty.")
    if len(name) > 200:
        return _fail(item, "Company name is longer than 200 characters.")
    if item.notes and len(item.notes) > 2000:
        return _fail(item, "Notes are longer than 2000 characters.")
    try:
        normalized = normalize_company_name(name)
    except ValueError:
        return _fail(item, "Company name is empty.")
    for product_name in products:
        if _product(db, actor.organization_id, product_name) is None:
            return _fail(item, f"Unknown product: {product_name}")
    for tag in tags:
        if _tag(tag) is None:
            return _fail(item, f"Tag is not valid: {tag}")
    if item.industry_raw and _industry(db, actor.organization_id, item.industry_raw) is None:
        return _fail(item, f"Unknown industry: {item.industry_raw}")
    if item.owner_email and _owner(db, actor.organization_id, item.owner_email) is None:
        return _fail(item, "Owner email is not a member of this organization.")
    earlier = seen.get(normalized)
    if earlier is not None:
        item.status = "duplicate"
        item.message = f"Duplicate of row {earlier} in this file."
        return item
    seen[normalized] = row_number
    existing = db.scalar(
        select(Company).where(
            Company.organization_id == actor.organization_id,
            Company.normalized_name == normalized,
        )
    )
    if existing is not None:
        item.status = "duplicate"
        item.match_id = existing.id
        item.message = f"Matches existing account {existing.display_name}."
    return item


def _apply(db: Session, actor: Actor, item: ParsedRow, update_rows: set[int]) -> ParsedRow:
    if item.status == "error":
        return item
    if item.status == "duplicate" and item.row_number not in update_rows:
        item.status = "skipped"
        item.message = "Skipped duplicate."
        return item
    if item.status == "duplicate" and item.match_id is None:
        item.status = "skipped"
        item.message = "Skipped duplicate inside the file."
        return item
    try:
        with db.begin_nested():
            if item.status == "duplicate" and item.match_id is not None:
                company = db.get(Company, item.match_id)
                if company is None or company.organization_id != actor.organization_id:
                    raise ApiError(404, "not_found", "Matched account is no longer available.")
                _fill(db, actor, company, item)
                item.status = "updated"
                item.message = "Updated the existing account."
            else:
                company = _insert(db, actor, item)
                item.status = "created"
                item.match_id = company.id
                item.message = "Created."
    except (ApiError, IntegrityError) as exc:
        item.status = "failed"
        item.message = exc.message if isinstance(exc, ApiError) else "Could not save this row."
    return item


def _insert(db: Session, actor: Actor, item: ParsedRow) -> Company:
    company = Company(
        organization_id=actor.organization_id,
        display_name=item.display_name.strip(),
        normalized_name=normalize_company_name(item.display_name),
        city=item.city,
        state=item.state,
        country=item.country[:80],
        notes=item.notes,
        source_origin="csv_import",
        review_status="pending",
        business_unit="",
    )
    _assign(db, actor, company, item)
    db.add(company)
    db.flush()
    _attach(db, actor, company, item)
    return company


def _fill(db: Session, actor: Actor, company: Company, item: ParsedRow) -> None:
    if item.city:
        company.city = item.city
    if item.state:
        company.state = item.state
    if item.notes:
        company.notes = item.notes
    _assign(db, actor, company, item)
    _attach(db, actor, company, item)


def _assign(db: Session, actor: Actor, company: Company, item: ParsedRow) -> None:
    if item.owner_email:
        owner = _owner(db, actor.organization_id, item.owner_email)
        if owner is None:
            raise ApiError(
                422, "validation_error", "Owner email is not a member of this organization."
            )
        company.owner_user_id = owner.id
    if item.industry_raw:
        industry = _industry(db, actor.organization_id, item.industry_raw)
        if industry is None:
            raise ApiError(422, "validation_error", f"Unknown industry: {item.industry_raw}")
        company.industry_id = industry.id
        company.industry_assignment = "manual"


def _attach(db: Session, actor: Actor, company: Company, item: ParsedRow) -> None:
    for product_name in item.products:
        product = _product(db, actor.organization_id, product_name)
        if product is None:
            raise ApiError(422, "validation_error", f"Unknown product: {product_name}")
        exists = db.scalar(
            select(CompanyProductNeed).where(
                CompanyProductNeed.company_id == company.id,
                CompanyProductNeed.product_id == product.id,
            )
        )
        if exists is None:
            db.add(
                CompanyProductNeed(
                    organization_id=actor.organization_id,
                    company_id=company.id,
                    product_id=product.id,
                    need_status="hypothesis",
                    source_origin="csv_import",
                )
            )
    for tag in item.tags:
        label = _tag(tag)
        if label is None:
            raise ApiError(422, "validation_error", f"Tag is not valid: {tag}")
        exists = db.scalar(
            select(CompanyTag).where(CompanyTag.company_id == company.id, CompanyTag.label == label)
        )
        if exists is None:
            db.add(
                CompanyTag(
                    organization_id=actor.organization_id, company_id=company.id, label=label
                )
            )
    if db.scalar(select(Opportunity).where(Opportunity.company_id == company.id)) is None:
        open_research_opportunity(db, company, actor.user.id, from_sheet=False)


def _product(db: Session, organization_id: uuid.UUID, name: str) -> Product | None:
    return db.scalar(
        select(Product).where(Product.organization_id == organization_id, Product.name == name)
    )


def _industry(db: Session, organization_id: uuid.UUID, raw: str) -> Industry | None:
    canonical = JSON_INDUSTRY_ALIASES.get(raw)
    if canonical is None and raw in CANONICAL_INDUSTRIES:
        canonical = raw
    if canonical is None:
        alias = db.scalar(
            select(IndustryAlias).where(
                IndustryAlias.organization_id == organization_id,
                IndustryAlias.alias == raw,
            )
        )
        if alias is None:
            return None
        return db.get(Industry, alias.industry_id)
    return db.scalar(
        select(Industry).where(
            Industry.organization_id == organization_id, Industry.name == canonical
        )
    )


def _owner(db: Session, organization_id: uuid.UUID, email: str) -> User | None:
    user = db.scalar(select(User).where(func.lower(User.email) == email.casefold()))
    if user is None:
        return None
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.organization_id == organization_id,
        )
    )
    if membership is None:
        return None
    return user


def _tag(raw: str) -> str | None:
    label = " ".join(raw.strip().split()).casefold()
    if not label or len(label) > 40:
        return None
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789 -")
    if any(character not in allowed for character in label):
        return None
    return label


def _split(raw: str) -> list[str]:
    if not raw:
        return []
    parts = raw.replace("|", ";").split(";")
    return [part.strip() for part in parts if part.strip()]


def _blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _fail(item: ParsedRow, message: str) -> ParsedRow:
    item.status = "error"
    item.message = message
    return item
