"""Privacy erasure, backup, migration rollback, and request ids."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from support import auth as _auth
from support import login as _login

from alembic import command
from ngreen_api.backup import backup_sqlite, restore_sqlite
from ngreen_api.redact import scrub


def test_scrub_removes_email_and_phone() -> None:
    cleaned = scrub("Reach desk@example.com or +14155552671 today")
    assert "desk@example.com" not in cleaned
    assert "+14155552671" not in cleaned
    assert "[email]" in cleaned
    assert "[phone]" in cleaned


def test_request_id_is_returned(client: TestClient) -> None:
    response = client.get("/health", headers={"X-Request-ID": "phase9-request"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "phase9-request"
    assert "serper" not in response.text.lower()
    assert "vapi" not in response.json()


def test_health_smoke_loop(client: TestClient) -> None:
    for _ in range(20):
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/accounts").status_code == 401


def test_sqlite_backup_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "app.db"
    connection = sqlite3.connect(source)
    connection.execute("create table note(body text)")
    connection.execute("insert into note values ('kept')")
    connection.commit()
    connection.close()
    saved = tmp_path / "app-backup.db"
    backup_sqlite(source, saved)
    connection = sqlite3.connect(source)
    connection.execute("delete from note")
    connection.commit()
    connection.close()
    restore_sqlite(saved, source)
    connection = sqlite3.connect(source)
    assert connection.execute("select body from note").fetchone()[0] == "kept"
    connection.close()


def test_migration_rollback_and_return(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    url = f"sqlite:///{tmp_path / 'migrate.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    config = Config(str(ini))
    config.set_main_option("script_location", str(ini.parent / "alembic"))
    command.upgrade(config, "head")
    command.downgrade(config, "0005_contacts")
    names = set(inspect(create_engine(url)).get_table_names())
    assert "simulated_calls" not in names
    assert "contacts" in names
    command.upgrade(config, "head")
    names = set(inspect(create_engine(url)).get_table_names())
    assert "simulated_calls" in names
    assert "call_events" in names


def test_erase_removes_transcript_and_keeps_suppression(client: TestClient) -> None:
    owner = _login(client, "owner@ngreen.demo")
    manager = _login(client, "manager@ngreen.demo")
    sales = _login(client, "sales@ngreen.demo")
    email = "desk@example.com"
    account = client.post(
        "/api/v1/accounts",
        headers=_auth(owner),
        json={"display_name": "Privacy Fixture"},
    )
    assert account.status_code == 201, account.text
    contact = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": account.json()["id"],
            "display_name": "Desk",
            "email": email,
            "phone": "+14155552671",
            "source_note": "Typed by staff for the erasure test.",
            "permission_basis": "unknown",
        },
    )
    assert contact.status_code == 201, contact.text
    contact_id = contact.json()["id"]
    permitted = client.post(
        f"/api/v1/contacts/{contact_id}/permissions",
        headers=_auth(owner),
        json={
            "basis": "recorded_consent",
            "channel_scope": "phone",
            "proof_note": "Staff recorded consent for this fixture.",
        },
    )
    assert permitted.status_code == 200, permitted.text
    rehearsal = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={"contact_id": contact_id, "transcript": f"Email {email}. Not interested."},
    )
    assert rehearsal.status_code == 201, rehearsal.text
    denied = client.get(f"/api/v1/privacy/contacts/{contact_id}", headers=_auth(sales))
    assert denied.status_code == 403
    exported = client.get(f"/api/v1/privacy/contacts/{contact_id}", headers=_auth(manager))
    assert exported.status_code == 200
    assert exported.json()["email"] == email
    assert email in exported.json()["calls"][0]["transcript"]
    erased = client.post(f"/api/v1/privacy/contacts/{contact_id}/erase", headers=_auth(owner))
    assert erased.status_code == 204
    assert client.get("/api/v1/contacts?page_size=100", headers=_auth(owner)).text.find(email) == -1
    calls = client.get("/api/v1/calls", headers=_auth(owner))
    assert email not in calls.text
    audit = client.get("/api/v1/audit?page_size=100", headers=_auth(owner))
    assert audit.status_code == 200
    summaries = " ".join(item["summary"] for item in audit.json()["items"])
    assert email not in summaries
    assert "+14155552671" not in summaries
    again = client.post(
        "/api/v1/contacts",
        headers=_auth(owner),
        json={
            "company_id": account.json()["id"],
            "display_name": "Desk",
            "email": email,
            "phone": "+14155552671",
            "source_note": "Typed again after erasure.",
            "permission_basis": "recorded_consent",
        },
    )
    assert again.status_code == 201, again.text
    blocked = client.post(
        "/api/v1/calls/simulate",
        headers=_auth(owner),
        json={"contact_id": again.json()["id"], "transcript": "Hello again."},
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "do_not_call"
