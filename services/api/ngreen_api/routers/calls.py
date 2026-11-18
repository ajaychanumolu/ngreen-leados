"""DEMO rehearsals and a live adapter that stays disabled until every gate passes."""

from __future__ import annotations

import hmac
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.contact_research import channel_hash
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_crm
from ngreen_api.mock_voice import DEMO_SCRIPT_BODY, DEMO_SCRIPT_NAME, parse_transcript
from ngreen_api.models import (
    CallEvent,
    CallScript,
    Company,
    Contact,
    Opportunity,
    OpportunityStageEvent,
    SimulatedCall,
    Suppression,
    Task,
)
from ngreen_api.records import audit
from ngreen_api.settings import get_settings
from ngreen_api.voice_provider import VapiVoiceProvider, VoiceRequest, live_blockers
from ngreen_contracts.call_insight import (
    CallInsight,
    call_event_idempotency_key,
    insight_can_auto_mark_won,
)
from ngreen_contracts.eligibility import evaluate_live_call
from ngreen_contracts.enums import CallOutcome, OpportunityStage, PermissionBasis, StaffRole

router = APIRouter(prefix="/api/v1", tags=["calls"])


class StartBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact_id: uuid.UUID | None = None


class StartOut(BaseModel):
    dialed: bool
    provider: str
    call_id: uuid.UUID


@router.post("/calls/start", response_model=StartOut, status_code=201)
def start_live_call(
    body: StartBody,
    actor: Actor = Depends(require_crm),
    db: Session = Depends(get_db),
) -> StartOut:
    if body.contact_id is None:
        raise ApiError(403, "live_disabled", "Live calling is disabled. No number was dialed.")
    contact = _contact(db, actor, body.contact_id)
    settings = get_settings()
    expires_at = contact.permission_expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    decision = evaluate_live_call(
        voice_live_enabled=settings.voice_live_enabled,
        actor_role=StaffRole(actor.role),
        destination_e164=contact.phone,
        permission_basis=PermissionBasis(contact.permission_basis),
        do_not_call=contact.do_not_call,
        permission_revoked=contact.permission_revoked,
        suppressed=_suppressed(db, contact),
        expires_at=expires_at,
        now=datetime.now(UTC),
    )
    now = datetime.now(UTC)
    in_flight = int(
        db.scalar(
            select(func.count())
            .select_from(SimulatedCall)
            .where(
                SimulatedCall.organization_id == actor.organization_id,
                SimulatedCall.mode == "live",
                SimulatedCall.review_status == "pending",
            )
        )
        or 0
    )
    spent_today = int(
        db.scalar(
            select(func.count())
            .select_from(SimulatedCall)
            .where(
                SimulatedCall.organization_id == actor.organization_id,
                SimulatedCall.mode == "live",
                SimulatedCall.created_at >= now - timedelta(days=1),
            )
        )
        or 0
    )
    reasons = live_blockers(
        legal_approved=settings.voice_legal_approved,
        live_enabled=settings.voice_live_enabled,
        test_contact_id=settings.voice_test_contact_id,
        contact_id=str(contact.id),
        phone_number_id=settings.vapi_phone_number_id,
        assistant_id=settings.vapi_assistant_id,
        decision_reasons=list(decision.reasons),
        now=now,
        in_flight=in_flight,
        spent_today=spent_today,
        daily_cap=settings.voice_daily_cap,
        concurrent_cap=settings.voice_concurrent_cap,
    )
    if reasons:
        raise ApiError(403, "live_disabled", f"{reasons[0]} No number was dialed.")
    result = VapiVoiceProvider(settings.vapi_api_key).place(
        VoiceRequest(
            destination_e164=contact.phone or "",
            assistant_id=settings.vapi_assistant_id,
            phone_number_id=settings.vapi_phone_number_id,
        )
    )
    if not result.placed or not result.provider_call_id:
        raise ApiError(502, "provider_outage", f"{result.detail} No number was dialed.")
    insight = parse_transcript("Needs review. The live transcript has not arrived.")
    call = SimulatedCall(
        organization_id=contact.organization_id,
        contact_id=contact.id,
        company_id=contact.company_id,
        actor_user_id=actor.user.id,
        script_id=None,
        provider_call_id=result.provider_call_id,
        transcript="Live call accepted by the provider. The transcript is not in yet.",
        outcome=insight.outcome.value,
        insight_json=insight.model_dump_json(),
        review_status="pending",
        mode="live",
        dialed=True,
    )
    db.add(call)
    db.flush()
    audit(db, actor, "call", result.provider_call_id, "start", "One approved test call was sent.")
    db.commit()
    return StartOut(dialed=True, provider=result.provider, call_id=call.id)


