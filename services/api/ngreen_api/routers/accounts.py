import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.catalog_seed import open_research_opportunity
from ngreen_api.csvio import render_csv
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_writer
from ngreen_api.models import (
    Company,
    CompanyNote,
    CompanyProductNeed,
    CompanyTag,
    Contact,
    Industry,
    Opportunity,
    Product,
    User,
)
from ngreen_api.records import audit, blank, clean_tag, owned_company, product_named, require_member
from ngreen_contracts.enums import NeedStatus, SourceOrigin
from ngreen_contracts.taxonomy import normalize_company_name

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


class AccountBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=200)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)
    owner_user_id: uuid.UUID | None = None
    industry_id: uuid.UUID | None = None
    product_names: list[str] = Field(default_factory=list, max_length=11)
    tags: list[str] = Field(default_factory=list, max_length=20)


class AccountOut(BaseModel):
    id: uuid.UUID
    display_name: str
    normalized_name: str
    city: str | None
    state: str | None
    country: str
    notes: str | None
    source_origin: str
    review_status: str
    review_label: str | None = None
    owner_user_id: uuid.UUID | None = None
    owner_name: str | None = None
    industry_id: uuid.UUID | None = None
    industry_name: str | None = None
    tags: list[str] = Field(default_factory=list)
    products: list[str] = Field(default_factory=list)
    stage: str | None = None
    contact_count: int = 0
    created_at: datetime


class NeedOut(BaseModel):
    id: uuid.UUID
    product_name: str
    need_status: str
    evidence_note: str | None


class ContactOut(BaseModel):
    id: uuid.UUID
    display_name: str | None
    role_title: str | None
    email: str | None
    phone: str | None
    source_note: str
    source_url: str | None = None
    permission_basis: str
    do_not_call: bool = False


class NoteOut(BaseModel):
    id: uuid.UUID
    body: str
    author_name: str
    created_at: datetime


class AccountDetail(AccountOut):
    needs: list[NeedOut] = Field(default_factory=list)
    contacts: list[ContactOut] = Field(default_factory=list)
    notes_log: list[NoteOut] = Field(default_factory=list)
    opportunity_id: uuid.UUID | None = None


class AccountPage(BaseModel):
    items: list[AccountOut]
    page: int
    page_size: int
    total: int


class TagBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tag: str = Field(min_length=1, max_length=40)


class NeedBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str = Field(min_length=1, max_length=80)
    evidence_note: str | None = Field(default=None, max_length=2000)


class NeedPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    need_status: NeedStatus
    evidence_note: str | None = Field(default=None, max_length=2000)


class NoteBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1, max_length=2000)


