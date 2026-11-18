"""Database engine and session. Postgres in Docker, SQLite when Docker is absent."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ngreen_api.settings import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def prepare_database() -> Engine:
    """Create tables. SQLite also fills columns added after the first local file."""
    engine = get_engine()
    from ngreen_api.models import Company  # noqa: F401

    Base.metadata.create_all(engine)
    if get_settings().database_url.startswith("sqlite"):
        _add_missing_company_columns(engine)
        _add_missing_research_columns(engine)
        _add_missing_contact_columns(engine)
    return engine


def _add_missing_company_columns(engine: Engine) -> None:
    from sqlalchemy import inspect, text

    columns = {column["name"] for column in inspect(engine).get_columns("companies")}
    statements = {
        "review_label": "ALTER TABLE companies ADD COLUMN review_label VARCHAR(80)",
        "owner_user_id": "ALTER TABLE companies ADD COLUMN owner_user_id CHAR(32)",
        "industry_id": "ALTER TABLE companies ADD COLUMN industry_id CHAR(32)",
        "industry_assignment": "ALTER TABLE companies ADD COLUMN industry_assignment VARCHAR(40)",
        "canonical_domain": "ALTER TABLE companies ADD COLUMN canonical_domain VARCHAR(200)",
        "business_unit": "ALTER TABLE companies ADD COLUMN business_unit VARCHAR(120) DEFAULT ''",
    }
    missing = [sql for name, sql in statements.items() if name not in columns]
    if not missing:
        return
    with engine.begin() as connection:
        for sql in missing:
            connection.execute(text(sql))


def _add_missing_research_columns(engine: Engine) -> None:
    from sqlalchemy import inspect, text

    tables = set(inspect(engine).get_table_names())
    if "research_queries" not in tables:
        return
    columns = {column["name"] for column in inspect(engine).get_columns("research_queries")}
    missing = []
    if "known_skipped" not in columns:
        missing.append(
            "ALTER TABLE research_queries ADD COLUMN known_skipped INTEGER NOT NULL DEFAULT 0"
        )
    if "seller_skipped" not in columns:
        missing.append(
            "ALTER TABLE research_queries ADD COLUMN seller_skipped INTEGER NOT NULL DEFAULT 0"
        )
    if not missing:
        return
    with engine.begin() as connection:
        for sql in missing:
            connection.execute(text(sql))


def _add_missing_contact_columns(engine: Engine) -> None:
    from sqlalchemy import inspect, text

    tables = set(inspect(engine).get_table_names())
    if "contacts" not in tables:
        return
    columns = {column["name"] for column in inspect(engine).get_columns("contacts")}
    statements = {
        "source_url": "ALTER TABLE contacts ADD COLUMN source_url VARCHAR(500)",
        "checked_at": "ALTER TABLE contacts ADD COLUMN checked_at DATETIME",
        "owner_user_id": "ALTER TABLE contacts ADD COLUMN owner_user_id CHAR(32)",
        "validity": "ALTER TABLE contacts ADD COLUMN validity VARCHAR(40) DEFAULT 'unverified'",
        "permission_expires_at": "ALTER TABLE contacts ADD COLUMN permission_expires_at DATETIME",
        "permission_revoked": (
            "ALTER TABLE contacts ADD COLUMN permission_revoked BOOLEAN NOT NULL DEFAULT 0"
        ),
        "do_not_call": "ALTER TABLE contacts ADD COLUMN do_not_call BOOLEAN NOT NULL DEFAULT 0",
        "channel_scope": "ALTER TABLE contacts ADD COLUMN channel_scope VARCHAR(20) DEFAULT 'none'",
    }
    missing = [sql for name, sql in statements.items() if name not in columns]
    if not missing:
        return
    with engine.begin() as connection:
        for sql in missing:
            connection.execute(text(sql))


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        url = get_settings().database_url
        connect_args = (
            {"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}
        )
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def get_db() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def reset_engine() -> None:
    """Drop the cached engine. Tests call this after changing DATABASE_URL."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
