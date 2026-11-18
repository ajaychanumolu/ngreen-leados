"""Load the reference sheet as unverified hypotheses. No contacts are created."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ngreen_api.models import (
    AuditEvent,
    Company,
    CompanyProductNeed,
    Industry,
    IndustryAlias,
    Opportunity,
    OpportunityStageEvent,
    Product,
    User,
)
from ngreen_contracts.reference import load_reference_catalog
from ngreen_contracts.taxonomy import (
    CANONICAL_INDUSTRIES,
    JSON_INDUSTRY_ALIASES,
    PRODUCT_HEADINGS,
    REFERENCE_REVIEW_LABEL,
)


def reference_json_path() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "data" / "reference_accounts.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("data/reference_accounts.json")


def seed_catalog(db: Session, organization_id: uuid.UUID) -> None:
    catalog = load_reference_catalog(reference_json_path())
    products = _products(db, organization_id)
    industries = _industries(db, organization_id)
    _aliases(db, organization_id, industries)
    actor = db.scalar(select(User).where(User.email == "owner@ngreen.demo"))
    inserted = 0
    for target in catalog.targets():
        company = db.scalar(
            select(Company).where(
                Company.organization_id == organization_id,
                Company.normalized_name == target.normalized_name,
            )
        )
        if company is None:
            company = Company(
                organization_id=organization_id,
                display_name=target.display_name,
                normalized_name=target.normalized_name,
                country="India",
                source_origin=target.source_origin,
                review_status="pending",
                review_label=REFERENCE_REVIEW_LABEL,
                industry_id=None,
                business_unit="",
            )
            db.add(company)
            db.flush()
            inserted += 1
            if actor is not None:
                open_research_opportunity(db, company, actor.id, from_sheet=True)
        for product_name in target.product_hypotheses:
            product = products[product_name]
            exists = db.scalar(
                select(CompanyProductNeed).where(
                    CompanyProductNeed.company_id == company.id,
                    CompanyProductNeed.product_id == product.id,
                )
            )
            if exists is None:
                db.add(
                    CompanyProductNeed(
                        organization_id=organization_id,
                        company_id=company.id,
                        product_id=product.id,
                        need_status="hypothesis",
                        evidence_note=None,
                        source_origin="reference_sheet",
                    )
                )
        if actor is not None and _opportunity(db, company.id) is None:
            open_research_opportunity(db, company, actor.id, from_sheet=True)
    if actor is not None:
        covered = set(
            db.scalars(
                select(Opportunity.company_id).where(Opportunity.organization_id == organization_id)
            ).all()
        )
        for company in db.scalars(
            select(Company).where(Company.organization_id == organization_id)
        ).all():
            if company.id not in covered:
                open_research_opportunity(
                    db,
                    company,
                    actor.id,
                    from_sheet=company.source_origin == "reference_sheet",
                )
    if inserted and actor is not None:
        db.add(
            AuditEvent(
                organization_id=organization_id,
                actor_user_id=actor.id,
                entity_type="catalog",
                entity_id=str(organization_id),
                action="seed_reference",
                summary=f"Loaded {inserted} reference targets as unverified hypotheses",
            )
        )
    db.flush()


def _products(db: Session, organization_id: uuid.UUID) -> dict[str, Product]:
    found: dict[str, Product] = {}
    for index, name in enumerate(PRODUCT_HEADINGS):
        row = db.scalar(
            select(Product).where(Product.organization_id == organization_id, Product.name == name)
        )
        if row is None:
            row = Product(organization_id=organization_id, name=name, sort_order=index)
            db.add(row)
            db.flush()
        found[name] = row
    return found


def _industries(db: Session, organization_id: uuid.UUID) -> dict[str, Industry]:
    found: dict[str, Industry] = {}
    for index, name in enumerate(CANONICAL_INDUSTRIES):
        row = db.scalar(
            select(Industry).where(
                Industry.organization_id == organization_id, Industry.name == name
            )
        )
        if row is None:
            row = Industry(organization_id=organization_id, name=name, sort_order=index)
            db.add(row)
            db.flush()
        found[name] = row
    return found


def _aliases(db: Session, organization_id: uuid.UUID, industries: dict[str, Industry]) -> None:
    for alias, canonical in JSON_INDUSTRY_ALIASES.items():
        existing = db.scalar(
            select(IndustryAlias).where(
                IndustryAlias.organization_id == organization_id,
                IndustryAlias.alias == alias,
            )
        )
        if existing is None:
            db.add(
                IndustryAlias(
                    organization_id=organization_id,
                    industry_id=industries[canonical].id,
                    alias=alias,
                )
            )
    db.flush()


def _opportunity(db: Session, company_id: uuid.UUID) -> Opportunity | None:
    return db.scalar(select(Opportunity).where(Opportunity.company_id == company_id))


def open_research_opportunity(
    db: Session, company: Company, actor_id: uuid.UUID, *, from_sheet: bool
) -> Opportunity:
    title = f"{company.display_name} research"
    reason = (
        "Loaded from the reference sheet as an unverified hypothesis."
        if from_sheet
        else "Account added by staff. Stage starts at Research."
    )
    opportunity = Opportunity(
        organization_id=company.organization_id,
        company_id=company.id,
        stage="research",
        title=title[:200],
        value_inr=None,
        owner_user_id=None,
    )
    db.add(opportunity)
    db.flush()
    db.add(
        OpportunityStageEvent(
            organization_id=company.organization_id,
            opportunity_id=opportunity.id,
            from_stage=None,
            to_stage="research",
            reason=reason,
            actor_user_id=actor_id,
        )
    )
    return opportunity
