from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import Actor, get_actor
from ngreen_api.models import Company, Contact, Opportunity, ResearchCandidate

router = APIRouter(prefix="/api/v1", tags=["overview"])


class OverviewResponse(BaseModel):
    accounts: int
    reference_targets: int
    opportunities: int
    manual_contacts: int
    research_candidates: int
    accounts_source: str = "database"
    unavailable: list[str]


@router.get("/overview", response_model=OverviewResponse)
def overview(actor: Actor = Depends(get_actor), db: Session = Depends(get_db)) -> OverviewResponse:
    org = actor.organization_id

    def counted(model: type, *extra) -> int:
        stmt = select(func.count()).select_from(model).where(model.organization_id == org)
        for clause in extra:
            stmt = stmt.where(clause)
        return int(db.scalar(stmt) or 0)

    return OverviewResponse(
        accounts=counted(Company),
        reference_targets=counted(Company, Company.source_origin == "reference_sheet"),
        opportunities=counted(Opportunity),
        manual_contacts=counted(Contact, Contact.source_url.is_(None)),
        research_candidates=counted(ResearchCandidate, ResearchCandidate.status == "pending"),
        unavailable=[
            "permissioned_contacts",
            "meetings",
            "won_orders",
        ],
    )
