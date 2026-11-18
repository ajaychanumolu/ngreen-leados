import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_crm, require_writer
from ngreen_api.models import Company, Contact, Opportunity, OpportunityStageEvent, Task
from ngreen_api.records import audit, blank, owned_company
from ngreen_contracts.enums import OpportunityStage

router = APIRouter(prefix="/api/v1/opportunities", tags=["opportunities"])


class OpportunityBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    value_inr: int | None = Field(default=None, ge=0, le=1_000_000_000)
    heuristic_note: str | None = Field(default=None, max_length=300)


class StageBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_stage: OpportunityStage
    reason: str = Field(min_length=3, max_length=500)


class OpportunityOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    title: str
    stage: str
    value_inr: int | None
    heuristic_note: str | None
    review_label: str | None
    updated_at: datetime


class OpportunityPage(BaseModel):
    items: list[OpportunityOut]
    page: int
    page_size: int
    total: int


class StageEventOut(BaseModel):
    id: uuid.UUID
    from_stage: str | None
    to_stage: str
    reason: str
    created_at: datetime


@router.get("", response_model=OpportunityPage)
def list_opportunities(
    page: int = 1,
    page_size: int = 100,
    stage: str | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> OpportunityPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    base = select(Opportunity).where(Opportunity.organization_id == actor.organization_id)
    if stage:
        if stage not in {item.value for item in OpportunityStage}:
            raise ApiError(422, "validation_error", "Unknown stage.")
        base = base.where(Opportunity.stage == stage)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(Opportunity.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return OpportunityPage(
        items=[_out(db, row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.post("", response_model=OpportunityOut, status_code=201)
def create_opportunity(
    body: OpportunityBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> OpportunityOut:
    company = owned_company(db, actor, body.company_id)
    opportunity = Opportunity(
        organization_id=actor.organization_id,
        company_id=company.id,
        title=body.title.strip(),
        stage=OpportunityStage.RESEARCH.value,
        value_inr=body.value_inr,
        heuristic_note=blank(body.heuristic_note),
        owner_user_id=actor.user.id,
    )
    db.add(opportunity)
    db.flush()
    db.add(
        OpportunityStageEvent(
            organization_id=actor.organization_id,
            opportunity_id=opportunity.id,
            from_stage=None,
            to_stage=OpportunityStage.RESEARCH.value,
            reason="Opportunity opened by staff at Research.",
            actor_user_id=actor.user.id,
        )
    )
    audit(db, actor, "opportunity", str(opportunity.id), "create", "Opened an opportunity")
    db.commit()
    db.refresh(opportunity)
    return _out(db, opportunity)


@router.patch("/{opportunity_id}/stage", response_model=OpportunityOut)
def move_stage(
    opportunity_id: uuid.UUID,
    body: StageBody,
    actor: Actor = Depends(require_crm),
    db: Session = Depends(get_db),
) -> OpportunityOut:
    opportunity = _owned(db, actor, opportunity_id)
    target = body.to_stage.value
    if opportunity.stage == target:
        raise ApiError(422, "validation_error", "The opportunity is already in that stage.")
    if target == OpportunityStage.OUTREACH_ELIGIBLE.value and not _permitted(db, opportunity):
        raise ApiError(
            409,
            "permission_required",
            "Outreach Eligible needs a contact whose permission is not unknown.",
        )
    previous = opportunity.stage
    opportunity.stage = target
    if target in {OpportunityStage.WON.value, OpportunityStage.LOST.value}:
        opportunity.close_reason = body.reason.strip()
    db.add(
        OpportunityStageEvent(
            organization_id=actor.organization_id,
            opportunity_id=opportunity.id,
            from_stage=previous,
            to_stage=target,
            reason=body.reason.strip(),
            actor_user_id=actor.user.id,
        )
    )
    if target == OpportunityStage.SAMPLE_TRIAL_REQUESTED.value:
        _sample_task(db, actor, opportunity)
    audit(db, actor, "opportunity", str(opportunity.id), "stage", f"Stage {previous} to {target}")
    db.commit()
    db.refresh(opportunity)
    return _out(db, opportunity)


@router.get("/{opportunity_id}/events", response_model=list[StageEventOut])
def list_events(
    opportunity_id: uuid.UUID,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> list[StageEventOut]:
    opportunity = _owned(db, actor, opportunity_id)
    rows = db.scalars(
        select(OpportunityStageEvent)
        .where(OpportunityStageEvent.opportunity_id == opportunity.id)
        .order_by(OpportunityStageEvent.created_at)
    ).all()
    return [
        StageEventOut(
            id=row.id,
            from_stage=row.from_stage,
            to_stage=row.to_stage,
            reason=row.reason,
            created_at=row.created_at,
        )
        for row in rows
    ]


def _owned(db: Session, actor: Actor, opportunity_id: uuid.UUID) -> Opportunity:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None or opportunity.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Opportunity not found.")
    return opportunity


def _permitted(db: Session, opportunity: Opportunity) -> bool:
    contact = db.scalar(
        select(Contact).where(
            Contact.company_id == opportunity.company_id,
            Contact.permission_basis != "unknown",
        )
    )
    return contact is not None


def _sample_task(db: Session, actor: Actor, opportunity: Opportunity) -> None:
    title = "Review sample request"
    existing = db.scalar(
        select(Task).where(
            Task.opportunity_id == opportunity.id,
            Task.title == title,
            Task.status == "open",
        )
    )
    if existing is not None:
        return
    db.add(
        Task(
            organization_id=actor.organization_id,
            company_id=opportunity.company_id,
            opportunity_id=opportunity.id,
            title=title,
            status="open",
            owner_user_id=actor.user.id,
            created_by=actor.user.id,
        )
    )


def _out(db: Session, opportunity: Opportunity) -> OpportunityOut:
    company = db.get(Company, opportunity.company_id)
    return OpportunityOut(
        id=opportunity.id,
        company_id=opportunity.company_id,
        company_name=company.display_name if company else "",
        title=opportunity.title,
        stage=opportunity.stage,
        value_inr=opportunity.value_inr,
        heuristic_note=opportunity.heuristic_note,
        review_label=company.review_label if company else None,
        updated_at=opportunity.updated_at,
    )
