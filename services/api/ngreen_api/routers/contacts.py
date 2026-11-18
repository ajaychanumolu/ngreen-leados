import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.contact_research import channel_hash, discover_public_contacts
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_importer, require_writer
from ngreen_api.models import Company, Contact, ContactPermission, Suppression
from ngreen_api.privacy import wipe_contact
from ngreen_api.records import audit, blank, owned_company
from ngreen_api.research_search import ProviderOutage
from ngreen_api.settings import get_settings
from ngreen_contracts.eligibility import evaluate_live_call
from ngreen_contracts.enums import PermissionBasis, StaffRole

router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class ContactBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: uuid.UUID
    display_name: str | None = Field(default=None, max_length=200)
    role_title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    source_note: str = Field(min_length=3, max_length=500)
    permission_basis: PermissionBasis = PermissionBasis.UNKNOWN


class ContactPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=200)
    role_title: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    source_note: str | None = Field(default=None, min_length=3, max_length=500)
    permission_basis: PermissionBasis | None = None


class ContactOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    display_name: str | None
    role_title: str | None
    email: str | None
    phone: str | None
    source_note: str
    source_url: str | None = None
    permission_basis: str
    do_not_call: bool = False
    validity: str = "unverified"
    channel_scope: str = "none"
    call_allowed: bool = False
    call_reasons: list[str] = Field(default_factory=list)


class ContactPage(BaseModel):
    items: list[ContactOut]
    page: int
    page_size: int
    total: int


class DiscoverBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: uuid.UUID


class DiscoverOut(BaseModel):
    created: list[ContactOut]
    skipped_sources: int
    message: str


class PermissionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basis: PermissionBasis
    channel_scope: str = Field(pattern="^(email|phone|both)$")
    proof_note: str = Field(min_length=3, max_length=500)
    expires_at: datetime | None = None


class OptOutBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="Staff recorded do not call", min_length=3, max_length=200)