class ScriptOut(BaseModel):
    id: uuid.UUID
    name: str
    body: str
    approved: bool


class SimulateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    contact_id: uuid.UUID
    transcript: str = Field(min_length=8, max_length=2000)
    script_id: uuid.UUID | None = None


class ReviewBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: str


class WebhookBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_call_id: str = Field(min_length=1, max_length=80)
    provider_event_id: str = Field(min_length=1, max_length=80)
    contact_id: uuid.UUID
    transcript: str = Field(min_length=8, max_length=2000)


class CallOut(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    transcript: str
    outcome: str
    summary: str
    next_action: str
    review_status: str
    mode: str
    dialed: bool
    needs_human_review: bool
    do_not_call: bool
    event_count: int


@router.get("/calls/scripts", response_model=list[ScriptOut])
def list_scripts(
    actor: Actor = Depends(get_actor), db: Session = Depends(get_db)
) -> list[ScriptOut]:
    _ensure_script(db, actor)
    db.commit()
    rows = db.scalars(
        select(CallScript)
        .where(CallScript.organization_id == actor.organization_id)
        .order_by(CallScript.created_at)
    ).all()
    return [
        ScriptOut(id=row.id, name=row.name, body=row.body, approved=row.approved) for row in rows
    ]


class ScriptBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=8, max_length=4000)


@router.patch("/calls/scripts/{script_id}", response_model=ScriptOut)
def update_script(
    script_id: uuid.UUID,
    body: ScriptBody,
    actor: Actor = Depends(require_crm),
    db: Session = Depends(get_db),
) -> ScriptOut:
    script = db.get(CallScript, script_id)
    if script is None or script.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Call script not found.")
    script.body = body.body.strip()
    script.approved = True
    audit(db, actor, "call_script", str(script.id), "update", "Updated how the agent should talk.")
    db.commit()
    return ScriptOut(id=script.id, name=script.name, body=script.body, approved=script.approved)


@router.get("/calls", response_model=list[CallOut])
def list_calls(actor: Actor = Depends(get_actor), db: Session = Depends(get_db)) -> list[CallOut]:
    rows = db.scalars(
        select(SimulatedCall)
        .where(SimulatedCall.organization_id == actor.organization_id)
        .order_by(SimulatedCall.created_at.desc())
        .limit(50)
    ).all()
    return [_out(db, row) for row in rows]


