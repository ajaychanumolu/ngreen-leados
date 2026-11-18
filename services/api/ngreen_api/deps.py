"""Request dependencies. Application role comes from memberships."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.models import Membership, User
from ngreen_api.security import verify_access_token
from ngreen_contracts.enums import StaffRole

_bearer = HTTPBearer(auto_error=False)

WRITE_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN.value,
        StaffRole.RESEARCHER.value,
        StaffRole.SALES_EXECUTIVE.value,
        StaffRole.MANAGER.value,
    }
)
IMPORT_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN.value,
        StaffRole.RESEARCHER.value,
        StaffRole.MANAGER.value,
    }
)
CRM_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN.value,
        StaffRole.SALES_EXECUTIVE.value,
        StaffRole.MANAGER.value,
    }
)


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Actor:
    user: User
    membership: Membership

    @property
    def organization_id(self) -> uuid.UUID:
        return self.membership.organization_id

    @property
    def role(self) -> str:
        return self.membership.role


def get_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Actor:
    if credentials is None or not credentials.credentials:
        raise ApiError(401, "not_authenticated", "Sign in required.")
    try:
        verified = verify_access_token(credentials.credentials)
    except (PermissionError, jwt.PyJWTError, ValueError) as exc:
        message = str(exc) if isinstance(exc, PermissionError) else "Sign in required."
        raise ApiError(401, "not_authenticated", message) from exc
    user = db.get(User, verified.user_id)
    if user is None:
        raise ApiError(401, "not_authenticated", "Sign in required.")
    membership = db.scalar(select(Membership).where(Membership.user_id == user.id))
    if membership is None:
        raise ApiError(403, "forbidden", "No organization membership.")
    return Actor(user=user, membership=membership)


def require_writer(actor: Actor = Depends(get_actor)) -> Actor:
    if actor.role not in WRITE_ROLES:
        raise ApiError(403, "forbidden", "This role cannot edit accounts.")
    return actor


def require_importer(actor: Actor = Depends(get_actor)) -> Actor:
    if actor.role not in IMPORT_ROLES:
        raise ApiError(403, "forbidden", "This role cannot import accounts.")
    return actor


def require_crm(actor: Actor = Depends(get_actor)) -> Actor:
    if actor.role not in CRM_ROLES:
        raise ApiError(403, "forbidden", "This role cannot move opportunities.")
    return actor


REPORT_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN.value,
        StaffRole.MANAGER.value,
        StaffRole.READ_ONLY.value,
    }
)


def require_reports(actor: Actor = Depends(get_actor)) -> Actor:
    if actor.role not in REPORT_ROLES:
        raise ApiError(403, "forbidden", "This role cannot view reports.")
    return actor


PRIVACY_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN.value,
        StaffRole.MANAGER.value,
    }
)


def require_privacy(actor: Actor = Depends(get_actor)) -> Actor:
    if actor.role not in PRIVACY_ROLES:
        raise ApiError(403, "forbidden", "This role cannot export or erase personal data.")
    return actor
