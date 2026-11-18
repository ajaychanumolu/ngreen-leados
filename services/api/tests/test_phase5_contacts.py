"""Public business emails stay unpermissioned. Unknown permission cannot call."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from support import auth as _auth
from support import login as _login

from ngreen_api.contact_research import business_emails
from ngreen_api.research_extract import assess_sources
from ngreen_api.research_search import Hit
from ngreen_api.settings import get_settings


def _company(client: TestClient, token: str, name: str = "North Depot Public") -> str:
    created = client.post(
        "/api/v1/accounts",
        headers=_auth(token),
        json={"display_name": name},
    )
    assert created.status_code == 201, created.text
    return created.json()["id"]


def test_unknown_permission_blocks_and_opt_out_sticks(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    sales = _login(client, "sales@ngreen.demo")
    company_id = _company(client, owner)
    denied = client.post(
        "/api/v1/contacts/discover",
        headers=_auth(sales),
        json={"company_id": company_id},
    )
    assert denied.status_code == 403

    created = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": company_id,
            "display_name": "Desk",
            "email": "procurement@northdepot.example",
            "phone": "+14155552671",
            "source_note": "Typed by staff from a contract",
            "permission_basis": "unknown",
        },
    )
    assert created.status_code == 201, created.text
    contact = created.json()
    assert contact["call_allowed"] is False
    assert "permission basis is unknown" in contact["call_reasons"]
    refused = client.post("/api/v1/calls/start", headers=_auth(owner), json={})
    assert refused.status_code == 403
    assert refused.json()["code"] == "live_disabled"

    granted = client.post(
        f"/api/v1/contacts/{contact['id']}/permissions",
        headers=_auth(owner),
        json={
            "basis": "recorded_consent",
            "channel_scope": "phone",
            "proof_note": "Written consent is on the account file.",
            "expires_at": "2099-01-01T00:00:00Z",
        },
    )
    assert granted.status_code == 200, granted.text
    assert granted.json()["call_allowed"] is False
    assert "live voice provider is disabled" in granted.json()["call_reasons"]

    opted = client.post(
        f"/api/v1/contacts/{contact['id']}/opt-out",
        headers=_auth(owner),
        json={"reason": "They asked us to stop"},
    )
    assert opted.status_code == 200, opted.text
    assert opted.json()["do_not_call"] is True
    assert "contact is marked do not call" in opted.json()["call_reasons"]
    again = client.post(
        f"/api/v1/contacts/{contact['id']}/permissions",
        headers=_auth(owner),
        json={
            "basis": "recorded_consent",
            "channel_scope": "phone",
            "proof_note": "Trying to override the opt-out.",
        },
    )
    assert again.status_code == 409


def test_discover_keeps_only_official_emails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _login(client, "owner@ngreen.demo")
    company_id = _company(client, owner, "North Depot Public")
    empty = client.post(
        "/api/v1/contacts/discover",
        headers=_auth(owner),
        json={"company_id": company_id},
    )
    assert empty.status_code == 200, empty.text
    assert empty.json()["created"] == []
    assert "does not invent" in empty.json()["message"]

    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    get_settings.cache_clear()

    class Stub:
        def search(self, query: str, limit: int) -> list[Hit]:
            return [
                Hit(
                    title="North Depot Public contact",
                    url="https://linkedin.com/in/someone",
                    snippet="Email procurement@northdepot.example",
                ),
                Hit(
                    title="North Depot Public contact",
                    url="https://northdepot.example/contact",
                    snippet="Write procurement@northdepot.example or personal name@gmail.com.",
                ),
            ]

    monkeypatch.setattr("ngreen_api.contact_research.SerperProvider", lambda _key: Stub())
    found = client.post(
        "/api/v1/contacts/discover",
        headers=_auth(owner),
        json={"company_id": company_id},
    )
    assert found.status_code == 200, found.text
    created = found.json()["created"]
    assert [item["email"] for item in created] == ["procurement@northdepot.example"]
    assert created[0]["permission_basis"] == "unknown"
    assert created[0]["call_allowed"] is False
    assert created[0]["source_url"] == "https://northdepot.example/contact"
    assert business_emails(
        "North Depot Public",
        "Call +919876543210",
        "https://northdepot.example/contact",
        "North Depot Public",
        None,
    ) == []


def test_groq_quotes_still_have_to_be_in_the_snippet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("AI_API_KEY", "test-key")
    monkeypatch.setenv("AI_MODEL", "openai/gpt-oss-20b")
    get_settings.cache_clear()
    seen: dict[str, str] = {}

    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {"quotes": [{"quote": "not in the page", "kind": "buyer"}]}
                                )
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                }
            ).encode()

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    def capture(request, **_kwargs):
        seen["url"] = request.full_url
        seen["agent"] = request.get_header("User-agent")
        return FakeResponse()

    monkeypatch.setattr("ngreen_api.research_extract.urllib.request.urlopen", capture)
    score, accepted, dropped, _contradiction, extracted = assess_sources(
        ["A public directory page."],
        product="Carry Bags",
        geography="Hyderabad",
        industry=None,
    )
    assert "api.groq.com" in seen["url"]
    assert seen["agent"] == "ngreen-leados/0.1"
    assert extracted.provider == "groq"
    assert extracted.model == "openai/gpt-oss-20b"
    assert accepted == []
    assert dropped == 1
    assert score.breakdown.buyer_relevant_evidence == 0
