"""Structured end-of-call result. A model instance is not a CRM update."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ngreen_contracts.enums import (
    CallOutcome,
    DecisionMaker,
    InterestLevel,
    SpokenLanguage,
)
from ngreen_contracts.taxonomy import PRODUCT_HEADINGS


class RequirementMention(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product: str
    raw_phrase: str = Field(min_length=1)
    quantity: float | None = None
    unit: str | None = None
    material_spec: str | None = None
    evidence_span: str = Field(min_length=1)

    @field_validator("product")
    @classmethod
    def product_must_be_in_taxonomy_or_unmapped(cls, value: str) -> str:
        if value not in PRODUCT_HEADINGS and not value.startswith("unmapped:"):
            raise ValueError(
                "product must be a taxonomy heading or an unmapped: raw phrase"
            )
        return value


class CallInsight(BaseModel):
    """Validated assistant extraction. Human review stays required for CRM writes."""

    model_config = ConfigDict(extra="forbid")

    outcome: CallOutcome
    spoken_language: SpokenLanguage
    spoke_to_decision_maker: DecisionMaker
    requirements: list[RequirementMention]
    interest_level: InterestLevel
    timeline: str | None = None
    objections: list[str]
    meeting_requested: bool
    callback_requested_at: str | None = None
    summary: str = Field(min_length=1, max_length=2000)
    next_action: str = Field(min_length=1, max_length=500)
    needs_human_review: bool
    do_not_call: bool
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("callback_requested_at")
    @classmethod
    def callback_is_not_a_free_form_claim(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.endswith("Z"):
            raise ValueError("callback_requested_at must be an ISO-8601 UTC timestamp")
        return value


def insight_can_auto_mark_won(insight: CallInsight) -> bool:
    """Call extraction never closes an order. The argument is accepted so callers
    cannot bypass the rule by forgetting to consult it.
    """
    del insight
    return False


def call_event_idempotency_key(provider_call_id: str, provider_event_id: str) -> str:
    call_id = provider_call_id.strip()
    event_id = provider_event_id.strip()
    if not call_id or not event_id:
        raise ValueError("provider call id and event id are both required")
    return f"{call_id}:{event_id}"
