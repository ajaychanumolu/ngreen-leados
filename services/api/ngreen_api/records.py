"""Shared account lookups and audit rows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.deps import Actor, ApiError
from ngreen_api.models import AuditEvent, Company, Membership, Product


def owned_company(db: Session, actor: Actor, account_id: uuid.UUID) -> Company:
    company = db.get(Company, account_id)
    if company is None or company.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Account not found.")
    return company


def audit(
    db: Session, actor: Actor, entity_type: str, entity_id: str, action: str, summary: str
) -> None:
    db.add(
        AuditEvent(
            organization_id=actor.organization_id,
            actor_user_id=actor.user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            summary=summary[:500],
        )
    )


def require_member(db: Session, actor: Actor, user_id: uuid.UUID) -> Membership:
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == actor.organization_id,
            Membership.user_id == user_id,
        )
    )
    if membership is None:
        raise ApiError(422, "validation_error", "Owner must belong to this organization.")
    return membership


def product_named(db: Session, actor: Actor, name: str) -> Product:
    product = db.scalar(
        select(Product).where(
            Product.organization_id == actor.organization_id, Product.name == name
        )
    )
    if product is None:
        raise ApiError(422, "validation_error", f"Unknown product: {name}")
    return product


def clean_tag(raw: str) -> str:
    label = " ".join(raw.strip().split()).casefold()
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789 -")
    if not label or len(label) > 40 or any(character not in allowed for character in label):
        raise ApiError(
            422,
            "validation_error",
            "Tags use letters, numbers, spaces, and hyphens, up to 40 characters.",
        )
    return label


def blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
