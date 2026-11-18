import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import Actor, get_actor
from ngreen_api.models import Organization

router = APIRouter(prefix="/api/v1", tags=["me"])


class MeResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    organization_id: uuid.UUID
    organization_name: str
    role: str
    auth_mode: str


@router.get("/me", response_model=MeResponse)
def me(actor: Actor = Depends(get_actor), db: Session = Depends(get_db)) -> MeResponse:
    from ngreen_api.settings import get_settings

    org = db.get(Organization, actor.organization_id)
    if org is None:
        from ngreen_api.deps import ApiError

        raise ApiError(403, "forbidden", "Organization is missing.")
    return MeResponse(
        user_id=actor.user.id,
        email=actor.user.email,
        display_name=actor.user.display_name,
        organization_id=org.id,
        organization_name=org.name,
        role=actor.role,
        auth_mode=get_settings().auth_mode,
    )
