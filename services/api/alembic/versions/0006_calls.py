"""DEMO call rehearsal tables and seller-skip counts.

Revision ID: 0006_calls
Revises: 0005_contacts
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_calls"
down_revision: str | None = "0005_contacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "research_queries",
        sa.Column("seller_skipped", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "call_scripts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_call_scripts_organization_id", "call_scripts", ["organization_id"])
    op.create_table(
        "simulated_calls",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("script_id", sa.Uuid(), nullable=True),
        sa.Column("provider_call_id", sa.String(length=80), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(length=40), nullable=False),
        sa.Column("insight_json", sa.Text(), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("dialed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["script_id"], ["call_scripts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulated_calls_organization_id", "simulated_calls", ["organization_id"])
    op.create_index("ix_simulated_calls_contact_id", "simulated_calls", ["contact_id"])
    op.create_index("ix_simulated_calls_company_id", "simulated_calls", ["company_id"])
    op.create_table(
        "call_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("call_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("provider_call_id", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["simulated_calls.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "idempotency_key"),
    )
    op.create_index("ix_call_events_organization_id", "call_events", ["organization_id"])
    op.create_index("ix_call_events_call_id", "call_events", ["call_id"])


def downgrade() -> None:
    op.drop_index("ix_call_events_call_id", table_name="call_events")
    op.drop_index("ix_call_events_organization_id", table_name="call_events")
    op.drop_table("call_events")
    op.drop_index("ix_simulated_calls_company_id", table_name="simulated_calls")
    op.drop_index("ix_simulated_calls_contact_id", table_name="simulated_calls")
    op.drop_index("ix_simulated_calls_organization_id", table_name="simulated_calls")
    op.drop_table("simulated_calls")
    op.drop_index("ix_call_scripts_organization_id", table_name="call_scripts")
    op.drop_table("call_scripts")
    op.drop_column("research_queries", "seller_skipped")
