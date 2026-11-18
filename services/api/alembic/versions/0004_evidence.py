"""Evidence claims, fit assessments, and known-lead skips.

Revision ID: 0004_evidence
Revises: 0003_research
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_evidence"
down_revision: str | None = "0003_research"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "research_queries",
        sa.Column("known_skipped", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "research_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("fit_total", sa.Integer(), nullable=False),
        sa.Column("reasons_json", sa.Text(), nullable=False),
        sa.Column("industry_alignment", sa.Integer(), nullable=False),
        sa.Column("product_fit", sa.Integer(), nullable=False),
        sa.Column("operational_scale", sa.Integer(), nullable=False),
        sa.Column("geography_supply", sa.Integer(), nullable=False),
        sa.Column("buyer_relevant_evidence", sa.Integer(), nullable=False),
        sa.Column("source_freshness", sa.Integer(), nullable=False),
        sa.Column("contradiction", sa.Boolean(), nullable=False),
        sa.Column("dropped_claims", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["candidate_id"], ["research_candidates.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("candidate_id"),
    )
    op.create_index(
        "ix_research_assessments_organization_id", "research_assessments", ["organization_id"]
    )
    op.create_index(
        "ix_research_assessments_candidate_id", "research_assessments", ["candidate_id"]
    )
    op.create_table(
        "evidence_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("supported", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["research_candidates.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evidence_claims_organization_id", "evidence_claims", ["organization_id"])
    op.create_index("ix_evidence_claims_candidate_id", "evidence_claims", ["candidate_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_claims_candidate_id", table_name="evidence_claims")
    op.drop_index("ix_evidence_claims_organization_id", table_name="evidence_claims")
    op.drop_table("evidence_claims")
    op.drop_index("ix_research_assessments_candidate_id", table_name="research_assessments")
    op.drop_index("ix_research_assessments_organization_id", table_name="research_assessments")
    op.drop_table("research_assessments")
    op.drop_column("research_queries", "known_skipped")
