import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from ngreen_api.csvio import ParsedRow, commit_csv, preview_csv
from ngreen_api.db import get_db
from ngreen_api.deps import Actor, require_importer
from ngreen_api.records import audit

router = APIRouter(prefix="/api/v1/imports", tags=["imports"])


class CsvBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_text: str = Field(min_length=1, max_length=500_000)


class CommitBody(CsvBody):
    update_rows: list[int] = Field(default_factory=list, max_length=500)


class RowOut(BaseModel):
    row_number: int
    status: str
    display_name: str | None
    message: str
    match_id: uuid.UUID | None = None


class PreviewOut(BaseModel):
    ready: int
    errors: int
    duplicates: int
    rows: list[RowOut]


class CommitOut(BaseModel):
    created: int
    updated: int
    skipped: int
    failed: int
    rows: list[RowOut]


@router.post("/preview", response_model=PreviewOut)
def preview(
    body: CsvBody,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> PreviewOut:
    rows = preview_csv(db, actor, body.csv_text)
    return PreviewOut(
        ready=sum(row.status == "ready" for row in rows),
        errors=sum(row.status == "error" for row in rows),
        duplicates=sum(row.status == "duplicate" for row in rows),
        rows=[_row(row) for row in rows],
    )


@router.post("/commit", response_model=CommitOut)
def commit(
    body: CommitBody,
    actor: Actor = Depends(require_importer),
    db: Session = Depends(get_db),
) -> CommitOut:
    batch, rows = commit_csv(db, actor, body.csv_text, set(body.update_rows))
    audit(
        db,
        actor,
        "import",
        str(batch.id),
        "commit",
        (
            f"Import created {batch.created_count}, updated {batch.updated_count}, "
            f"skipped {batch.skipped_count}, failed {batch.failed_count}"
        ),
    )
    db.commit()
    return CommitOut(
        created=batch.created_count,
        updated=batch.updated_count,
        skipped=batch.skipped_count,
        failed=batch.failed_count,
        rows=[_row(row) for row in rows],
    )


def _row(row: ParsedRow) -> RowOut:
    return RowOut(
        row_number=row.row_number,
        status=row.status,
        display_name=row.display_name or None,
        message=row.message,
        match_id=row.match_id,
    )
