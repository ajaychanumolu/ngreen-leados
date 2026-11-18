"""Manual CRM catalogue, needs, contacts, opportunities, tasks, and imports.

Revision ID: 0002_crm
Revises: 0001_foundation
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_crm"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "industries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index("ix_industries_organization_id", "industries", ["organization_id"])
    op.create_table(
        "industry_aliases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("industry_id", sa.Uuid(), nullable=False),
        sa.Column("alias", sa.String(length=120), nullable=False),
        sa.ForeignKeyConstraint(["industry_id"], ["industries.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "alias"),
    )
    op.create_index("ix_industry_aliases_organization_id", "industry_aliases", ["organization_id"])
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index("ix_products_organization_id", "products", ["organization_id"])
    with op.batch_alter_table("companies") as batch:
        batch.add_column(sa.Column("review_label", sa.String(length=80), nullable=True))
        batch.add_column(sa.Column("owner_user_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("industry_id", sa.Uuid(), nullable=True))
        batch.add_column(sa.Column("industry_assignment", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("canonical_domain", sa.String(length=200), nullable=True))
        batch.add_column(
            sa.Column("business_unit", sa.String(length=120), nullable=False, server_default="")
        )
        batch.create_foreign_key("fk_companies_owner_user_id", "users", ["owner_user_id"], ["id"])
        batch.create_foreign_key(
            "fk_companies_industry_id", "industries", ["industry_id"], ["id"]
        )
    op.create_index(
        "uq_companies_domain_unit",
        "companies",
        ["organization_id", "canonical_domain", "business_unit"],
        unique=True,
        sqlite_where=sa.text("canonical_domain IS NOT NULL"),
        postgresql_where=sa.text("canonical_domain IS NOT NULL"),
    )
    op.create_table(
        "company_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "label"),
    )
    op.create_index("ix_company_tags_organization_id", "company_tags", ["organization_id"])
    op.create_index("ix_company_tags_company_id", "company_tags", ["company_id"])
    op.create_table(
        "company_product_needs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("need_status", sa.String(length=40), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("source_origin", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "product_id"),
    )
    op.create_index(
        "ix_company_product_needs_organization_id", "company_product_needs", ["organization_id"]
    )
    op.create_index("ix_company_product_needs_company_id", "company_product_needs", ["company_id"])
    op.create_index("ix_company_product_needs_product_id", "company_product_needs", ["product_id"])
    op.create_table(
        "company_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_notes_organization_id", "company_notes", ["organization_id"])
    op.create_index("ix_company_notes_company_id", "company_notes", ["company_id"])
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=True),
        sa.Column("role_title", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("source_note", sa.String(length=500), nullable=False),
        sa.Column("permission_basis", sa.String(length=80), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_organization_id", "contacts", ["organization_id"])
    op.create_index("ix_contacts_company_id", "contacts", ["company_id"])
    op.create_table(
        "crm_opportunities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("stage", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("value_inr", sa.Integer(), nullable=True),
        sa.Column("heuristic_note", sa.String(length=300), nullable=True),
        sa.Column("close_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_crm_opportunities_organization_id", "crm_opportunities", ["organization_id"]
    )
    op.create_index("ix_crm_opportunities_company_id", "crm_opportunities", ["company_id"])
    op.create_index("ix_crm_opportunities_stage", "crm_opportunities", ["stage"])
    op.create_table(
        "opportunity_stage_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("opportunity_id", sa.Uuid(), nullable=False),
        sa.Column("from_stage", sa.String(length=40), nullable=True),
        sa.Column("to_stage", sa.String(length=40), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["crm_opportunities.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_opportunity_stage_events_organization_id",
        "opportunity_stage_events",
        ["organization_id"],
    )
    op.create_index(
        "ix_opportunity_stage_events_opportunity_id",
        "opportunity_stage_events",
        ["opportunity_id"],
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=True),
        sa.Column("owner_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["opportunity_id"], ["crm_opportunities.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_organization_id", "tasks", ["organization_id"])
    op.create_table(
        "imports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_imports_organization_id", "imports", ["organization_id"])
    op.create_table(
        "import_rows",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("import_id", sa.Uuid(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["import_id"], ["imports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_import_rows_import_id", "import_rows", ["import_id"])


def downgrade() -> None:
    op.drop_index("ix_import_rows_import_id", table_name="import_rows")
    op.drop_table("import_rows")
    op.drop_index("ix_imports_organization_id", table_name="imports")
    op.drop_table("imports")
    op.drop_index("ix_tasks_organization_id", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(
        "ix_opportunity_stage_events_opportunity_id", table_name="opportunity_stage_events"
    )
    op.drop_index(
        "ix_opportunity_stage_events_organization_id", table_name="opportunity_stage_events"
    )
    op.drop_table("opportunity_stage_events")
    op.drop_index("ix_crm_opportunities_stage", table_name="crm_opportunities")
    op.drop_index("ix_crm_opportunities_company_id", table_name="crm_opportunities")
    op.drop_index("ix_crm_opportunities_organization_id", table_name="crm_opportunities")
    op.drop_table("crm_opportunities")
    op.drop_index("ix_contacts_company_id", table_name="contacts")
    op.drop_index("ix_contacts_organization_id", table_name="contacts")
    op.drop_table("contacts")
    op.drop_index("ix_company_notes_company_id", table_name="company_notes")
    op.drop_index("ix_company_notes_organization_id", table_name="company_notes")
    op.drop_table("company_notes")
    op.drop_index("ix_company_product_needs_product_id", table_name="company_product_needs")
    op.drop_index("ix_company_product_needs_company_id", table_name="company_product_needs")
    op.drop_index("ix_company_product_needs_organization_id", table_name="company_product_needs")
    op.drop_table("company_product_needs")
    op.drop_index("ix_company_tags_company_id", table_name="company_tags")
    op.drop_index("ix_company_tags_organization_id", table_name="company_tags")
    op.drop_table("company_tags")
    op.drop_index("uq_companies_domain_unit", table_name="companies")
    with op.batch_alter_table("companies") as batch:
        batch.drop_constraint("fk_companies_industry_id", type_="foreignkey")
        batch.drop_constraint("fk_companies_owner_user_id", type_="foreignkey")
        batch.drop_column("business_unit")
        batch.drop_column("canonical_domain")
        batch.drop_column("industry_assignment")
        batch.drop_column("industry_id")
        batch.drop_column("owner_user_id")
        batch.drop_column("review_label")
    op.drop_index("ix_products_organization_id", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_industry_aliases_organization_id", table_name="industry_aliases")
    op.drop_table("industry_aliases")
    op.drop_index("ix_industries_organization_id", table_name="industries")
    op.drop_table("industries")
