"""Contract rules that later phases must keep."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from ngreen_contracts.api_shapes import ApiErrorBody, Page
from ngreen_contracts.call_insight import (
    CallInsight,
    RequirementMention,
    call_event_idempotency_key,
    insight_can_auto_mark_won,
)
from ngreen_contracts.eligibility import evaluate_live_call
from ngreen_contracts.enums import (
    CallOutcome,
    DecisionMaker,
    InterestLevel,
    PermissionBasis,
    SpokenLanguage,
    StaffRole,
)
from ngreen_contracts.fit_score import FitScoreBreakdown, unscored

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
FIXTURE_E164 = "+910000000000"


def _insight(**overrides: object) -> CallInsight:
    payload: dict[str, object] = {
        "outcome": CallOutcome.INTERESTED,
        "spoken_language": SpokenLanguage.EN,
        "spoke_to_decision_maker": DecisionMaker.UNKNOWN,
        "requirements": [
            {
                "product": "Courier Bags",
                "raw_phrase": "courier bags",
                "quantity": None,
                "unit": None,
                "material_spec": None,
                "evidence_span": "interested in courier bags",
            }
        ],
        "interest_level": InterestLevel.MEDIUM,
        "timeline": None,
        "objections": [],
        "meeting_requested": False,
        "callback_requested_at": None,
        "summary": "Caller asked about courier bags.",
        "next_action": "Staff reviews the note before any CRM change.",
        "needs_human_review": True,
        "do_not_call": False,
        "confidence": 0.4,
    }
    payload.update(overrides)
    return CallInsight.model_validate(payload)


def _decision(**overrides: object):
    payload = {
        "voice_live_enabled": True,
        "actor_role": StaffRole.SALES_EXECUTIVE,
        "destination_e164": FIXTURE_E164,
        "permission_basis": PermissionBasis.RECORDED_CONSENT,
        "do_not_call": False,
        "permission_revoked": False,
        "suppressed": False,
        "expires_at": NOW + timedelta(days=30),
        "now": NOW,
    }
    payload.update(overrides)
    return evaluate_live_call(**payload)


def test_unknown_permission_blocks_a_live_call() -> None:
    decision = _decision(permission_basis=PermissionBasis.UNKNOWN)
    assert decision.allowed is False
    assert "permission basis is unknown" in decision.reasons


def test_live_flag_off_blocks_even_with_consent() -> None:
    decision = _decision(voice_live_enabled=False)
    assert decision.allowed is False
    assert "live voice provider is disabled" in decision.reasons


def test_read_only_and_researcher_cannot_authorize_a_live_call() -> None:
    for role in (StaffRole.READ_ONLY, StaffRole.RESEARCHER):
        decision = _decision(actor_role=role)
        assert decision.allowed is False


def test_opt_out_suppression_and_expiry_block() -> None:
    assert _decision(do_not_call=True).allowed is False
    assert _decision(suppressed=True).allowed is False
    assert _decision(permission_revoked=True).allowed is False
    expired = _decision(expires_at=NOW - timedelta(minutes=1))
    assert expired.allowed is False
    assert "permission has expired" in expired.reasons


def test_all_gates_open_is_allowed_and_still_not_a_phone_call() -> None:
    decision = _decision()
    assert decision.allowed is True
    assert decision.reasons == ()


def test_naive_datetimes_are_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        _decision(expires_at=datetime(2026, 11, 18, 12, 0))


def test_call_insight_rejects_unknown_fields_and_unmapped_products() -> None:
    with pytest.raises(ValidationError):
        _insight(invented_plastic_use=True)
    with pytest.raises(ValidationError):
        RequirementMention(
            product="Compostable mystery film",
            raw_phrase="compostable mystery film",
            evidence_span="we use compostable mystery film",
        )


def test_unmapped_product_phrase_is_kept() -> None:
    item = RequirementMention(
        product="unmapped: bio liner",
        raw_phrase="bio liner",
        evidence_span="we buy bio liner",
    )
    assert item.product.startswith("unmapped:")


def test_insight_cannot_auto_mark_won() -> None:
    insight = _insight(outcome=CallOutcome.MEETING_REQUESTED, meeting_requested=True)
    assert insight_can_auto_mark_won(insight) is False


def test_duplicate_provider_event_has_one_key() -> None:
    first = call_event_idempotency_key("call-fixture-1", "event-fixture-1")
    second = call_event_idempotency_key("call-fixture-1", "event-fixture-1")
    assert first == second
    with pytest.raises(ValueError):
        call_event_idempotency_key("  ", "event-fixture-1")


def test_missing_evidence_scores_zero() -> None:
    score = unscored("no source attached")
    assert score.total == 0
    assert "conversion probability" in score.label


def test_fit_components_cap_at_100() -> None:
    perfect = FitScoreBreakdown(
        industry_alignment=25,
        product_fit=25,
        operational_scale=15,
        geography_supply=10,
        buyer_relevant_evidence=20,
        source_freshness=5,
    )
    assert perfect.total == 100
    with pytest.raises(ValidationError):
        FitScoreBreakdown(
            industry_alignment=25,
            product_fit=25,
            operational_scale=15,
            geography_supply=10,
            buyer_relevant_evidence=21,
            source_freshness=5,
        )


def test_callback_timestamp_must_be_utc() -> None:
    with pytest.raises(ValidationError):
        _insight(callback_requested_at="2026-11-18T09:00:00+05:30")
    ok = _insight(callback_requested_at="2026-11-18T03:30:00Z")
    assert ok.callback_requested_at is not None


def test_page_and_error_shapes() -> None:
    page = Page[str](items=["a"], page=1, page_size=25, total=1)
    assert page.total == 1
    with pytest.raises(ValidationError):
        Page[str](items=[], page=0, page_size=25, total=0)
    error = ApiErrorBody(code="not_authenticated", message="Sign in required.")
    assert error.code == "not_authenticated"
