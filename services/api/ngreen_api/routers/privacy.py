"""Personal-data export, erasure, and the staff audit list."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, require_privacy
from ngreen_api.models import AuditEvent, SimulatedCall
from ngreen_api.privacy import wipe_contact
from ngreen_api.records import audit
from ngreen_api.routers.contacts import _owned, _suppress

router = APIRouter(prefix="/api/v1", tags=["privacy"])


class CallExport(BaseModel):
    id: uuid.UUID
    outcome: str
    transcript: str
    mode: str
    dialed: bool
    created_at: datetime


class ContactExport(BaseModel):
    contact_id: uuid.UUID
    display_name: str | None
    email: str | None
    phone: str | None
    source_url: str | None
    calls: list[CallExport]


class AuditItem(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID
    entity_type: str
    entity_id: str
    action: str
    summary: str
    created_at: datetime


class AuditPage(BaseModel):
    items: list[AuditItem]
    page: int
    page_size: int
    total: int


@router.get("/privacy/contacts/{contact_id}", response_model=ContactExport)
def export_contact(
    contact_id: uuid.UUID,
    actor: Actor = Depends(require_privacy),
    db: Session = Depends(get_db),
) -> ContactExport:
    contact = _owned(db, actor, contact_id)
    calls = db.scalars(
        select(SimulatedCall)
        .where(SimulatedCall.contact_id == contact.id)
        .order_by(SimulatedCall.created_at)
    ).all()
    return ContactExport(
        contact_id=contact.id,
        display_name=contact.display_name,
        email=contact.email,
        phone=contact.phone,
        source_url=contact.source_url,
        calls=[
            CallExport(
                id=call.id,
                outcome=call.outcome,
                transcript=call.transcript,
                mode=call.mode,
                dialed=call.dialed,
                created_at=call.created_at,
            )
            for call in calls
        ],
    )


@router.post("/privacy/contacts/{contact_id}/erase", status_code=204)
def erase_contact(
    contact_id: uuid.UUID,
    actor: Actor = Depends(require_privacy),
    db: Session = Depends(get_db),
) -> None:
    contact = _owned(db, actor, contact_id)
    _suppress(db, actor, contact, "Contact erased; suppression kept")
    wipe_contact(db, contact)
    audit(
        db,
        actor,
        "contact",
        str(contact_id),
        "erase",
        "Erased a contact. The address, phone, and transcript were removed.",
    )
    db.commit()


@router.get("/audit", response_model=AuditPage)
def list_audit(
    page: int = 1,
    page_size: int = 50,
    actor: Actor = Depends(require_privacy),
    db: Session = Depends(get_db),
) -> AuditPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    base = select(AuditEvent).where(AuditEvent.organization_id == actor.organization_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(AuditEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return AuditPage(
        items=[
            AuditItem(
                id=row.id,
                actor_user_id=row.actor_user_id,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                action=row.action,
                summary=row.summary,
                created_at=row.created_at,
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )
