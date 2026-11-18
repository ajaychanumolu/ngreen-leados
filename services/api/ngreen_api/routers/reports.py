"""Pipeline counts read from stored rows. Nothing here is a revenue forecast."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.clock import INDIA, india_today
from ngreen_api.csvio import render_csv
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_reports
from ngreen_api.models import (
    Membership,
    Opportunity,
    OpportunityStageEvent,
    ResearchAssessment,
    ResearchCandidate,
    ResearchQuery,
    ResearchRun,
    SimulatedCall,
    Task,
    UsageEvent,
    User,
)
from ngreen_contracts.enums import OpportunityStage

router = APIRouter(prefix="/api/v1", tags=["reports"])

_RETRY = frozenset({"failed", "cancelled", "capped"})
_NOTES = (
    "Every count is a query on this organization's rows.",
    "A zero means the query returned no rows.",
    "Credits per candidate are provider units, not rupees and not revenue.",
    "An approved candidate was accepted by a person. It is not a confirmed order.",
    "The fit average is omitted when no assessment is stored.",
    "Overdue tasks are open tasks due before today in Asia/Kolkata.",
    "Rehearsals use mode demo and were not dialed. Live attempts use mode live.",
)


class StageCount(BaseModel):
    stage: str
    count: int
    oldest_days: int | None


class TeamRow(BaseModel):
    user_id: uuid.UUID
    display_name: str
    role: str
    open_tasks: int
    opportunities: int


class AlertRow(BaseModel):
    kind: str
    summary: str
    entity_id: uuid.UUID


class RetryRow(BaseModel):
    run_id: uuid.UUID
    status: str
    error_summary: str | None
    spent_credits: int


class SpendLine(BaseModel):
    id: uuid.UUID
    kind: str
    units: int
    mode: str
    created_at: datetime


class SpendPage(BaseModel):
    items: list[SpendLine]
    page: int
    page_size: int
    total: int


class TeamMember(BaseModel):
    user_id: uuid.UUID
    display_name: str
    role: str


class FunnelReport(BaseModel):
    source: str = "database"
    as_of: date
    stages: list[StageCount]
    candidates_stored: int
    candidates_pending: int
    candidates_approved: int
    candidates_rejected: int
    candidates_merged: int
    queries_ok: int
    results_stored: int
    known_skipped: int
    seller_skipped: int
    query_errors: int
    search_credits: int
    contact_search_credits: int
    model_tokens: int
    credits_per_stored_candidate: float | None
    credits_per_approved_candidate: float | None
    assessed: int
    average_fit: float | None
    contradictions: int
    zero_fit: int
    rehearsals: int
    live_attempts: int
    calls_pending_review: int
    tasks_open: int
    tasks_overdue: int
    tasks_unassigned: int
    team: list[TeamRow]
    alerts: list[AlertRow]
    alerts_truncated: bool
    retry_queue: list[RetryRow]
    recent_spend: list[SpendLine]
    notes: list[str] = Field(default_factory=lambda: list(_NOTES))


def _aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment


def _age_days(moment: datetime, today: date) -> int:
    local = _aware(moment).astimezone(INDIA).date()
    return max(0, (today - local).days)


def _per(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 2)


def _units(db: Session, org: uuid.UUID, kind: str) -> int:
    value = db.scalar(
        select(func.coalesce(func.sum(UsageEvent.units), 0)).where(
            UsageEvent.organization_id == org,
            UsageEvent.kind == kind,
        )
    )
    return int(value or 0)


@router.get("/team", response_model=list[TeamMember])
def list_team(actor: Actor = Depends(get_actor), db: Session = Depends(get_db)) -> list[TeamMember]:
    rows = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.organization_id == actor.organization_id)
        .order_by(User.display_name)
    ).all()
    return [
        TeamMember(user_id=user.id, display_name=user.display_name, role=membership.role)
        for membership, user in rows
    ]


@router.get("/reports/funnel", response_model=FunnelReport)
def funnel(
    actor: Actor = Depends(require_reports),
    db: Session = Depends(get_db),
) -> FunnelReport:
    return _report(db, actor.organization_id)


@router.get("/reports/spend", response_model=SpendPage)
def spend(
    page: int = 1,
    page_size: int = 50,
    actor: Actor = Depends(require_reports),
    db: Session = Depends(get_db),
) -> SpendPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    org = actor.organization_id
    base = select(UsageEvent).where(UsageEvent.organization_id == org)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(UsageEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return SpendPage(
        items=[_spend(row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.get("/reports/export")
def export_report(
    actor: Actor = Depends(require_reports),
    db: Session = Depends(get_db),
) -> Response:
    report = _report(db, actor.organization_id)
    rows: list[list[object]] = [["note", note] for note in report.notes]
    rows.append(["as_of", report.as_of.isoformat()])
    for stage in report.stages:
        rows.append([f"stage_{stage.stage}", stage.count, stage.oldest_days])
    rows.extend(
        [
            ["candidates_stored", report.candidates_stored],
            ["candidates_approved", report.candidates_approved],
            ["search_credits", report.search_credits],
            ["credits_per_stored_candidate", report.credits_per_stored_candidate],
            ["credits_per_approved_candidate", report.credits_per_approved_candidate],
            ["model_tokens", report.model_tokens],
            ["assessed", report.assessed],
            ["average_fit", report.average_fit],
            ["rehearsals", report.rehearsals],
            ["live_attempts", report.live_attempts],
            ["tasks_open", report.tasks_open],
            ["tasks_overdue", report.tasks_overdue],
        ]
    )
    for line in report.recent_spend:
        rows.append(["spend", line.kind, line.units, line.mode, line.created_at.isoformat()])
    body = render_csv(["section", "value", "extra", "detail", "when"], rows)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="leados-report.csv"'},
    )


def _report(db: Session, org: uuid.UUID) -> FunnelReport:
    today = india_today()
    stages = _stages(db, org, today)
    stored = _candidates(db, org, None)
    pending = _candidates(db, org, "pending")
    approved = _candidates(db, org, "approved")
    rejected = _candidates(db, org, "rejected")
    merged = _candidates(db, org, "merged")
    search_credits = _units(db, org, "search")
    assessed = _assessed(db, org)
    fit_sum = db.scalar(
        select(func.coalesce(func.sum(ResearchAssessment.fit_total), 0)).where(
            ResearchAssessment.organization_id == org
        )
    )
    alerts, truncated = _alerts(db, org, today)
    return FunnelReport(
        as_of=today,
        stages=stages,
        candidates_stored=stored,
        candidates_pending=pending,
        candidates_approved=approved,
        candidates_rejected=rejected,
        candidates_merged=merged,
        queries_ok=_queries(db, org, "ok"),
        results_stored=_query_sum(db, org, ResearchQuery.result_count),
        known_skipped=_query_sum(db, org, ResearchQuery.known_skipped),
        seller_skipped=_query_sum(db, org, ResearchQuery.seller_skipped),
        query_errors=_queries(db, org, "error"),
        search_credits=search_credits,
        contact_search_credits=_units(db, org, "contact_search"),
        model_tokens=_units(db, org, "model"),
        credits_per_stored_candidate=_per(search_credits, stored),
        credits_per_approved_candidate=_per(search_credits, approved),
        assessed=assessed,
        average_fit=_per(int(fit_sum or 0), assessed),
        contradictions=_flagged(db, org, ResearchAssessment.contradiction.is_(True)),
        zero_fit=_flagged(db, org, ResearchAssessment.fit_total == 0),
        rehearsals=_calls(db, org, SimulatedCall.mode == "demo"),
        live_attempts=_calls(db, org, SimulatedCall.mode == "live"),
        calls_pending_review=_calls(db, org, SimulatedCall.review_status == "pending"),
        tasks_open=_tasks(db, org, Task.status == "open"),
        tasks_overdue=_overdue_count(db, org, today),
        tasks_unassigned=_tasks(
            db, org, Task.status == "open", Task.owner_user_id.is_(None)
        ),
        team=_team(db, org),
        alerts=alerts,
        alerts_truncated=truncated,
        retry_queue=_retry(db, org),
        recent_spend=_recent(db, org),
    )


def _candidates(db: Session, org: uuid.UUID, status: str | None) -> int:
    stmt = select(func.count()).select_from(ResearchCandidate).where(
        ResearchCandidate.organization_id == org
    )
    if status is not None:
        stmt = stmt.where(ResearchCandidate.status == status)
    return int(db.scalar(stmt) or 0)


def _queries(db: Session, org: uuid.UUID, status: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ResearchQuery)
            .where(ResearchQuery.organization_id == org, ResearchQuery.status == status)
        )
        or 0
    )


def _query_sum(db: Session, org: uuid.UUID, column) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(column), 0)).where(ResearchQuery.organization_id == org)
        )
        or 0
    )


def _assessed(db: Session, org: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ResearchAssessment)
            .where(ResearchAssessment.organization_id == org)
        )
        or 0
    )


def _flagged(db: Session, org: uuid.UUID, clause) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ResearchAssessment)
            .where(ResearchAssessment.organization_id == org, clause)
        )
        or 0
    )


def _calls(db: Session, org: uuid.UUID, clause) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(SimulatedCall)
            .where(SimulatedCall.organization_id == org, clause)
        )
        or 0
    )


def _tasks(db: Session, org: uuid.UUID, *clauses) -> int:
    stmt = select(func.count()).select_from(Task).where(Task.organization_id == org)
    for clause in clauses:
        stmt = stmt.where(clause)
    return int(db.scalar(stmt) or 0)


def _overdue_count(db: Session, org: uuid.UUID, today: date) -> int:
    return _tasks(
        db,
        org,
        Task.status == "open",
        Task.due_on.is_not(None),
        Task.due_on < today,
    )


def _stages(db: Session, org: uuid.UUID, today: date) -> list[StageCount]:
    opportunities = db.scalars(
        select(Opportunity).where(Opportunity.organization_id == org)
    ).all()
    latest: dict[uuid.UUID, datetime] = {}
    events = db.scalars(
        select(OpportunityStageEvent).where(OpportunityStageEvent.organization_id == org)
    ).all()
    for event in events:
        previous = latest.get(event.opportunity_id)
        if previous is None or _aware(event.created_at) > _aware(previous):
            latest[event.opportunity_id] = event.created_at
    grouped: dict[str, list[int]] = {stage.value: [] for stage in OpportunityStage}
    for opportunity in opportunities:
        moment = latest.get(opportunity.id, opportunity.created_at)
        grouped.setdefault(opportunity.stage, []).append(_age_days(moment, today))
    return [
        StageCount(
            stage=stage,
            count=len(ages),
            oldest_days=max(ages) if ages else None,
        )
        for stage, ages in grouped.items()
    ]


def _team(db: Session, org: uuid.UUID) -> list[TeamRow]:
    members = db.execute(
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(Membership.organization_id == org)
        .order_by(User.display_name)
    ).all()
    open_tasks = db.scalars(
        select(Task).where(Task.organization_id == org, Task.status == "open")
    ).all()
    owned = db.scalars(select(Opportunity).where(Opportunity.organization_id == org)).all()
    task_counts: dict[uuid.UUID, int] = {}
    opportunity_counts: dict[uuid.UUID, int] = {}
    for task in open_tasks:
        if task.owner_user_id is not None:
            task_counts[task.owner_user_id] = task_counts.get(task.owner_user_id, 0) + 1
    for opportunity in owned:
        if opportunity.owner_user_id is not None:
            key = opportunity.owner_user_id
            opportunity_counts[key] = opportunity_counts.get(key, 0) + 1
    return [
        TeamRow(
            user_id=user.id,
            display_name=user.display_name,
            role=membership.role,
            open_tasks=task_counts.get(user.id, 0),
            opportunities=opportunity_counts.get(user.id, 0),
        )
        for membership, user in members
    ]


def _alerts(db: Session, org: uuid.UUID, today: date) -> tuple[list[AlertRow], bool]:
    found: list[AlertRow] = []
    runs = db.scalars(
        select(ResearchRun)
        .where(ResearchRun.organization_id == org, ResearchRun.status.in_(("failed", "capped")))
        .order_by(ResearchRun.created_at.desc())
    ).all()
    for run in runs:
        kind = "research_failed" if run.status == "failed" else "research_capped"
        summary = run.error_summary or "Research run stopped before it finished."
        found.append(AlertRow(kind=kind, summary=summary[:200], entity_id=run.id))
    queries = db.scalars(
        select(ResearchQuery)
        .where(ResearchQuery.organization_id == org, ResearchQuery.status == "error")
        .order_by(ResearchQuery.position)
    ).all()
    for query in queries:
        found.append(
            AlertRow(
                kind="query_error",
                summary=(query.error or "A search query failed.")[:200],
                entity_id=query.run_id,
            )
        )
    overdue = db.scalars(
        select(Task)
        .where(
            Task.organization_id == org,
            Task.status == "open",
            Task.due_on.is_not(None),
            Task.due_on < today,
        )
        .order_by(Task.due_on)
    ).all()
    for task in overdue:
        found.append(AlertRow(kind="task_overdue", summary=task.title[:200], entity_id=task.id))
    pending = db.scalars(
        select(SimulatedCall)
        .where(SimulatedCall.organization_id == org, SimulatedCall.review_status == "pending")
        .order_by(SimulatedCall.created_at.desc())
    ).all()
    for call in pending:
        found.append(
            AlertRow(
                kind="call_pending",
                summary="A rehearsal is waiting for a person to accept or reject the note.",
                entity_id=call.id,
            )
        )
    return found[:40], len(found) > 40


def _retry(db: Session, org: uuid.UUID) -> list[RetryRow]:
    runs = db.scalars(
        select(ResearchRun)
        .where(ResearchRun.organization_id == org, ResearchRun.status.in_(_RETRY))
        .order_by(ResearchRun.created_at.desc())
    ).all()
    return [
        RetryRow(
            run_id=run.id,
            status=run.status,
            error_summary=run.error_summary,
            spent_credits=run.spent_credits,
        )
        for run in runs
    ]


def _recent(db: Session, org: uuid.UUID) -> list[SpendLine]:
    rows = db.scalars(
        select(UsageEvent)
        .where(UsageEvent.organization_id == org)
        .order_by(UsageEvent.created_at.desc())
        .limit(20)
    ).all()
    return [_spend(row) for row in rows]


def _spend(row: UsageEvent) -> SpendLine:
    return SpendLine(
        id=row.id,
        kind=row.kind,
        units=row.units,
        mode=row.mode,
        created_at=row.created_at,
    )
