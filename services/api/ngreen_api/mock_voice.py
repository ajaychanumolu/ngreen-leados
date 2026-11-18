"""DEMO call transcripts. This module never opens a network connection."""

from __future__ import annotations

from ngreen_contracts.call_insight import CallInsight, RequirementMention
from ngreen_contracts.enums import CallOutcome, DecisionMaker, InterestLevel, SpokenLanguage
from ngreen_contracts.taxonomy import PRODUCT_HEADINGS

DEMO_SCRIPT_NAME = "DEMO buyer introduction"
DEMO_SCRIPT_BODY = (
    "DEMO rehearsal only. N Green makes sustainable packaging for businesses that buy bags. "
    "Ask which product they use and whether they want a sample. "
    "Do not claim a number was dialed."
)


def parse_transcript(transcript: str) -> CallInsight:
    spoken = transcript.split("Buyer:", 1)[1] if "Buyer:" in transcript else transcript
    text = " ".join(spoken.split())
    low = text.casefold()
    requirements = [
        RequirementMention(product=product, raw_phrase=product, evidence_span=product)
        for product in PRODUCT_HEADINGS
        if product.casefold() in low
    ]
    meeting = "meeting" in low
    sample = "sample" in low
    if any(mark in low for mark in ("never contact", "do not call", "don't call", "stop calling")):
        outcome = CallOutcome.DO_NOT_CALL
        interest = InterestLevel.LOW
        meeting = False
        action = "Honor the opt-out. Do not call again."
    elif "wrong number" in low:
        outcome = CallOutcome.WRONG_NUMBER
        interest = InterestLevel.UNKNOWN
        action = "Correct the number before any other attempt."
    elif any(
        mark in low for mark in ("no answer", "did not answer", "did not lift", "didn't lift")
    ):
        outcome = CallOutcome.NO_ANSWER
        interest = InterestLevel.UNKNOWN
        action = "Try again only if permission is still valid."
    elif "not interested" in low:
        outcome = CallOutcome.NOT_INTERESTED
        interest = InterestLevel.LOW
        action = "Leave the account in nurture. Do not push a sample."
    elif meeting:
        outcome = CallOutcome.MEETING_REQUESTED
        interest = InterestLevel.HIGH
        action = "Book the meeting the buyer asked for."
    elif any(mark in low for mark in ("call me back", "call back", "callback")):
        outcome = CallOutcome.FOLLOW_UP
        interest = InterestLevel.MEDIUM
        action = "Call back only after a person accepts this note."
    elif "interested" in low:
        outcome = CallOutcome.INTERESTED
        interest = InterestLevel.HIGH if sample else InterestLevel.MEDIUM
        action = "Prepare a sample." if sample else "Follow up on the stated interest."
    else:
        outcome = CallOutcome.NEEDS_REVIEW
        interest = InterestLevel.UNKNOWN
        action = "A person needs to read this transcript."
    timeline = "next week" if "next week" in low else None
    return CallInsight(
        outcome=outcome,
        spoken_language=SpokenLanguage.EN,
        spoke_to_decision_maker=DecisionMaker.UNKNOWN,
        requirements=requirements,
        interest_level=interest,
        timeline=timeline,
        objections=[],
        meeting_requested=meeting and outcome is CallOutcome.MEETING_REQUESTED,
        callback_requested_at=None,
        summary=text[:2000] or "Empty DEMO transcript.",
        next_action=action,
        needs_human_review=True,
        do_not_call=outcome is CallOutcome.DO_NOT_CALL,
        confidence=0.4,
    )
