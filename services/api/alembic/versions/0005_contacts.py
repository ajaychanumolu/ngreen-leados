"""Contact permission, suppression, and public-source fields.

Revision ID: 0005_contacts
Revises: 0004_evidence
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_contacts"
down_revision: str | None = "0004_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contacts", sa.Column("source_url", sa.String(length=500), nullable=True))
    op.add_column("contacts", sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contacts", sa.Column("owner_user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "contacts",
        sa.Column("validity", sa.String(length=40), nullable=False, server_default="unverified"),
    )
    op.add_column(
        "contacts",
        sa.Column("permission_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "contacts",
        sa.Column("permission_revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "contacts",
        sa.Column("do_not_call", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "contacts",
        sa.Column("channel_scope", sa.String(length=20), nullable=False, server_default="none"),
    )
    op.create_table(
        "contact_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("basis", sa.String(length=80), nullable=False),
        sa.Column("channel_scope", sa.String(length=20), nullable=False),
        sa.Column("proof_note", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contact_permissions_organization_id", "contact_permissions", ["organization_id"]
    )
    op.create_index("ix_contact_permissions_contact_id", "contact_permissions", ["contact_id"])
    op.create_table(
        "suppressions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("channel_hash", sa.String(length=64), nullable=False),
        sa.Column("channel_kind", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "channel_hash"),
    )
    op.create_index("ix_suppressions_organization_id", "suppressions", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_suppressions_organization_id", table_name="suppressions")
    op.drop_table("suppressions")
    op.drop_index("ix_contact_permissions_contact_id", table_name="contact_permissions")
    op.drop_index("ix_contact_permissions_organization_id", table_name="contact_permissions")
    op.drop_table("contact_permissions")
    op.drop_column("contacts", "channel_scope")
    op.drop_column("contacts", "do_not_call")
    op.drop_column("contacts", "permission_revoked")
    op.drop_column("contacts", "permission_expires_at")
    op.drop_column("contacts", "validity")
    op.drop_column("contacts", "owner_user_id")
    op.drop_column("contacts", "checked_at")
    op.drop_column("contacts", "source_url")