@router.get("", response_model=AccountPage)
def list_accounts(
    page: int = 1,
    page_size: int = 25,
    q: str | None = None,
    city: str | None = None,
    source_origin: str | None = None,
    review_status: str | None = None,
    product: str | None = None,
    tag: str | None = None,
    stage: str | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> AccountPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    base = _filtered(db, actor, q, city, source_origin, review_status, product, tag, stage)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(Company.display_name.asc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return AccountPage(
        items=_cards(db, rows),
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.get("/export")
def export_accounts(
    q: str | None = None,
    city: str | None = None,
    source_origin: str | None = None,
    review_status: str | None = None,
    product: str | None = None,
    tag: str | None = None,
    stage: str | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> Response:
    base = _filtered(db, actor, q, city, source_origin, review_status, product, tag, stage)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    if int(total or 0) > 5000:
        raise ApiError(422, "validation_error", "Narrow the filters before exporting.")
    rows = db.scalars(base.order_by(Company.display_name.asc())).all()
    cards = _cards(db, rows)
    owners = _owner_emails(db, [card.owner_user_id for card in cards if card.owner_user_id])
    payload = render_csv(
        [
            "display_name",
            "city",
            "state",
            "country",
            "notes",
            "products",
            "tags",
            "owner_email",
            "industry",
            "source_origin",
            "review_status",
            "review_label",
            "stage",
        ],
        [
            [
                card.display_name,
                card.city or "",
                card.state or "",
                card.country,
                card.notes or "",
                "; ".join(card.products),
                "; ".join(card.tags),
                owners.get(card.owner_user_id, "") if card.owner_user_id else "",
                card.industry_name or "",
                card.source_origin,
                card.review_status,
                card.review_label or "",
                card.stage or "",
            ]
            for card in cards
        ],
    )
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="accounts.csv"'},
    )


@router.post("", response_model=AccountDetail, status_code=201)
def create_account(
    body: AccountBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> AccountDetail:
    normalized = normalize_company_name(body.display_name)
    if _by_name(db, actor, normalized) is not None:
        raise ApiError(409, "duplicate_account", "An account with this name already exists.")
    company = Company(
        organization_id=actor.organization_id,
        display_name=body.display_name.strip(),
        normalized_name=normalized,
        city=blank(body.city),
        state=blank(body.state),
        notes=blank(body.notes),
        source_origin="manual",
        review_status="pending",
        country="India",
        business_unit="",
    )
    _apply_optional(db, actor, company, body, body.model_fields_set)
    db.add(company)
    db.flush()
    _add_products(db, actor, company, body.product_names, "manual")
    _add_tags(db, actor, company, body.tags)
    open_research_opportunity(db, company, actor.user.id, from_sheet=False)
    audit(
        db, actor, "company", str(company.id), "create", f"Created account {company.display_name}"
    )
    db.commit()
    db.refresh(company)
    return _detail(db, company)


@router.get("/{account_id}", response_model=AccountDetail)
def get_account(
    account_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> AccountDetail:
    return _detail(db, owned_company(db, actor, account_id))


@router.patch("/{account_id}", response_model=AccountDetail)
def patch_account(
    account_id: uuid.UUID,
    body: AccountBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> AccountDetail:
    company = owned_company(db, actor, account_id)
    normalized = normalize_company_name(body.display_name)
    clash = _by_name(db, actor, normalized)
    if clash is not None and clash.id != company.id:
        raise ApiError(409, "duplicate_account", "An account with this name already exists.")
    company.display_name = body.display_name.strip()
    company.normalized_name = normalized
    company.city = blank(body.city)
    company.state = blank(body.state)
    company.notes = blank(body.notes)
    _apply_optional(db, actor, company, body, body.model_fields_set)
    if "product_names" in body.model_fields_set:
        _add_products(db, actor, company, body.product_names, "manual")
    if "tags" in body.model_fields_set:
        _add_tags(db, actor, company, body.tags)
    audit(
        db, actor, "company", str(company.id), "update", f"Updated account {company.display_name}"
    )
    db.commit()
    db.refresh(company)
    return _detail(db, company)


@router.post("/{account_id}/tags", response_model=AccountDetail)
def add_tag(
    account_id: uuid.UUID,
    body: TagBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> AccountDetail:
    company = owned_company(db, actor, account_id)
    _add_tags(db, actor, company, [body.tag])
    audit(db, actor, "company", str(company.id), "tag", "Added a tag")
    db.commit()
    return _detail(db, company)


@router.delete("/{account_id}/tags", response_model=AccountDetail)
def remove_tag(
    account_id: uuid.UUID,
    tag: str,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> AccountDetail:
    company = owned_company(db, actor, account_id)
    label = clean_tag(tag)
    row = db.scalar(
        select(CompanyTag).where(CompanyTag.company_id == company.id, CompanyTag.label == label)
    )
    if row is not None:
        db.delete(row)
        audit(db, actor, "company", str(company.id), "tag", "Removed a tag")
        db.commit()
    return _detail(db, company)


@router.post("/{account_id}/product-needs", response_model=NeedOut, status_code=201)
def add_need(
    account_id: uuid.UUID,
    body: NeedBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> NeedOut:
    company = owned_company(db, actor, account_id)
    product = product_named(db, actor, body.product_name)
    existing = db.scalar(
        select(CompanyProductNeed).where(
            CompanyProductNeed.company_id == company.id,
            CompanyProductNeed.product_id == product.id,
        )
    )
    if existing is not None:
        raise ApiError(409, "duplicate_need", "That product is already on this account.")
    note = blank(body.evidence_note)
    status = "hypothesis" if note is None else "publicly_evidenced"
    if status != "hypothesis" and note is None:
        raise ApiError(
            422, "validation_error", "A source note is required to move past hypothesis."
        )
    need = CompanyProductNeed(
        organization_id=actor.organization_id,
        company_id=company.id,
        product_id=product.id,
        need_status=status,
        evidence_note=note,
        source_origin="manual",
    )
    db.add(need)
    audit(db, actor, "company", str(company.id), "need", f"Added product need {product.name}")
    db.commit()
    db.refresh(need)
    return NeedOut(
        id=need.id,
        product_name=product.name,
        need_status=need.need_status,
        evidence_note=need.evidence_note,
    )


@router.patch("/{account_id}/product-needs/{need_id}", response_model=NeedOut)
def patch_need(
    account_id: uuid.UUID,
    need_id: uuid.UUID,
    body: NeedPatch,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> NeedOut:
    company = owned_company(db, actor, account_id)
    need = db.get(CompanyProductNeed, need_id)
    if (
        need is None
        or need.company_id != company.id
        or need.organization_id != actor.organization_id
    ):
        raise ApiError(404, "not_found", "Product need not found.")
    note = body.evidence_note if "evidence_note" in body.model_fields_set else need.evidence_note
    note = blank(note)
    if body.need_status != NeedStatus.HYPOTHESIS and not note:
        raise ApiError(
            422,
            "validation_error",
            "A source note is required to move past hypothesis.",
        )
    need.need_status = body.need_status.value
    need.evidence_note = note
    product = db.get(Product, need.product_id)
    audit(db, actor, "company", str(company.id), "need", "Updated a product need")
    db.commit()
    return NeedOut(
        id=need.id,
        product_name=product.name if product else "",
        need_status=need.need_status,
        evidence_note=need.evidence_note,
    )


@router.post("/{account_id}/notes", response_model=NoteOut, status_code=201)
def add_note(
    account_id: uuid.UUID,
    body: NoteBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> NoteOut:
    company = owned_company(db, actor, account_id)
    note = CompanyNote(
        organization_id=actor.organization_id,
        company_id=company.id,
        author_user_id=actor.user.id,
        body=body.body.strip(),
    )
    db.add(note)
    audit(db, actor, "company", str(company.id), "note", "Added a note")
    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id, body=note.body, author_name=actor.user.display_name, created_at=note.created_at
    )


def _by_name(db: Session, actor: Actor, normalized: str) -> Company | None:
    return db.scalar(
        select(Company).where(
            Company.organization_id == actor.organization_id,
            Company.normalized_name == normalized,
        )
    )


def _apply_optional(
    db: Session, actor: Actor, company: Company, body: AccountBody, fields: set[str]
) -> None:
    if "owner_user_id" in fields:
        if body.owner_user_id is not None:
            require_member(db, actor, body.owner_user_id)
        company.owner_user_id = body.owner_user_id
    if "industry_id" in fields:
        if body.industry_id is None:
            company.industry_id = None
            company.industry_assignment = None
        else:
            industry = db.get(Industry, body.industry_id)
            if industry is None or industry.organization_id != actor.organization_id:
                raise ApiError(422, "validation_error", "Unknown industry.")
            company.industry_id = industry.id
            company.industry_assignment = "manual"


def _add_products(
    db: Session, actor: Actor, company: Company, names: list[str], origin: str
) -> None:
    for name in names:
        product = product_named(db, actor, name)
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
                    source_origin=origin,
                )
            )


def _add_tags(db: Session, actor: Actor, company: Company, tags: list[str]) -> None:
    for raw in tags:
        label = clean_tag(raw)
        exists = db.scalar(
            select(CompanyTag).where(CompanyTag.company_id == company.id, CompanyTag.label == label)
        )
        if exists is None:
            db.add(
                CompanyTag(
                    organization_id=actor.organization_id, company_id=company.id, label=label
                )
            )


def _filtered(
    db: Session,
    actor: Actor,
    q: str | None,
    city: str | None,
    source_origin: str | None,
    review_status: str | None,
    product: str | None,
    tag: str | None,
    stage: str | None,
):
    stmt = select(Company).where(Company.organization_id == actor.organization_id)
    if q and q.strip():
        term = _like(normalize_company_name(q))
        stmt = stmt.where(Company.normalized_name.like(term, escape="\\"))
    if city and city.strip():
        stmt = stmt.where(func.lower(Company.city) == city.strip().casefold())
    if source_origin:
        _enum(source_origin, {item.value for item in SourceOrigin}, "source")
        stmt = stmt.where(Company.source_origin == source_origin)
    if review_status:
        stmt = stmt.where(Company.review_status == review_status)
    if product:
        stmt = stmt.where(
            Company.id.in_(
                select(CompanyProductNeed.company_id)
                .join(Product, Product.id == CompanyProductNeed.product_id)
                .where(
                    Product.organization_id == actor.organization_id,
                    Product.name == product,
                )
            )
        )
    if tag:
        stmt = stmt.where(
            Company.id.in_(
                select(CompanyTag.company_id).where(
                    CompanyTag.organization_id == actor.organization_id,
                    CompanyTag.label == clean_tag(tag),
                )
            )
        )
    if stage:
        stmt = stmt.where(
            Company.id.in_(
                select(Opportunity.company_id).where(
                    Opportunity.organization_id == actor.organization_id,
                    Opportunity.stage == stage,
                )
            )
        )
    return stmt


def _like(normalized: str) -> str:
    escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _enum(value: str, allowed: set[str], label: str) -> None:
    if value not in allowed:
        raise ApiError(422, "validation_error", f"Unknown {label}.")


def _cards(db: Session, rows: list[Company]) -> list[AccountOut]:
    ids = [row.id for row in rows]
    if not ids:
        return []
    tags: dict[uuid.UUID, list[str]] = {row_id: [] for row_id in ids}
    for tag in db.scalars(select(CompanyTag).where(CompanyTag.company_id.in_(ids))).all():
        tags[tag.company_id].append(tag.label)
    products: dict[uuid.UUID, list[str]] = {row_id: [] for row_id in ids}
    need_rows = db.execute(
        select(CompanyProductNeed.company_id, Product.name)
        .join(Product, Product.id == CompanyProductNeed.product_id)
        .where(CompanyProductNeed.company_id.in_(ids))
        .order_by(Product.sort_order)
    ).all()
    for company_id, name in need_rows:
        products[company_id].append(name)
    stages: dict[uuid.UUID, str] = {}
    opportunities = db.scalars(
        select(Opportunity)
        .where(Opportunity.company_id.in_(ids))
        .order_by(Opportunity.updated_at.desc())
    ).all()
    for opportunity in opportunities:
        stages.setdefault(opportunity.company_id, opportunity.stage)
    counts = dict(
        db.execute(
            select(Contact.company_id, func.count())
            .where(Contact.company_id.in_(ids))
            .group_by(Contact.company_id)
        ).all()
    )
    owner_ids = {row.owner_user_id for row in rows if row.owner_user_id}
    industry_ids = {row.industry_id for row in rows if row.industry_id}
    owners = {
        user.id: user.display_name
        for user in db.scalars(select(User).where(User.id.in_(owner_ids))).all()
    } if owner_ids else {}
    industries = {
        industry.id: industry.name
        for industry in db.scalars(select(Industry).where(Industry.id.in_(industry_ids))).all()
    } if industry_ids else {}
    return [
        AccountOut(
            id=row.id,
            display_name=row.display_name,
            normalized_name=row.normalized_name,
            city=row.city,
            state=row.state,
            country=row.country,
            notes=row.notes,
            source_origin=row.source_origin,
            review_status=row.review_status,
            review_label=row.review_label,
            owner_user_id=row.owner_user_id,
            owner_name=owners.get(row.owner_user_id) if row.owner_user_id else None,
            industry_id=row.industry_id,
            industry_name=industries.get(row.industry_id) if row.industry_id else None,
            tags=sorted(tags.get(row.id, [])),
            products=products.get(row.id, []),
            stage=stages.get(row.id),
            contact_count=int(counts.get(row.id, 0)),
            created_at=row.created_at,
        )
        for row in rows
    ]


def _detail(db: Session, company: Company) -> AccountDetail:
    card = _cards(db, [company])[0]
    needs = []
    for need, name in db.execute(
        select(CompanyProductNeed, Product.name)
        .join(Product, Product.id == CompanyProductNeed.product_id)
        .where(CompanyProductNeed.company_id == company.id)
        .order_by(Product.sort_order)
    ).all():
        needs.append(
            NeedOut(
                id=need.id,
                product_name=name,
                need_status=need.need_status,
                evidence_note=need.evidence_note,
            )
        )
    contacts = [
        ContactOut(
            id=contact.id,
            display_name=contact.display_name,
            role_title=contact.role_title,
            email=contact.email,
            phone=contact.phone,
            source_note=contact.source_note,
            source_url=contact.source_url,
            permission_basis=contact.permission_basis,
            do_not_call=contact.do_not_call,
        )
        for contact in db.scalars(
            select(Contact).where(Contact.company_id == company.id).order_by(Contact.created_at)
        ).all()
    ]
    notes = []
    for note, author in db.execute(
        select(CompanyNote, User.display_name)
        .join(User, User.id == CompanyNote.author_user_id)
        .where(CompanyNote.company_id == company.id)
        .order_by(CompanyNote.created_at)
    ).all():
        notes.append(
            NoteOut(id=note.id, body=note.body, author_name=author, created_at=note.created_at)
        )
    opportunity = db.scalar(
        select(Opportunity)
        .where(Opportunity.company_id == company.id)
        .order_by(Opportunity.created_at.asc())
    )
    return AccountDetail(
        **card.model_dump(),
        needs=needs,
        contacts=contacts,
        notes_log=notes,
        opportunity_id=opportunity.id if opportunity else None,
    )


def _owner_emails(db: Session, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}
    return {
        user.id: user.email
        for user in db.scalars(select(User).where(User.id.in_(user_ids))).all()
    }
