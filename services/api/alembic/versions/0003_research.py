"""Research runs, queries, candidates, sources, and usage.

Revision ID: 0003_research
Revises: 0002_crm
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_research"
down_revision: str | None = "0002_crm"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("industry_id", sa.Uuid(), nullable=True),
        sa.Column("geography", sa.String(length=120), nullable=False),
        sa.Column("limit_companies", sa.Integer(), nullable=False),
        sa.Column("max_queries", sa.Integer(), nullable=False),
        sa.Column("max_results_per_query", sa.Integer(), nullable=False),
        sa.Column("budget_credits", sa.Integer(), nullable=False),
        sa.Column("spent_credits", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("worker", sa.String(length=20), nullable=False),
        sa.Column("queries_total", sa.Integer(), nullable=False),
        sa.Column("queries_done", sa.Integer(), nullable=False),
        sa.Column("error_summary", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["industry_id"], ["industries.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_runs_organization_id", "research_runs", ["organization_id"])
    op.create_table(
        "research_queries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("query_text", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_research_queries_organization_id", "research_queries", ["organization_id"])
    op.create_index("ix_research_queries_run_id", "research_queries", ["run_id"])
    op.create_table(
        "research_candidates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("canonical_domain", sa.String(length=200), nullable=True),
        sa.Column("identity_key", sa.String(length=220), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("duplicate_company_id", sa.Uuid(), nullable=True),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["duplicate_company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "identity_key"),
    )
    op.create_index(
        "ix_research_candidates_organization_id", "research_candidates", ["organization_id"]
    )
    op.create_index("ix_research_candidates_run_id", "research_candidates", ["run_id"])
    op.create_table(
        "sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("query_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("canonical_url", sa.String(length=500), nullable=False),
        sa.Column("page_title", sa.String(length=300), nullable=False),
        sa.Column("domain", sa.String(length=200), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["research_candidates.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["query_id"], ["research_queries.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sources_organization_id", "sources", ["organization_id"])
    op.create_index("ix_sources_candidate_id", "sources", ["candidate_id"])
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("units", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_organization_id", "usage_events", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_events_organization_id", table_name="usage_events")
    op.drop_table("usage_events")
    op.drop_index("ix_sources_candidate_id", table_name="sources")
    op.drop_index("ix_sources_organization_id", table_name="sources")
    op.drop_table("sources")
    op.drop_index("ix_research_candidates_run_id", table_name="research_candidates")
    op.drop_index("ix_research_candidates_organization_id", table_name="research_candidates")
    op.drop_table("research_candidates")
    op.drop_index("ix_research_queries_run_id", table_name="research_queries")
    op.drop_index("ix_research_queries_organization_id", table_name="research_queries")
    op.drop_table("research_queries")
    op.drop_index("ix_research_runs_organization_id", table_name="research_runs")
    op.drop_table("research_runs")
