"""Login, authorization, and the account shell."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from support import auth as _auth
from support import login as _login

from ngreen_api.db import get_session_factory
from ngreen_api.models import Membership, Organization, User
from ngreen_api.security import hash_password
from ngreen_contracts.enums import StaffRole


def test_health_is_public(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["auth_mode"] == "demo"
    assert body["database"] == "sqlite"


def test_me_and_accounts_reject_missing_and_bad_tokens(client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401
    assert client.get("/api/v1/accounts").status_code == 401
    assert client.post("/api/v1/accounts", json={"display_name": "Acme"}).status_code == 401
    forged = client.get("/api/v1/me", headers=_auth("not-a-token"))
    assert forged.status_code == 401
    assert forged.json()["code"] == "not_authenticated"


def test_wrong_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/demo/login",
        json={"email": "owner@ngreen.demo", "password": "nope"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


def test_owner_can_create_and_reader_cannot(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    reader = _login(client, "reader@ngreen.demo")
    me = client.get("/api/v1/me", headers=_auth(owner))
    assert me.status_code == 200
    assert me.json()["role"] == StaffRole.OWNER_ADMIN.value
    assert me.json()["organization_name"] == "N Green"

    denied = client.post(
        "/api/v1/accounts",
        headers=_auth(reader),
        json={"display_name": "Blocked Co"},
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "forbidden"

    created = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={"display_name": "  Harbour Paper  ", "city": "Hyderabad", "state": "Telangana"},
    )
    assert created.status_code == 201, created.text
    account = created.json()
    assert account["normalized_name"] == "harbour paper"
    assert account["source_origin"] == "manual"
    assert account["review_status"] == "pending"
    assert account["country"] == "India"

    listing = client.get("/api/v1/accounts?page_size=100", headers=_auth(reader))
    assert listing.status_code == 200
    assert listing.json()["total"] == 21
    fetched = client.get(f"/api/v1/accounts/{account['id']}", headers=_auth(reader))
    assert fetched.status_code == 200

    overview = client.get("/api/v1/overview", headers=_auth(reader))
    assert overview.status_code == 200
    body = overview.json()
    assert body["accounts"] == 21
    assert body["reference_targets"] == 20
    assert body["manual_contacts"] == 0
    assert body["accounts_source"] == "database"
    assert "won_orders" in body["unavailable"]

    duplicate = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={"display_name": "harbour paper"},
    )
    assert duplicate.status_code == 409


def test_patch_and_other_organization_cannot_read(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    created = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={"display_name": "Coastal Stores", "notes": "Manual note"},
    )
    account_id = created.json()["id"]
    patched = client.patch(
        f"/api/v1/accounts/{account_id}",
        headers=_auth(owner),
        json={"display_name": "Coastal Stores", "city": "Pune", "notes": "Updated note"},
    )
    assert patched.status_code == 200
    assert patched.json()["city"] == "Pune"
    assert patched.json()["notes"] == "Updated note"

    db = get_session_factory()()
    try:
        other = Organization(name="Other", slug="other")
        db.add(other)
        db.flush()
        outsider = User(
            email="outsider@example.demo",
            display_name="Outsider",
            password_hash=hash_password("demo-pass"),
        )
        db.add(outsider)
        db.flush()
        db.add(
            Membership(
                organization_id=other.id,
                user_id=outsider.id,
                role=StaffRole.OWNER_ADMIN.value,
            )
        )
        db.commit()
    finally:
        db.close()

    token = _login(client, "outsider@example.demo")
    hidden = client.get(f"/api/v1/accounts/{account_id}", headers=_auth(token))
    assert hidden.status_code == 404
    own_list = client.get("/api/v1/accounts", headers=_auth(token))
    assert own_list.json()["total"] == 0
    own_overview = client.get("/api/v1/overview", headers=_auth(token))
    assert own_overview.json()["accounts"] == 0


def test_login_rate_limit(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import ngreen_api.routers.auth as auth_router

    monkeypatch.setattr(auth_router, "login_is_limited", lambda _key: True)
    response = client.post(
        "/api/v1/auth/demo/login",
        json={"email": "owner@ngreen.demo", "password": "demo-pass"},
    )
    assert response.status_code == 429


def test_migration_creates_tables(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from alembic.config import Config

    from alembic import command

    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    config = Config("services/api/alembic.ini")
    config.set_main_option("script_location", "services/api/alembic")
    command.upgrade(config, "head")
    from sqlalchemy import create_engine, inspect

    names = set(inspect(create_engine(url)).get_table_names())
    assert {
        "organizations",
        "users",
        "memberships",
        "companies",
        "audit_events",
        "products",
        "industries",
        "industry_aliases",
        "company_product_needs",
        "contacts",
        "crm_opportunities",
        "tasks",
        "imports",
        "research_runs",
        "research_queries",
        "research_candidates",
        "sources",
        "usage_events",
        "research_assessments",
        "evidence_claims",
        "contact_permissions",
        "suppressions",
        "call_scripts",
        "simulated_calls",
        "call_events",
    } <= names
