"""Runtime settings. Secrets come from the environment, never from the client."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    database_url: str
    jwt_secret: str
    demo_auth_enabled: bool
    supabase_url: str
    cors_origins: list[str]
    serper_api_key: str
    research_worker: str
    research_budget_credits: int
    redis_url: str
    ai_provider: str
    ai_api_key: str
    ai_model: str
    voice_live_enabled: bool
    voice_legal_approved: bool
    voice_webhook_secret: str
    vapi_api_key: str
    vapi_assistant_id: str
    vapi_phone_number_id: str
    voice_test_contact_id: str
    voice_daily_cap: int
    voice_concurrent_cap: int

    @property
    def database_kind(self) -> str:
        if self.database_url.startswith("postgresql"):
            return "postgresql"
        if self.database_url.startswith("sqlite"):
            return "sqlite"
        return "other"

    @property
    def auth_mode(self) -> str:
        if self.supabase_url:
            return "supabase"
        return "demo"


def _load_env_file() -> None:
    """Fill empty process variables from the repo .env. Existing variables win."""
    path = Path(__file__).resolve().parents[3] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def _database_url() -> str:
    """Use the Supabase Postgres URI when it is set. Otherwise keep the local file."""
    supabase_db = os.environ.get("SUPABASE_DB_URL", "").strip()
    if supabase_db.startswith("postgres"):
        return supabase_db
    return os.environ.get("DATABASE_URL", "sqlite:///./data/local-leados.db")


@lru_cache
def get_settings() -> Settings:
    _load_env_file()
    origins = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return Settings(
        database_url=_database_url(),
        jwt_secret=os.environ.get("LOCAL_JWT_SECRET", "local-dev-only-change-me"),
        demo_auth_enabled=os.environ.get("DEMO_AUTH_ENABLED", "true").lower() == "true",
        supabase_url=os.environ.get("SUPABASE_URL", "").rstrip("/"),
        cors_origins=[item.strip() for item in origins.split(",") if item.strip()],
        serper_api_key=os.environ.get("SERPER_API_KEY", "").strip(),
        research_worker=os.environ.get("RESEARCH_WORKER", "inline"),
        research_budget_credits=int(os.environ.get("RESEARCH_BUDGET_CREDITS", "5")),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        ai_provider=os.environ.get("AI_PROVIDER", "mock").strip().lower() or "mock",
        ai_api_key=os.environ.get("AI_API_KEY", "").strip(),
        ai_model=os.environ.get("AI_MODEL", "").strip(),
        voice_live_enabled=os.environ.get("VOICE_LIVE_ENABLED", "false").lower() == "true",
        voice_legal_approved=os.environ.get("VOICE_LEGAL_APPROVED", "false").lower() == "true",
        voice_webhook_secret=os.environ.get("VOICE_WEBHOOK_SECRET", "").strip(),
        vapi_api_key=os.environ.get("VAPI_API_KEY", "").strip(),
        vapi_assistant_id=os.environ.get("VAPI_ASSISTANT_ID", "").strip(),
        vapi_phone_number_id=os.environ.get("VAPI_PHONE_NUMBER_ID", "").strip(),
        voice_test_contact_id=os.environ.get("VOICE_TEST_CONTACT_ID", "").strip(),
        voice_daily_cap=int(os.environ.get("VOICE_DAILY_CAP", "1")),
        voice_concurrent_cap=int(os.environ.get("VOICE_CONCURRENT_CAP", "1")),
    )
