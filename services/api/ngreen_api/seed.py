"""DEMO staff for local sign-in. These are not real people."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.catalog_seed import seed_catalog
from ngreen_api.models import Membership, Organization, User
from ngreen_api.security import hash_password
from ngreen_contracts.enums import StaffRole

DEMO_PASSWORD = "demo-pass"
DEMO_STAFF: tuple[tuple[str, str, str], ...] = (
    ("owner@ngreen.demo", "N Green owner", StaffRole.OWNER_ADMIN.value),
    ("researcher@ngreen.demo", "N Green researcher", StaffRole.RESEARCHER.value),
    ("sales@ngreen.demo", "N Green sales", StaffRole.SALES_EXECUTIVE.value),
    ("manager@ngreen.demo", "N Green manager", StaffRole.MANAGER.value),
    ("reader@ngreen.demo", "N Green reader", StaffRole.READ_ONLY.value),
)


def seed_demo(db: Session) -> Organization:
    org = db.scalar(select(Organization).where(Organization.slug == "ngreen"))
    if org is None:
        org = Organization(name="N Green", slug="ngreen")
        db.add(org)
        db.flush()
        for email, name, role in DEMO_STAFF:
            user = User(email=email, display_name=name, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()
            db.add(Membership(organization_id=org.id, user_id=user.id, role=role))
        db.flush()
    seed_catalog(db, org.id)
    db.commit()
    return org
