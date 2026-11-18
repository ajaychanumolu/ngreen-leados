"""Shared API test client. DEMO staff and a fresh SQLite file per test."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from ngreen_api.db import reset_engine
from ngreen_api.main import app
from ngreen_api.research_jobs import reset_research_limits
from ngreen_api.security import reset_login_limits
from ngreen_api.settings import get_settings


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("LOCAL_JWT_SECRET", "test-secret")
    monkeypatch.setenv("DEMO_AUTH_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SERPER_API_KEY", "")
    monkeypatch.setenv("RESEARCH_WORKER", "sync")
    monkeypatch.setenv("RESEARCH_BUDGET_CREDITS", "5")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_API_KEY", "")
    monkeypatch.setenv("VOICE_LIVE_ENABLED", "false")
    monkeypatch.setenv("VOICE_LEGAL_APPROVED", "false")
    monkeypatch.setenv("VAPI_API_KEY", "")
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "")
    monkeypatch.setenv("VAPI_PHONE_NUMBER_ID", "")
    monkeypatch.setenv("VOICE_TEST_CONTACT_ID", "")
    get_settings.cache_clear()
    reset_engine()
    reset_login_limits()
    reset_research_limits()
    with TestClient(app) as test_client:
        yield test_client
    reset_engine()
    get_settings.cache_clear()
    reset_login_limits()
    reset_research_limits()


def login(client: TestClient, email: str, password: str = "demo-pass") -> str:
    response = client.post(
        "/api/v1/auth/demo/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["auth_mode"] == "demo"
    return str(body["access_token"])


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
