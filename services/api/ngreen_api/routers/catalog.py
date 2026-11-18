import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ngreen_api.db import get_db
from ngreen_api.deps import Actor, get_actor
from ngreen_api.models import CompanyProductNeed, Industry, IndustryAlias, Membership, Product, User

router = APIRouter(prefix="/api/v1", tags=["catalog"])


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    company_count: int


class IndustryOut(BaseModel):
    id: uuid.UUID
    name: str
    aliases: list[str]


class MemberOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str


@router.get("/products", response_model=list[ProductOut])
def list_products(
    actor: Actor = Depends(get_actor), db: Session = Depends(get_db)
) -> list[ProductOut]:
    rows = db.scalars(
        select(Product)
        .where(Product.organization_id == actor.organization_id)
        .order_by(Product.sort_order)
    ).all()
    counts = dict(
        db.execute(
            select(CompanyProductNeed.product_id, func.count())
            .where(CompanyProductNeed.organization_id == actor.organization_id)
            .group_by(CompanyProductNeed.product_id)
        ).all()
    )
    return [
        ProductOut(id=row.id, name=row.name, company_count=int(counts.get(row.id, 0)))
        for row in rows
    ]


@router.get("/industries", response_model=list[IndustryOut])
def list_industries(
    actor: Actor = Depends(get_actor), db: Session = Depends(get_db)
) -> list[IndustryOut]:
    rows = db.scalars(
        select(Industry)
        .where(Industry.organization_id == actor.organization_id)
        .order_by(Industry.sort_order)
    ).all()
    aliases: dict[uuid.UUID, list[str]] = {row.id: [] for row in rows}
    for alias in db.scalars(
        select(IndustryAlias).where(IndustryAlias.organization_id == actor.organization_id)
    ).all():
        aliases.setdefault(alias.industry_id, []).append(alias.alias)
    return [
        IndustryOut(id=row.id, name=row.name, aliases=sorted(aliases.get(row.id, [])))
        for row in rows
    ]


@router.get("/members", response_model=list[MemberOut])
def list_members(
    actor: Actor = Depends(get_actor), db: Session = Depends(get_db)
) -> list[MemberOut]:
    rows = db.execute(
        select(User, Membership.role)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.organization_id == actor.organization_id)
        .order_by(User.display_name)
    ).all()
    return [
        MemberOut(id=user.id, email=user.email, display_name=user.display_name, role=role)
        for user, role in rows
    ]