@router.get("", response_model=ContactPage)
def list_contacts(
    page: int = 1,
    page_size: int = 50,
    company_id: uuid.UUID | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> ContactPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    base = select(Contact).where(Contact.organization_id == actor.organization_id)
    if company_id is not None:
        owned_company(db, actor, company_id)
        base = base.where(Contact.company_id == company_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(Contact.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return ContactPage(
        items=[_out(db, row, actor) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.post("/discover", response_model=DiscoverOut)
def discover_contacts(
    body: DiscoverBody,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> DiscoverOut:
    company = owned_company(db, actor, body.company_id)
    try:
        result = discover_public_contacts(db, company, actor.user.id)
    except ProviderOutage as exc:
        raise ApiError(502, "provider_outage", str(exc)) from exc
    audit(db, actor, "contact", str(company.id), "discover", result.message)
    db.commit()
    for contact in result.created:
        db.refresh(contact)
    return DiscoverOut(
        created=[_out(db, contact, actor) for contact in result.created],
        skipped_sources=result.skipped_sources,
        message=result.message,
    )


@router.post("", response_model=ContactOut, status_code=201)
def create_contact(
    body: ContactBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> ContactOut:
    company = owned_company(db, actor, body.company_id)
    contact = _build(company, actor, body)
    db.add(contact)
    audit(db, actor, "contact", str(company.id), "create", "Added a manual contact")
    db.commit()
    db.refresh(contact)
    return _out(db, contact, actor)


@router.patch("/{contact_id}", response_model=ContactOut)
def patch_contact(
    contact_id: uuid.UUID,
    body: ContactPatch,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> ContactOut:
    contact = _owned(db, actor, contact_id)
    fields = body.model_fields_set
    if "display_name" in fields:
        contact.display_name = blank(body.display_name)
    if "role_title" in fields:
        contact.role_title = blank(body.role_title)
    if "email" in fields:
        contact.email = _email(body.email)
    if "phone" in fields:
        contact.phone = _phone(body.phone)
    if "source_note" in fields and body.source_note is not None:
        contact.source_note = body.source_note.strip()
    if "permission_basis" in fields and body.permission_basis is not None:
        contact.permission_basis = body.permission_basis.value
    _require_identity(contact.display_name, contact.email, contact.phone)
    audit(db, actor, "contact", str(contact.id), "update", "Updated a manual contact")
    db.commit()
    db.refresh(contact)
    return _out(db, contact, actor)


@router.post("/{contact_id}/permissions", response_model=ContactOut)
def record_permission(
    contact_id: uuid.UUID,
    body: PermissionBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> ContactOut:
    contact = _owned(db, actor, contact_id)
    if body.basis is PermissionBasis.UNKNOWN:
        raise ApiError(422, "validation_error", "Unknown permission cannot authorize a call.")
    if contact.do_not_call or contact.permission_revoked:
        raise ApiError(
            409,
            "do_not_call",
            "This contact is opted out. A new permission does not override that.",
        )
    if body.expires_at is not None and body.expires_at.tzinfo is None:
        raise ApiError(422, "validation_error", "Expiry must include a timezone.")
    contact.permission_basis = body.basis.value
    contact.channel_scope = body.channel_scope
    contact.permission_expires_at = body.expires_at
    contact.owner_user_id = actor.user.id
    db.add(
        ContactPermission(
            organization_id=actor.organization_id,
            contact_id=contact.id,
            basis=body.basis.value,
            channel_scope=body.channel_scope,
            proof_note=body.proof_note.strip(),
            expires_at=body.expires_at,
            recorded_by=actor.user.id,
        )
    )
    audit(db, actor, "contact", str(contact.id), "permission", "Recorded a call permission")
    db.commit()
    db.refresh(contact)
    return _out(db, contact, actor)


@router.post("/{contact_id}/opt-out", response_model=ContactOut)
def opt_out(
    contact_id: uuid.UUID,
    body: OptOutBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> ContactOut:
    contact = _owned(db, actor, contact_id)
    contact.do_not_call = True
    contact.permission_revoked = True
    contact.channel_scope = "none"
    _suppress(db, actor, contact, body.reason.strip())
    audit(db, actor, "contact", str(contact.id), "opt_out", "Recorded do not call")
    db.commit()
    db.refresh(contact)
    return _out(db, contact, actor)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(
    contact_id: uuid.UUID,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> None:
    contact = _owned(db, actor, contact_id)
    _suppress(db, actor, contact, "Contact deleted; suppression kept")
    wipe_contact(db, contact)
    audit(db, actor, "contact", str(contact_id), "delete", "Deleted a contact and kept suppression")
    db.commit()


def _build(company: Company, actor: Actor, body: ContactBody) -> Contact:
    name = blank(body.display_name)
    email = _email(body.email)
    phone = _phone(body.phone)
    _require_identity(name, email, phone)
    return Contact(
        organization_id=actor.organization_id,
        company_id=company.id,
        display_name=name,
        role_title=blank(body.role_title),
        email=email,
        phone=phone,
        source_note=body.source_note.strip(),
        permission_basis=body.permission_basis.value,
        created_by=actor.user.id,
    )


def _owned(db: Session, actor: Actor, contact_id: uuid.UUID) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None or contact.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Contact not found.")
    return contact


def _out(db: Session, contact: Contact, actor: Actor) -> ContactOut:
    company = db.get(Company, contact.company_id)
    expires_at = contact.permission_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    decision = evaluate_live_call(
        voice_live_enabled=get_settings().voice_live_enabled,
        actor_role=StaffRole(actor.role),
        destination_e164=contact.phone,
        permission_basis=PermissionBasis(contact.permission_basis),
        do_not_call=contact.do_not_call,
        permission_revoked=contact.permission_revoked,
        suppressed=_suppressed(db, contact),
        expires_at=expires_at,
        now=datetime.now(UTC),
    )
    return ContactOut(
        id=contact.id,
        company_id=contact.company_id,
        company_name=company.display_name if company else "",
        display_name=contact.display_name,
        role_title=contact.role_title,
        email=contact.email,
        phone=contact.phone,
        source_note=contact.source_note,
        source_url=contact.source_url,
        permission_basis=contact.permission_basis,
        do_not_call=contact.do_not_call,
        validity=contact.validity,
        channel_scope=contact.channel_scope,
        call_allowed=decision.allowed,
        call_reasons=list(decision.reasons),
    )


def _suppress(db: Session, actor: Actor, contact: Contact, reason: str) -> None:
    values = [("email", contact.email), ("phone", contact.phone)]
    for kind, value in values:
        if not value:
            continue
        digest = channel_hash(actor.organization_id, kind, value)
        existing = db.scalar(
            select(Suppression).where(
                Suppression.organization_id == actor.organization_id,
                Suppression.channel_hash == digest,
            )
        )
        if existing is None:
            db.add(
                Suppression(
                    organization_id=actor.organization_id,
                    channel_hash=digest,
                    channel_kind=kind,
                    reason=reason[:200],
                )
            )


def _suppressed(db: Session, contact: Contact) -> bool:
    for kind, value in (("email", contact.email), ("phone", contact.phone)):
        if not value:
            continue
        digest = channel_hash(contact.organization_id, kind, value)
        found = db.scalar(
            select(Suppression.id).where(
                Suppression.organization_id == contact.organization_id,
                Suppression.channel_hash == digest,
            )
        )
        if found is not None:
            return True
    return False


def _require_identity(name: str | None, email: str | None, phone: str | None) -> None:
    if not name and not email and not phone:
        raise ApiError(
            422,
            "validation_error",
            "A contact needs a name, an email, or a phone number that you already have.",
        )


def _email(value: str | None) -> str | None:
    cleaned = blank(value)
    if cleaned is None:
        return None
    if (
        " " in cleaned
        or cleaned.count("@") != 1
        or cleaned.startswith("@")
        or cleaned.endswith("@")
    ):
        raise ApiError(422, "validation_error", "Email is not valid.")
    return cleaned


def _phone(value: str | None) -> str | None:
    cleaned = blank(value)
    if cleaned is None:
        return None
    allowed = set("0123456789 +-()")
    if any(character not in allowed for character in cleaned):
        raise ApiError(422, "validation_error", "Phone can contain digits, spaces, and + - ( ).")
    return cleaned
