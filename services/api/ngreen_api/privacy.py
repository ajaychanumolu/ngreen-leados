"""Delete stored personal rows for one contact. Suppression hashes stay."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.models import CallEvent, Contact, ContactPermission, SimulatedCall


def wipe_contact(db: Session, contact: Contact) -> None:
    calls = db.scalars(select(SimulatedCall).where(SimulatedCall.contact_id == contact.id)).all()
    for call in calls:
        events = db.scalars(select(CallEvent).where(CallEvent.call_id == call.id)).all()
        for event in events:
            db.delete(event)
        db.delete(call)
    permissions = db.scalars(
        select(ContactPermission).where(ContactPermission.contact_id == contact.id)
    ).all()
    for permission in permissions:
        db.delete(permission)
    db.delete(contact)
