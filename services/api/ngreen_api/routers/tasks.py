import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.clock import india_today
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, ApiError, get_actor, require_writer
from ngreen_api.models import Membership, Task
from ngreen_api.records import audit, owned_company

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    company_id: uuid.UUID | None = None
    due_on: date | None = None
    owner_user_id: uuid.UUID | None = None


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: str | None = None
    due_on: date | None = None
    owner_user_id: uuid.UUID | None = None


class TaskOut(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    company_id: uuid.UUID | None
    due_on: date | None
    owner_user_id: uuid.UUID | None
    overdue: bool
    created_at: datetime


class TaskPage(BaseModel):
    items: list[TaskOut]
    page: int
    page_size: int
    total: int


@router.get("", response_model=TaskPage)
def list_tasks(
    page: int = 1,
    page_size: int = 50,
    status: str | None = None,
    overdue: bool = False,
    owner_id: uuid.UUID | None = None,
    actor: Actor = Depends(get_actor),
    db: Session = Depends(get_db),
) -> TaskPage:
    if page < 1 or page_size < 1 or page_size > 100:
        raise ApiError(422, "validation_error", "Page must be >= 1 and page size 1–100.")
    base = select(Task).where(Task.organization_id == actor.organization_id)
    if status:
        if status not in {"open", "done"}:
            raise ApiError(422, "validation_error", "Status must be open or done.")
        base = base.where(Task.status == status)
    if overdue:
        base = base.where(
            Task.status == "open",
            Task.due_on.is_not(None),
            Task.due_on < india_today(),
        )
    if owner_id is not None:
        _member(db, actor, owner_id)
        base = base.where(Task.owner_user_id == owner_id)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    rows = db.scalars(
        base.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return TaskPage(
        items=[_out(row) for row in rows],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskBody,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> TaskOut:
    if body.company_id is not None:
        owned_company(db, actor, body.company_id)
    task = Task(
        organization_id=actor.organization_id,
        company_id=body.company_id,
        title=body.title.strip(),
        status="open",
        due_on=body.due_on,
        owner_user_id=_member(db, actor, body.owner_user_id or actor.user.id),
        created_by=actor.user.id,
    )
    db.add(task)
    db.flush()
    audit(db, actor, "task", str(task.id), "create", "Created a task")
    db.commit()
    db.refresh(task)
    return _out(task)


@router.patch("/{task_id}", response_model=TaskOut)
def patch_task(
    task_id: uuid.UUID,
    body: TaskPatch,
    actor: Actor = Depends(require_writer),
    db: Session = Depends(get_db),
) -> TaskOut:
    task = db.get(Task, task_id)
    if task is None or task.organization_id != actor.organization_id:
        raise ApiError(404, "not_found", "Task not found.")
    if body.status is not None and body.status not in {"open", "done"}:
        raise ApiError(422, "validation_error", "Status must be open or done.")
    if "title" in body.model_fields_set and body.title is not None:
        task.title = body.title.strip()
    if body.status is not None:
        task.status = body.status
    if "due_on" in body.model_fields_set:
        task.due_on = body.due_on
    if "owner_user_id" in body.model_fields_set:
        task.owner_user_id = (
            None if body.owner_user_id is None else _member(db, actor, body.owner_user_id)
        )
    audit(db, actor, "task", str(task.id), "update", "Updated a task")
    db.commit()
    db.refresh(task)
    return _out(task)


def _member(db: Session, actor: Actor, user_id: uuid.UUID) -> uuid.UUID:
    membership = db.scalar(
        select(Membership).where(
            Membership.organization_id == actor.organization_id,
            Membership.user_id == user_id,
        )
    )
    if membership is None:
        raise ApiError(422, "validation_error", "That person is not on this team.")
    return user_id


def _out(task: Task) -> TaskOut:
    overdue = (
        task.status == "open" and task.due_on is not None and task.due_on < india_today()
    )
    return TaskOut(
        id=task.id,
        title=task.title,
        status=task.status,
        company_id=task.company_id,
        due_on=task.due_on,
        owner_user_id=task.owner_user_id,
        overdue=overdue,
        created_at=task.created_at,
    )
