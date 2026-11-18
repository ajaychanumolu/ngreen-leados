"""Labeled demo rows for a client walkthrough. Running this again does not duplicate them."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "services" / "api"), str(ROOT / "packages" / "contracts" / "src")]

from sqlalchemy import select  # noqa: E402

from ngreen_api.db import get_session_factory  # noqa: E402
from ngreen_api.mock_voice import DEMO_SCRIPT_BODY, parse_transcript  # noqa: E402
from ngreen_api.models import (  # noqa: E402
    Company,
    Contact,
    Opportunity,
    OpportunityStageEvent,
    Organization,
    SimulatedCall,
    User,
)
from ngreen_contracts.taxonomy import normalize_company_name  # noqa: E402

NOTE = "Sample row for the client demo. Not a verified buyer and not a real call."
AGENT = DEMO_SCRIPT_BODY.strip()

ROWS = [
    {
        "name": "DEMO Green Basket",
        "city": "Pune",
        "email": "buyer@green-basket.example",
        "phone": "+919000000001",
        "buyer": None,
    },
    {
        "name": "DEMO Metro Kitchen",
        "city": "Bengaluru",
        "email": "buyer@metro-kitchen.example",
        "phone": "+919000000002",
        "buyer": "No answer. They did not lift the call.",
    },
    {
        "name": "DEMO Lake Pharmacy",
        "city": "Hyderabad",
        "email": "buyer@lake-pharmacy.example",
        "phone": "+919000000003",
        "buyer": "Interested in Carry Bags and wants a sample next week.",
    },
    {
        "name": "DEMO Hill Stores",
        "city": "Chennai",
        "email": "buyer@hill-stores.example",
        "phone": "+919000000004",
        "buyer": "Not interested in packaging right now.",
    },
]


def main() -> None:
    db = get_session_factory()()
    try:
        org = db.scalar(select(Organization).where(Organization.slug == "ngreen"))
        actor = db.scalar(select(User).where(User.email == "owner@ngreen.demo"))
        if org is None or actor is None:
            raise SystemExit("Start the API once, then run this demo seed again.")
        added = 0
        for row in ROWS:
            normalized = normalize_company_name(row["name"])
            company = db.scalar(
                select(Company).where(
                    Company.organization_id == org.id,
                    Company.normalized_name == normalized,
                )
            )
            if company is not None:
                continue
            company = Company(
                organization_id=org.id,
                display_name=row["name"],
                normalized_name=normalized,
                city=row["city"],
                country="India",
                notes=NOTE,
                source_origin="manual",
                review_status="pending",
                review_label="Demo walkthrough",
                business_unit="",
            )
            db.add(company)
            db.flush()
            contact = Contact(
                organization_id=org.id,
                company_id=company.id,
                display_name="Buyer desk",
                email=row["email"],
                phone=row["phone"],
                source_note=NOTE,
                permission_basis="unknown",
                channel_scope="none",
                created_by=actor.id,
            )
            db.add(contact)
            db.flush()
            stage = "research"
            buyer = row["buyer"]
            if buyer and "interested in carry bags" in buyer.casefold():
                stage = "contacted"
            opportunity = Opportunity(
                organization_id=org.id,
                company_id=company.id,
                stage=stage,
                title=row["name"][:200],
                owner_user_id=actor.id,
            )
            db.add(opportunity)
            db.flush()
            db.add(
                OpportunityStageEvent(
                    organization_id=org.id,
                    opportunity_id=opportunity.id,
                    from_stage=None,
                    to_stage=stage,
                    reason=NOTE,
                    actor_user_id=actor.id,
                )
            )
            if buyer:
                transcript = f"Agent: {AGENT}\n\nBuyer: {buyer}"
                insight = parse_transcript(transcript)
                db.add(
                    SimulatedCall(
                        organization_id=org.id,
                        contact_id=contact.id,
                        company_id=company.id,
                        actor_user_id=actor.id,
                        provider_call_id=f"demo-mock-{uuid.uuid4()}",
                        transcript=transcript,
                        outcome=insight.outcome.value,
                        insight_json=insight.model_dump_json(),
                        review_status="pending",
                        mode="demo",
                        dialed=False,
                    )
                )
            added += 1
        db.commit()
        print(f"Demo rows added: {added}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
