"""DEMO rehearsals never dial. Interest creates one task. Opt-out blocks the next attempt."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from support import auth as _auth
from support import login as _login

from ngreen_api.research_search import looks_like_packaging_seller, plan_queries
from ngreen_api.settings import get_settings


def test_search_targets_buyers_and_drops_packaging_sellers() -> None:
    planned = plan_queries("Carry Bags", "Pune", None, 3)
    assert planned
    assert all(" supplier " not in query for query in planned)
    assert any("-supplier" in query for query in planned)
    assert looks_like_packaging_seller(
        "Top Carry Bag Wholesalers in Pune",
        "We supply paper bags.",
        "justdial.com",
    )
    assert looks_like_packaging_seller(
        "Carry bag tender",
        "Hotel procurement requirement",
        "tenderkart.in",
    )
    assert looks_like_packaging_seller(
        "Customized Paper Carry Bags for Restaurants",
        "Premium paper bags for hotels.",
        "arrowpaperproducts.com",
    )
    assert not looks_like_packaging_seller(
        "Hotel group procurement",
        "We need Carry Bags for our stores.",
        "example-hotel.com",
    )


def test_interest_creates_one_task_and_opt_out_blocks_the_next_call(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    researcher = _login(client, "researcher@ngreen.demo")
    accounts = client.get("/api/v1/accounts?page_size=1", headers=_auth(owner))
    company_id = accounts.json()["items"][0]["id"]
    created = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": company_id,
            "display_name": "Buyer desk",
            "email": "desk@buyer.example",
            "phone": "+14155552671",
            "source_note": "Typed from a contract the team already holds.",
            "permission_basis": "unknown",
        },
    )
    assert created.status_code == 201, created.text
    contact_id = created.json()["id"]
    saved = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={
            "contact_id": contact_id,
            "transcript": "Interested in Courier Bags and wants a sample next week.",
        },
    )
    assert saved.status_code == 201, saved.text
    assert saved.json()["dialed"] is False
    granted = client.post(
        f"/api/v1/contacts/{contact_id}/permissions",
        headers=_auth(owner),
        json={
            "basis": "recorded_consent",
            "channel_scope": "phone",
            "proof_note": "Written consent is on the account file.",
            "expires_at": "2099-01-01T00:00:00Z",
        },
    )
    assert granted.status_code == 200, granted.text
    denied = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(researcher),
        json={
            "contact_id": contact_id,
            "transcript": "Interested in Courier Bags and wants a sample next week.",
        },
    )
    assert denied.status_code == 403
    simulated = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={
            "contact_id": contact_id,
            "transcript": "Interested in Courier Bags and wants a sample next week.",
        },
    )
    assert simulated.status_code == 201, simulated.text
    call = simulated.json()
    assert call["dialed"] is False
    assert call["mode"] == "demo"
    assert call["outcome"] == "interested"
    assert call["review_status"] == "pending"
    board = client.get("/api/v1/opportunities?page_size=100", headers=_auth(owner))
    assert board.status_code == 200
    placed = next(item for item in board.json()["items"] if item["company_id"] == company_id)
    assert placed["stage"] == "contacted"
    refused = client.post("/api/v1/calls/start", headers=_auth(owner), json={})
    assert refused.status_code == 403
    assert refused.json()["code"] == "live_disabled"
    before = client.get("/api/v1/tasks", headers=_auth(owner)).json()["total"]
    accepted = client.post(
        f"/api/v1/calls/{call['id']}/review",
        headers=_auth(owner),
        json={"action": "accept"},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["review_status"] == "accepted"
    after = client.get("/api/v1/tasks", headers=_auth(owner)).json()
    assert after["total"] == before + 1
    again = client.post(
        f"/api/v1/calls/{call['id']}/review",
        headers=_auth(owner),
        json={"action": "accept"},
    )
    assert again.status_code == 409

    opted = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={"contact_id": contact_id, "transcript": "Please never contact me again."},
    )
    assert opted.status_code == 201, opted.text
    assert opted.json()["do_not_call"] is True
    assert opted.json()["dialed"] is False
    listed = client.get("/api/v1/contacts?page_size=100", headers=_auth(owner))
    assert listed.status_code == 200
    match = next(item for item in listed.json()["items"] if item["id"] == contact_id)
    assert match["do_not_call"] is True
    repeat = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={"contact_id": contact_id, "transcript": "Interested in a sample next week."},
    )
    assert repeat.status_code == 409
    assert repeat.json()["code"] == "do_not_call"


def test_webhook_replay_does_not_create_a_second_call(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    assert created.status_code == 201, created.text
    payload = {
        "provider_call_id": "demo-call-1",
        "provider_event_id": "event-1",
        "contact_id": created.json()["id"],
        "transcript": "The buyer asked for a meeting next week.",
    }
    unsigned = client.post("/api/v1/integrations/voice/webhook", json=payload)
    assert unsigned.status_code == 401
    headers = {"X-Demo-Voice-Signature": "demo-webhook"}
    first = client.post("/api/v1/integrations/voice/webhook", headers=headers, json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["dialed"] is False
    assert first.json()["outcome"] == "meeting_requested"
    assert first.json()["event_count"] == 1
    second = client.post("/api/v1/integrations/voice/webhook", headers=headers, json=payload)
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["event_count"] == 1
