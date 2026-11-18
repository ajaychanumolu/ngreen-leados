"""DEMO and guarded live research. No candidate is a verified buyer."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient
from support import auth as _auth
from support import login as _login

import ngreen_api.research_search as research_search
from ngreen_api.db import get_session_factory
from ngreen_api.models import ResearchRun
from ngreen_api.research_jobs import execute_run
from ngreen_api.research_search import Hit, ProviderOutage
from ngreen_api.settings import get_settings


def _product_id(client: TestClient, token: str, name: str = "Carry Bags") -> str:
    products = client.get("/api/v1/products", headers=_auth(token))
    assert products.status_code == 200
    return next(item["id"] for item in products.json() if item["name"] == name)


def _run(client: TestClient, token: str, **extra: object) -> dict:
    body = {
        "product_id": _product_id(client, token),
        "geography": "Hyderabad",
        "limit_companies": 3,
        "max_queries": 2,
    }
    body.update(extra)
    response = client.post("/api/v1/research/runs", headers=_auth(token), json=body)
    return response


def test_demo_search_is_labeled_and_does_not_verify_buyers(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    sales = _login(client, "sales@ngreen.demo")
    denied = client.post(
        "/api/v1/research/runs",
        headers=_auth(sales),
        json={
            "product_id": _product_id(client, owner),
            "geography": "Hyderabad",
            "max_queries": 1,
        },
    )
    assert denied.status_code == 403

    created = _run(client, owner)
    assert created.status_code == 201, created.text
    run = created.json()
    assert run["mode"] == "demo"
    assert run["status"] == "completed"
    assert "pending" not in {item["status"] for item in run["queries"]}
    assert run["industry_filter"] is None
    assert run["candidates"]
    labels = {item["review_label"] for item in run["candidates"]}
    assert labels == {"Research candidate – not a verified buyer"}
    assert all(item["canonical_domain"] is None for item in run["candidates"])
    for candidate in run["candidates"]:
        assert candidate["sources"]
        assert candidate["sources"][0]["canonical_url"].startswith("https://example.com/demo/research/")
        assert candidate["sources"][0]["snippet"].startswith("DEMO search fixture")
    health = client.get("/health")
    assert health.json()["research_mode"] == "demo"

    approved = client.post(
        f"/api/v1/research/candidates/{run['candidates'][0]['id']}/review",
        headers=_auth(owner),
        json={"action": "approve"},
    )
    assert approved.status_code == 200, approved.text
    account_id = approved.json()["company_id"]
    account = client.get(f"/api/v1/accounts/{account_id}", headers=_auth(owner))
    body = account.json()
    assert body["source_origin"] == "web_research"
    assert body["industry_id"] is None
    assert body["contact_count"] == 0
    assert body["contacts"] == []
    assert body["needs"]
    assert all(need["need_status"] == "hypothesis" for need in body["needs"])
    assert body["review_label"] == "Research candidate – not a verified buyer"


def test_budget_rate_and_provider_outage(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _login(client, "owner@ngreen.demo")
    monkeypatch.setenv("RESEARCH_BUDGET_CREDITS", "1")
    get_settings.cache_clear()
    blocked = _run(client, owner, max_queries=3)
    assert blocked.status_code == 422
    assert blocked.json()["code"] == "budget_exceeded"
    before = client.get("/api/v1/research/runs", headers=_auth(owner)).json()["total"]

    monkeypatch.setenv("RESEARCH_BUDGET_CREDITS", "5")
    get_settings.cache_clear()

    class Down:
        name = "serper"

        def search(self, query: str, limit: int) -> list[Hit]:
            raise ProviderOutage("Serper returned 503.")

    monkeypatch.setattr("ngreen_api.research_jobs.provider_for", lambda _key: Down())
    failed = _run(client, owner, max_queries=1, limit_companies=2)
    assert failed.status_code == 201, failed.text
    assert failed.json()["status"] == "failed"
    assert failed.json()["candidates"] == []
    assert "503" in (failed.json()["error_summary"] or "")
    assert client.get("/api/v1/research/runs", headers=_auth(owner)).json()["total"] == before + 1

    monkeypatch.setattr(
        "ngreen_api.routers.research.research_is_limited",
        lambda _key: True,
    )
    limited = _run(client, owner, max_queries=1)
    assert limited.status_code == 429


def test_cancel_stops_later_queries_and_live_results_keep_links(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _login(client, "owner@ngreen.demo")
    monkeypatch.setattr("ngreen_api.routers.research.dispatch", lambda _run_id: "sync")
    queued = _run(client, owner, max_queries=2, limit_companies=5)
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "queued"
    run_id = queued.json()["id"]
    cancelled = client.post(f"/api/v1/research/runs/{run_id}/cancel", headers=_auth(owner))
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    again = client.post(f"/api/v1/research/runs/{run_id}/cancel", headers=_auth(owner))
    assert again.status_code == 200
    assert again.json()["status"] == "cancelled"
    execute_run(run_id)
    stored = client.get(f"/api/v1/research/runs/{run_id}", headers=_auth(owner)).json()
    assert stored["queries_done"] == 0
    assert stored["candidates"] == []

    calls = {"n": 0}

    class Stopper:
        name = "demo"

        def search(self, query: str, limit: int) -> list[Hit]:
            calls["n"] += 1
            if calls["n"] == 1:
                db = get_session_factory()()
                try:
                    run = db.get(ResearchRun, uuid.UUID(run_id))
                    assert run is not None
                    run.status = "cancelled"
                    db.commit()
                finally:
                    db.close()
            return [
                Hit(
                    title="DEMO North Depot",
                    url="https://example.com/demo/research/north-depot",
                    snippet="DEMO search fixture.",
                )
            ]

    monkeypatch.setattr("ngreen_api.research_jobs.provider_for", lambda _key: Stopper())
    monkeypatch.setattr(
        "ngreen_api.routers.research.dispatch",
        lambda queued_id: execute_run(queued_id),
    )
    # Use a fresh queued run by retrying the cancelled one, which will execute.
    retried = client.post(f"/api/v1/research/runs/{run_id}/retry", headers=_auth(owner))
    assert retried.status_code == 200, retried.text
    assert calls["n"] == 1
    assert retried.json()["status"] == "cancelled"

    class FakeResponse:
        def read(self) -> bytes:
            return json.dumps(
                {
                    "organic": [
                        {
                            "title": "Harbour Public Page",
                            "link": "https://example.com/stores",
                            "snippet": "A public web page.",
                        },
                        {
                            "title": "Local",
                            "link": "http://127.0.0.1/secret",
                            "snippet": "must not be stored",
                        },
                    ]
                }
            ).encode()

        def __enter__(self) -> FakeResponse:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "ngreen_api.research_search.urllib.request.urlopen", lambda *_a, **_k: FakeResponse()
    )
    monkeypatch.setattr("ngreen_api.research_jobs.provider_for", research_search.provider_for)
    live = _run(client, owner, max_queries=1, limit_companies=5, geography="Hyderabad")
    assert live.status_code == 201, live.text
    body = live.json()
    assert body["mode"] == "live"
    assert body["status"] == "completed"
    assert len(body["candidates"]) == 1
    source = body["candidates"][0]["sources"][0]
    assert source["canonical_url"] == "https://example.com/stores"
    assert source["snippet"] == "A public web page."
    assert "127.0.0.1" not in json.dumps(body)
