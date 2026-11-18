"""Planning files that Phase 0 must leave in the repo."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_env_example_keeps_live_calling_off_and_has_no_secrets() -> None:
    text = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "VOICE_LIVE_ENABLED=false" in text
    assert "SERPER_API_KEY=" in text
    assert "sk-" not in text
    for line in text.splitlines():
        if line.startswith("SERPER_API_KEY=") or line.startswith("VAPI_API_KEY="):
            assert line.endswith("=")


def test_wireframe_is_labeled_and_lists_required_routes() -> None:
    html = (ROOT / "docs" / "wireframes" / "index.html").read_text(encoding="utf-8")
    lowered = html.lower()
    assert "not the application" in lowered
    assert "Reference target – not verified" in html
    for route in (
        "/login",
        "/overview",
        "/research",
        "/accounts",
        "/imports",
        "/contacts",
        "/calling",
        "/crm",
        "/tasks",
        "/reports",
        "/settings",
    ):
        assert route in html
    assert "DEMO" in html


def test_phase_docs_exist() -> None:
    required = [
        "docs/PRD.md",
        "docs/ARCHITECTURE.md",
        "docs/ERD.md",
        "docs/SECURITY_AND_COMPLIANCE.md",
        "docs/DECISIONS.md",
        "docs/PHASE_PLAN.md",
        "docs/PROGRESS.md",
        "docs/SCREEN_MAP.md",
        "docs/API_CONTRACT.md",
        "README.md",
    ]
    for relative in required:
        path = ROOT / relative
        assert path.is_file(), relative
        assert path.stat().st_size > 200
