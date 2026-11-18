"""Phase 0 data contracts for N Green LeadOS."""

from ngreen_contracts.call_insight import (
    CallInsight,
    RequirementMention,
    call_event_idempotency_key,
    insight_can_auto_mark_won,
)
from ngreen_contracts.eligibility import LiveCallDecision, evaluate_live_call
from ngreen_contracts.enums import (
    CallOutcome,
    NeedStatus,
    PermissionBasis,
    SourceOrigin,
    StaffRole,
)
from ngreen_contracts.fit_score import FitScore, unscored
from ngreen_contracts.reference import ReferenceCatalog, ReferenceTarget, load_reference_catalog
from ngreen_contracts.taxonomy import (
    CANONICAL_INDUSTRIES,
    PRODUCT_HEADINGS,
    normalize_company_name,
)

__all__ = [
    "CANONICAL_INDUSTRIES",
    "CallInsight",
    "CallOutcome",
    "FitScore",
    "LiveCallDecision",
    "NeedStatus",
    "PermissionBasis",
    "PRODUCT_HEADINGS",
    "ReferenceCatalog",
    "ReferenceTarget",
    "RequirementMention",
    "SourceOrigin",
    "StaffRole",
    "call_event_idempotency_key",
    "evaluate_live_call",
    "insight_can_auto_mark_won",
    "load_reference_catalog",
    "normalize_company_name",
    "unscored",
]
