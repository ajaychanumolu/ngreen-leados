"""Voice providers. The sandbox never opens a network connection."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

_INDIA = ZoneInfo("Asia/Kolkata")
_OPEN = 9
_CLOSE = 18


@dataclass(frozen=True)
class VoiceRequest:
    destination_e164: str
    assistant_id: str
    phone_number_id: str


@dataclass(frozen=True)
class VoiceResult:
    placed: bool
    provider: str
    provider_call_id: str | None
    detail: str


class SandboxVoiceProvider:
    """Used while legal approval or the live flag is missing. Places nothing."""

    name = "sandbox"

    def place(self, request: VoiceRequest) -> VoiceResult:
        del request
        return VoiceResult(
            False,
            self.name,
            None,
            "Live calling is disabled. No request was sent.",
        )


class VapiVoiceProvider:
    """POST https://api.vapi.ai/call for one saved assistant and one customer."""

    name = "vapi"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def place(self, request: VoiceRequest) -> VoiceResult:
        payload = {
            "assistantId": request.assistant_id,
            "phoneNumberId": request.phone_number_id,
            "customer": {"number": request.destination_e164},
        }
        outgoing = urllib.request.Request(
            "https://api.vapi.ai/call",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ngreen-leados/0.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(outgoing, timeout=20) as response:
                body = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return VoiceResult(False, self.name, None, f"Vapi returned {exc.code}.")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return VoiceResult(False, self.name, None, "Vapi did not accept the call.")
        call_id = str(body.get("id") or "")[:80] or None
        return VoiceResult(True, self.name, call_id, "Vapi accepted one call.")


def within_calling_hours(now: datetime) -> bool:
    local = now.astimezone(_INDIA)
    return local.weekday() < 5 and _OPEN <= local.hour < _CLOSE


def live_blockers(
    *,
    legal_approved: bool,
    live_enabled: bool,
    test_contact_id: str,
    contact_id: str,
    phone_number_id: str,
    assistant_id: str,
    decision_reasons: list[str],
    now: datetime,
    in_flight: int,
    spent_today: int,
    daily_cap: int,
    concurrent_cap: int,
) -> list[str]:
    reasons: list[str] = []
    if not legal_approved:
        reasons.append("legal and telecom approval is missing")
    if not live_enabled:
        reasons.append("live voice provider is disabled")
    if not test_contact_id:
        reasons.append("no named test contact is approved")
    elif contact_id != test_contact_id:
        reasons.append("this contact is not the approved test contact")
    if not phone_number_id:
        reasons.append("caller number is not configured")
    if not assistant_id:
        reasons.append("saved call assistant is not configured")
    reasons.extend(decision_reasons)
    if not within_calling_hours(now):
        reasons.append("outside the allowed calling hours")
    if in_flight >= concurrent_cap:
        reasons.append("too many live calls are already in progress")
    if spent_today >= daily_cap:
        reasons.append("the daily call cap is reached")
    unique: list[str] = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    return unique
