"""Live calling stays disabled. The Vapi request shape is one number, and only in a stub."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from support import auth as _auth
from support import login as _login

from ngreen_api.settings import get_settings
from ngreen_api.voice_provider import VapiVoiceProvider, VoiceRequest, within_calling_hours


def test_default_start_does_not_call_the_provider(client: TestClient, monkeypatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("urlopen must not run while live calling is disabled")

    monkeypatch.setattr("ngreen_api.voice_provider.urllib.request.urlopen", explode)
    owner = _login(client, "owner@ngreen.demo")
    accounts = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner))
    company_id = accounts.json()["items"][0]["id"]
    created = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": company_id,
            "display_name": "Buyer desk",
            "phone": "+14155552671",
            "source_note": "Typed from a contract the team already holds.",
            "permission_basis": "recorded_consent",
        },
    )
    assert created.status_code == 201, created.text
    refused = client.post(
        "/api/v1/calls/start",
        headers=_auth(owner),
        json={"contact_id": created.json()["id"]},
    )
    assert refused.status_code == 403
    assert refused.json()["code"] == "live_disabled"
    assert "No number was dialed" in refused.json()["message"]


def test_opt_out_blocks_even_when_the_live_flags_are_on(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("urlopen must not run for an opted-out contact")

    monkeypatch.setattr("ngreen_api.voice_provider.urllib.request.urlopen", explode)
    owner = _login(client, "owner@ngreen.demo")
    accounts = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner))
    company_id = accounts.json()["items"][0]["id"]
    created = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": company_id,
            "display_name": "Buyer desk",
            "phone": "+14155552671",
            "source_note": "Typed from a contract the team already holds.",
            "permission_basis": "recorded_consent",
        },
    )
    contact_id = created.json()["id"]
    opted = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={"contact_id": contact_id, "transcript": "Please never contact me again."},
    )
    assert opted.status_code == 201, opted.text
    monkeypatch.setenv("VOICE_LIVE_ENABLED", "true")
    monkeypatch.setenv("VOICE_LEGAL_APPROVED", "true")
    monkeypatch.setenv("VAPI_API_KEY", "test-key")
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "assistant-1")
    monkeypatch.setenv("VAPI_PHONE_NUMBER_ID", "phone-1")
    monkeypatch.setenv("VOICE_TEST_CONTACT_ID", contact_id)
    get_settings.cache_clear()
    refused = client.post(
        "/api/v1/calls/start",
        headers=_auth(owner),
        json={"contact_id": contact_id},
    )
    assert refused.status_code == 403
    assert "do not call" in refused.json()["message"]


def test_stale_webhook_is_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICE_WEBHOOK_SECRET", "demo-webhook")
    get_settings.cache_clear()
    owner = _login(client, "owner@ngreen.demo")
    accounts = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner))
    company_id = accounts.json()["items"][0]["id"]
    created = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": company_id,
            "display_name": "Webhook desk",
            "phone": "+14155552671",
            "source_note": "Typed from a contract the team already holds.",
            "permission_basis": "recorded_consent",
        },
    )
    payload = {
        "provider_call_id": "demo-call-9",
        "provider_event_id": "event-9",
        "contact_id": created.json()["id"],
        "transcript": "The buyer asked for a meeting next week.",
    }
    stale = client.post(
        "/api/v1/integrations/voice/webhook",
        headers={
            "Authorization": "Bearer demo-webhook",
            "X-Vapi-Timestamp": "2020-01-01T00:00:00Z",
        },
        json=payload,
    )
    assert stale.status_code == 401
    fresh = client.post(
        "/api/v1/integrations/voice/webhook",
        headers={"X-Vapi-Secret": "demo-webhook"},
        json=payload,
    )
    assert fresh.status_code == 200, fresh.text
    assert fresh.json()["dialed"] is False


def test_vapi_payload_is_a_single_customer(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    class FakeResponse:
        def read(self) -> bytes:
            return b'{"id":"call_1"}'

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    def capture(request, **_kwargs):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr("ngreen_api.voice_provider.urllib.request.urlopen", capture)
    result = VapiVoiceProvider("test-key").place(
        VoiceRequest("+14155552671", "assistant-1", "phone-1")
    )
    assert result.placed is True
    assert result.provider_call_id == "call_1"
    assert seen["url"] == "https://api.vapi.ai/call"
    body = seen["body"]
    assert isinstance(body, dict)
    assert body["customer"] == {"number": "+14155552671"}
    assert "customers" not in body


def test_calling_window_is_weekday_daytime_in_india() -> None:
    sunday = datetime(2026, 11, 15, 5, 0, tzinfo=UTC)
    tuesday = datetime(2026, 11, 17, 5, 30, tzinfo=UTC)
    night = datetime(2026, 11, 17, 16, 30, tzinfo=UTC)
    assert within_calling_hours(sunday) is False
    assert within_calling_hours(tuesday) is True
    assert within_calling_hours(night) is False
