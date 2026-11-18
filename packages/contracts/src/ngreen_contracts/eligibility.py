"""Fail-closed gate for a live outbound call.

A passing decision is necessary and still not sufficient: Phase 7 also requires
an approved provider, a signed webhook, a budget, and a named test contact.
This module does not place a call.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from ngreen_contracts.enums import PermissionBasis, StaffRole

_E164 = re.compile(r"^\+[1-9]\d{7,14}$")

_CALL_ROLES = frozenset(
    {
        StaffRole.OWNER_ADMIN,
        StaffRole.SALES_EXECUTIVE,
        StaffRole.MANAGER,
    }
)


@dataclass(frozen=True)
class LiveCallDecision:
    allowed: bool
    reasons: tuple[str, ...]


def destination_is_e164(value: str | None) -> bool:
    if value is None:
        return False
    return _E164.fullmatch(value) is not None


def evaluate_live_call(
    *,
    voice_live_enabled: bool,
    actor_role: StaffRole,
    destination_e164: str | None,
    permission_basis: PermissionBasis,
    do_not_call: bool,
    permission_revoked: bool,
    suppressed: bool,
    expires_at: datetime | None,
    now: datetime,
) -> LiveCallDecision:
    reasons: list[str] = []
    if not voice_live_enabled:
        reasons.append("live voice provider is disabled")
    if actor_role not in _CALL_ROLES:
        reasons.append("actor role cannot authorize a live call")
    if not destination_is_e164(destination_e164):
        reasons.append("destination is not a valid E.164 number")
    if permission_basis is PermissionBasis.UNKNOWN:
        reasons.append("permission basis is unknown")
    if do_not_call:
        reasons.append("contact is marked do not call")
    if permission_revoked:
        reasons.append("permission was revoked")
    if suppressed:
        reasons.append("destination is on the suppression list")
    if expires_at is not None:
        if expires_at.tzinfo is None or now.tzinfo is None:
            raise ValueError("expires_at and now must be timezone-aware")
        if expires_at.astimezone(UTC) <= now.astimezone(UTC):
            reasons.append("permission has expired")
    return LiveCallDecision(allowed=len(reasons) == 0, reasons=tuple(reasons))
