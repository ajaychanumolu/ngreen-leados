"""Shared enumerations. Values are stable contract strings."""

from __future__ import annotations

from enum import StrEnum


class StaffRole(StrEnum):
    OWNER_ADMIN = "owner_admin"
    RESEARCHER = "researcher"
    SALES_EXECUTIVE = "sales_executive"
    MANAGER = "manager"
    READ_ONLY = "read_only"


class NeedStatus(StrEnum):
    HYPOTHESIS = "hypothesis"
    PUBLICLY_EVIDENCED = "publicly_evidenced"
    BUYER_CONFIRMED = "buyer_confirmed"
    REJECTED = "rejected"


class ClaimStatus(StrEnum):
    SUPPORTED = "supported"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    CONTRADICTED = "contradicted"


class CategoryAssignment(StrEnum):
    MANUAL = "manual"
    INFERRED = "inferred"
    SOURCE_VERIFIED = "source_verified"


class SourceOrigin(StrEnum):
    REFERENCE_SHEET = "reference_sheet"
    WEB_RESEARCH = "web_research"
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


class OpportunityStage(StrEnum):
    RESEARCH = "research"
    VALIDATED_ACCOUNT = "validated_account"
    OUTREACH_ELIGIBLE = "outreach_eligible"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    MEETING_SCHEDULED = "meeting_scheduled"
    SAMPLE_TRIAL_REQUESTED = "sample_trial_requested"
    QUOTATION_SENT = "quotation_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    NURTURE = "nurture"


class CallOutcome(StrEnum):
    INTERESTED = "interested"
    MEETING_REQUESTED = "meeting_requested"
    FOLLOW_UP = "follow_up"
    NOT_INTERESTED = "not_interested"
    NO_ANSWER = "no_answer"
    WRONG_NUMBER = "wrong_number"
    DO_NOT_CALL = "do_not_call"
    NEEDS_REVIEW = "needs_review"


class SpokenLanguage(StrEnum):
    EN = "en"
    HI = "hi"
    TE = "te"
    OTHER = "other"
    UNKNOWN = "unknown"


class DecisionMaker(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class InterestLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class PermissionBasis(StrEnum):
    """Legal/telecom basis for automated promotional voice contact.

    A public listing is not a basis. Unknown permission means do not call.
    """

    UNKNOWN = "unknown"
    RECORDED_CONSENT = "recorded_consent"
    EXISTING_BUSINESS_RELATIONSHIP = "existing_business_relationship"