@router.get("/calls/{call_id}", response_model=CallOut)
def get_call(
    call_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> CallOut:
    return _out(db, _owned(db, actor, call_id))


@router.post("/calls/simulate", response_model=CallOut, status_code=201)
def simulate(
    body: SimulateBody,
    actor: Actor = Depends(require_crm),
    db: Session = Depends(get_db),
) -> CallOut:
    contact = _contact(db, actor, body.contact_id)
    _guard(db, contact)
    script = _script(db, actor, body.script_id)
    call = _record(
        db,
        actor_id=actor.user.id,
        contact=contact,
        script_id=script.id if script else None,
        transcript=body.transcript,
        provider_call_id=f"demo-{uuid.uuid4()}",
    )
    audit(db, actor, "call", str(call.id), "simulate", "DEMO rehearsal. No number was dialed.")
    db.commit()
    db.refresh(call)
    return _out(db, call)


@router.post("/calls/{call_id}/review", response_model=CallOut)
def review_call(
    call_id: uuid.UUID,
    body: ReviewBody,
    actor: Actor = Depends(require_crm),
    db: Session = Depends(get_db),
) -> CallOut:
    call = _owned(db, actor, call_id)
    if call.review_status != "pending":
        raise ApiError(409, "already_reviewed", "This rehearsal was already reviewed.")
    if body.action not in {"accept", "reject"}:
        raise ApiError(422, "validation_error", "Review action must be accept or reject.")
    insight = CallInsight.model_validate_json(call.insight_json)
    if insight_can_auto_mark_won(insight):
        raise ApiError(409, "won_blocked", "A call note cannot mark an order won.")
    if body.action == "reject":
        call.review_status = "rejected"
        audit(db, actor, "call", str(call.id), "reject", "Rejected the DEMO call note.")
        db.commit()
        return _out(db, call)
    call.review_status = "accepted"
    _apply(db, actor, call, insight)
    audit(db, actor, "call", str(call.id), "accept", "Accepted the DEMO call note.")
    db.commit()
    db.refresh(call)
    return _out(db, call)


@router.post("/integrations/voice/webhook", response_model=CallOut)
def voice_webhook(
    body: WebhookBody,
    db: Session = Depends(get_db),
    signature: str | None = Header(default=None, alias="X-Demo-Voice-Signature"),
    authorization: str | None = Header(default=None),
    vapi_secret: str | None = Header(default=None, alias="X-Vapi-Secret"),
    vapi_timestamp: str | None = Header(default=None, alias="X-Vapi-Timestamp"),
) -> CallOut:
    if not _webhook_authorized(signature, authorization, vapi_secret, vapi_timestamp):
        raise ApiError(401, "unsigned", "Unsigned voice events are rejected.")
    contact = db.get(Contact, body.contact_id)
    if contact is None:
        raise ApiError(404, "not_found", "Contact not found.")
    try:
        key = call_event_idempotency_key(body.provider_call_id, body.provider_event_id)
    except ValueError as exc:
        raise ApiError(
            422, "validation_error", "Provider call id and event id are required."
        ) from exc
    existing = db.scalar(
        select(CallEvent).where(
            CallEvent.organization_id == contact.organization_id,
            CallEvent.idempotency_key == key,
        )
    )
    if existing is not None:
        call = db.get(SimulatedCall, existing.call_id)
        if call is None:
            raise ApiError(404, "not_found", "Call not found.")
        return _out(db, call)
    if contact.do_not_call or contact.permission_revoked or _suppressed(db, contact):
        raise ApiError(409, "do_not_call", "This contact is opted out.")
    call = _record(
        db,
        actor_id=contact.created_by,
        contact=contact,
        script_id=None,
        transcript=body.transcript,
        provider_call_id=body.provider_call_id.strip(),
    )
    db.add(
        CallEvent(
            organization_id=contact.organization_id,
            call_id=call.id,
            idempotency_key=key,
            provider_call_id=body.provider_call_id.strip(),
            provider_event_id=body.provider_event_id.strip(),
        )
    )
    db.commit()
    db.refresh(call)
    return _out(db, call)


def _record(
    db: Session,
    *,
    actor_id: uuid.UUID,
    contact: Contact,
    script_id: uuid.UUID | None,
    transcript: str,
    provider_call_id: str,
) -> SimulatedCall:
    insight = parse_transcript(transcript)
    call = SimulatedCall(
        organization_id=contact.organization_id,
        contact_id=contact.id,
        company_id=contact.company_id,
        actor_user_id=actor_id,
        script_id=script_id,
        provider_call_id=provider_call_id[:80],
        transcript=transcript.strip(),
        outcome=insight.outcome.value,
        insight_json=insight.model_dump_json(),
        review_status="pending",
        mode="demo",
        dialed=False,
    )
    db.add(call)
    db.flush()
    _place_contacted(db, call, actor_id, insight)
    if insight.do_not_call:
        contact.do_not_call = True
        contact.permission_revoked = True
        contact.channel_scope = "none"
        _suppress(db, contact, "DEMO transcript recorded do not call")
    return call


def _apply(db: Session, actor: Actor, call: SimulatedCall, insight: CallInsight) -> None:
    opportunity = db.scalar(
        select(Opportunity).where(
            Opportunity.organization_id == actor.organization_id,
            Opportunity.company_id == call.company_id,
        )
    )
    target = _stage(insight)
    if opportunity is not None and target is not None and opportunity.stage != target:
        previous = opportunity.stage
        opportunity.stage = target
        db.add(
            OpportunityStageEvent(
                organization_id=actor.organization_id,
                opportunity_id=opportunity.id,
                from_stage=previous,
                to_stage=target,
                reason=insight.next_action[:500],
                actor_user_id=actor.user.id,
            )
        )
    if insight.outcome in {
        CallOutcome.INTERESTED,
        CallOutcome.MEETING_REQUESTED,
        CallOutcome.FOLLOW_UP,
    }:
        due = datetime.now(UTC).date() + timedelta(days=7)
        db.add(
            Task(
                organization_id=actor.organization_id,
                company_id=call.company_id,
                opportunity_id=opportunity.id if opportunity else None,
                title=insight.next_action[:200],
                status="open",
                due_on=due,
                owner_user_id=actor.user.id,
                created_by=actor.user.id,
            )
        )


_WORKS = {
    CallOutcome.INTERESTED,
    CallOutcome.MEETING_REQUESTED,
    CallOutcome.FOLLOW_UP,
}
_ALREADY_CONTACTED = {
    OpportunityStage.CONTACTED.value,
    OpportunityStage.INTERESTED.value,
    OpportunityStage.MEETING_SCHEDULED.value,
    OpportunityStage.SAMPLE_TRIAL_REQUESTED.value,
    OpportunityStage.QUOTATION_SENT.value,
    OpportunityStage.NEGOTIATION.value,
    OpportunityStage.WON.value,
}


def _place_contacted(
    db: Session,
    call: SimulatedCall,
    actor_id: uuid.UUID,
    insight: CallInsight,
) -> None:
    if insight.outcome not in _WORKS:
        return
    opportunity = db.scalar(
        select(Opportunity).where(
            Opportunity.organization_id == call.organization_id,
            Opportunity.company_id == call.company_id,
        )
    )
    if opportunity is not None and opportunity.stage in _ALREADY_CONTACTED:
        return
    if opportunity is None:
        company = db.get(Company, call.company_id)
        title = company.display_name if company is not None else "Contacted lead"
        opportunity = Opportunity(
            organization_id=call.organization_id,
            company_id=call.company_id,
            title=title[:200],
            stage=OpportunityStage.CONTACTED.value,
            owner_user_id=actor_id,
        )
        db.add(opportunity)
        db.flush()
        previous = None
    else:
        previous = opportunity.stage
        opportunity.stage = OpportunityStage.CONTACTED.value
    db.add(
        OpportunityStageEvent(
            organization_id=call.organization_id,
            opportunity_id=opportunity.id,
            from_stage=previous,
            to_stage=OpportunityStage.CONTACTED.value,
            reason="Completed call works.",
            actor_user_id=actor_id,
        )
    )


def _stage(insight: CallInsight) -> str | None:
    if insight.outcome in _WORKS:
        return OpportunityStage.CONTACTED.value
    if insight.outcome is CallOutcome.NOT_INTERESTED:
        return OpportunityStage.NURTURE.value
    return None


def _guard(db: Session, contact: Contact) -> None:
    if not contact.email and not contact.phone:
        raise ApiError(
            409,
            "contact_required",
            "This lead needs an email or a mobile before a call can be saved.",
        )
    if contact.do_not_call or contact.permission_revoked or _suppressed(db, contact):
        raise ApiError(409, "do_not_call", "This contact is opted out.")


def _contact(db: Session, actor: Actor, contact_id: uuid.UUID) -> Contact:
    contact = db.get(Contact, contact_id)
    if contact is None or contact.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Contact not found.")
    return contact


def _owned(db: Session, actor: Actor, call_id: uuid.UUID) -> SimulatedCall:
    call = db.get(SimulatedCall, call_id)
    if call is None or call.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Call not found.")
    return call


def _script(db: Session, actor: Actor, script_id: uuid.UUID | None) -> CallScript | None:
    if script_id is None:
        return _ensure_script(db, actor)
    script = db.get(CallScript, script_id)
    if script is None or script.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Call script not found.")
    if not script.approved:
        raise ApiError(409, "script_unapproved", "Approve the script before a rehearsal.")
    return script


def _ensure_script(db: Session, actor: Actor) -> CallScript:
    row = db.scalar(
        select(CallScript).where(
            CallScript.organization_id == actor.organization_id,
            CallScript.name == DEMO_SCRIPT_NAME,
        )
    )
    if row is None:
        row = CallScript(
            organization_id=actor.organization_id,
            name=DEMO_SCRIPT_NAME,
            body=DEMO_SCRIPT_BODY,
            approved=True,
        )
        db.add(row)
        db.flush()
    return row


def _webhook_authorized(
    demo_signature: str | None,
    authorization: str | None,
    vapi_secret: str | None,
    timestamp: str | None,
) -> bool:
    secret = get_settings().voice_webhook_secret
    if not secret:
        return False
    if timestamp:
        try:
            sent = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return False
        if sent.tzinfo is None:
            return False
        skew = abs((datetime.now(UTC) - sent.astimezone(UTC)).total_seconds())
        if skew > 300:
            return False
    presented: list[str] = []
    if demo_signature:
        presented.append(demo_signature)
    if vapi_secret:
        presented.append(vapi_secret)
    if authorization and authorization.lower().startswith("bearer "):
        presented.append(authorization.split(" ", 1)[1].strip())
    return any(hmac.compare_digest(item.encode(), secret.encode()) for item in presented)


def _suppress(db: Session, contact: Contact, reason: str) -> None:
    for kind, value in (("email", contact.email), ("phone", contact.phone)):
        if not value:
            continue
        digest = channel_hash(contact.organization_id, kind, value)
        existing = db.scalar(
            select(Suppression).where(
                Suppression.organization_id == contact.organization_id,
                Suppression.channel_hash == digest,
            )
        )
        if existing is None:
            db.add(
                Suppression(
                    organization_id=contact.organization_id,
                    channel_hash=digest,
                    channel_kind=kind,
                    reason=reason[:200],
                )
            )


def _suppressed(db: Session, contact: Contact) -> bool:
    for kind, value in (("email", contact.email), ("phone", contact.phone)):
        if not value:
            continue
        digest = channel_hash(contact.organization_id, kind, value)
        found = db.scalar(
            select(Suppression.id).where(
                Suppression.organization_id == contact.organization_id,
                Suppression.channel_hash == digest,
            )
        )
        if found is not None:
            return True
    return False


def _out(db: Session, call: SimulatedCall) -> CallOut:
    company = db.get(Company, call.company_id)
    insight = CallInsight.model_validate_json(call.insight_json)
    events = db.scalar(
        select(func.count()).select_from(CallEvent).where(CallEvent.call_id == call.id)
    )
    return CallOut(
        id=call.id,
        contact_id=call.contact_id,
        company_id=call.company_id,
        company_name=company.display_name if company else "",
        transcript=call.transcript,
        outcome=call.outcome,
        summary=insight.summary,
        next_action=insight.next_action,
        review_status=call.review_status,
        mode=call.mode,
        dialed=False,
        needs_human_review=insight.needs_human_review,
        do_not_call=insight.do_not_call,
        event_count=int(events or 0),
    )
