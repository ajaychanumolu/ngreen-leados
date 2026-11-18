"""Follow-ups, funnel counts, and spend. Counts come from stored rows."""

from __future__ import annotations

import uuid
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from support import auth as _auth
from support import login as _login

from ngreen_api.clock import india_today
from ngreen_api.db import get_session_factory
from ngreen_api.models import (
    Organization,
    Product,
    ResearchAssessment,
    ResearchCandidate,
    ResearchQuery,
    ResearchRun,
    UsageEvent,
    User,
)


def test_funnel_is_stored_counts_and_sales_cannot_read(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    reader = _login(client, "reader@ngreen.demo")
    manager = _login(client, "manager@ngreen.demo")
    sales = _login(client, "sales@ngreen.demo")
    researcher = _login(client, "researcher@ngreen.demo")

    report = client.get("/api/v1/reports/funnel", headers=_auth(owner))
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["source"] == "database"
    assert body["credits_per_stored_candidate"] is None
    assert body["credits_per_approved_candidate"] is None
    assert body["average_fit"] is None
    assert body["candidates_stored"] == 0
    assert "not revenue" in " ".join(body["notes"])
    assert "value_inr" not in body
    overview = client.get("/api/v1/overview", headers=_auth(owner))
    research = next(item for item in body["stages"] if item["stage"] == "research")
    assert research["count"] == overview.json()["opportunities"]
    assert research["oldest_days"] == 0
    assert client.get("/api/v1/reports/funnel", headers=_auth(reader)).status_code == 200
    assert client.get("/api/v1/reports/funnel", headers=_auth(manager)).status_code == 200
    denied = client.get("/api/v1/reports/funnel", headers=_auth(sales))
    assert denied.status_code == 403
    assert client.get("/api/v1/reports/funnel", headers=_auth(researcher)).status_code == 403

    exported = client.get("/api/v1/reports/export", headers=_auth(owner))
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert "not revenue" in exported.text
    assert "search_credits" in exported.text
    spend = client.get("/api/v1/reports/spend", headers=_auth(owner))
    assert spend.status_code == 200
    assert spend.json()["total"] == 0
    assert client.get("/api/v1/reports/export", headers=_auth(sales)).status_code == 403


def test_overdue_follow_up_and_credit_ratios(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    reader = _login(client, "reader@ngreen.demo")
    team = client.get("/api/v1/team", headers=_auth(owner))
    assert team.status_code == 200
    sales_id = next(item["user_id"] for item in team.json() if item["role"] == "sales_executive")
    yesterday = (india_today() - timedelta(days=1)).isoformat()
    tomorrow = (india_today() + timedelta(days=1)).isoformat()

    created = client.post(
        "/api/v1/tasks",
        headers=_auth(owner),
        json={"title": "Call back the buyer", "due_on": yesterday, "owner_user_id": sales_id},
    )
    assert created.status_code == 201, created.text
    assert created.json()["overdue"] is True
    assert created.json()["owner_user_id"] == sales_id
    later = client.post(
        "/api/v1/tasks",
        headers=_auth(owner),
        json={"title": "Send the sample note", "due_on": tomorrow},
    )
    assert later.json()["overdue"] is False
    overdue = client.get("/api/v1/tasks?overdue=true", headers=_auth(owner))
    titles = [item["title"] for item in overdue.json()["items"]]
    assert titles == ["Call back the buyer"]
    stranger = client.patch(
        f"/api/v1/tasks/{created.json()['id']}",
        headers=_auth(owner),
        json={"owner_user_id": str(uuid.uuid4())},
    )
    assert stranger.status_code == 422
    blocked = client.patch(
        f"/api/v1/tasks/{created.json()['id']}",
        headers=_auth(reader),
        json={"status": "done"},
    )
    assert blocked.status_code == 403
    done = client.patch(
        f"/api/v1/tasks/{created.json()['id']}",
        headers=_auth(owner),
        json={"status": "done"},
    )
    assert done.json()["overdue"] is False
    cleared = client.get("/api/v1/tasks?overdue=true", headers=_auth(owner))
    assert cleared.json()["total"] == 0

    _seed_usage(client)
    report = client.get("/api/v1/reports/funnel", headers=_auth(owner)).json()
    assert report["candidates_stored"] == 2
    assert report["candidates_approved"] == 1
    assert report["search_credits"] == 2
    assert report["credits_per_stored_candidate"] == 1.0
    assert report["credits_per_approved_candidate"] == 2.0
    assert report["average_fit"] == 5.0
    assert report["zero_fit"] == 1
    assert report["live_attempts"] == 0
    kinds = {item["kind"] for item in report["alerts"]}
    assert "research_failed" in kinds
    assert "query_error" in kinds
    assert report["retry_queue"][0]["status"] == "failed"
    assert report["retry_queue"][0]["spent_credits"] == 1
    assert report["recent_spend"][0]["kind"] == "search"
    assert report["recent_spend"][0]["units"] == 2


def _seed_usage(_client: TestClient) -> None:
    db = get_session_factory()()
    try:
        org = db.scalar(select(Organization).where(Organization.slug == "ngreen"))
        user = db.scalar(select(User).where(User.email == "owner@ngreen.demo"))
        product = db.scalar(select(Product).where(Product.organization_id == org.id))
        assert org is not None and user is not None and product is not None
        run = ResearchRun(
            organization_id=org.id,
            actor_user_id=user.id,
            product_id=product.id,
            geography="Hyderabad",
            limit_companies=2,
            max_queries=1,
            max_results_per_query=5,
            budget_credits=5,
            spent_credits=1,
            status="failed",
            mode="demo",
            worker="sync",
            error_summary="Provider outage",
        )
        db.add(run)
        db.flush()
        db.add(
            ResearchQuery(
                organization_id=org.id,
                run_id=run.id,
                position=1,
                query_text="hotel sustainable packaging",
                status="error",
                error="Provider outage",
            )
        )
        approved = ResearchCandidate(
            organization_id=org.id,
            run_id=run.id,
            display_name="Example Depot",
            normalized_name="example depot",
            identity_key="demo:example depot",
            status="approved",
        )
        pending = ResearchCandidate(
            organization_id=org.id,
            run_id=run.id,
            display_name="Example Market",
            normalized_name="example market",
            identity_key="demo:example market",
            status="pending",
        )
        db.add(approved)
        db.add(pending)
        db.flush()
        for candidate, score in ((approved, 10), (pending, 0)):
            db.add(
                ResearchAssessment(
                    organization_id=org.id,
                    candidate_id=candidate.id,
                    provider="mock",
                    model_name="mock",
                    prompt_version="v1",
                    fit_total=score,
                    reasons_json="[]",
                    industry_alignment=0,
                    product_fit=0,
                    operational_scale=0,
                    geography_supply=0,
                    buyer_relevant_evidence=0,
                    source_freshness=0,
                )
            )
        db.add(
            UsageEvent(
                organization_id=org.id,
                run_id=run.id,
                kind="search",
                units=2,
                mode="demo",
            )
        )
        db.commit()
    finally:
        db.close()
