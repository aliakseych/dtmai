"""catalog: per-subject reference (formula) sheets

Revision ID: catalog_0003
Revises: catalog_0002
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "catalog_0003"
down_revision = "catalog_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reference_sheets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "subject_id",
            sa.Uuid(),
            sa.ForeignKey("catalog.subjects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contents", postgresql.JSONB(), nullable=False),
        sa.Column("source", sa.String(500), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("subject_id", name="uq_reference_sheets_subject_id"),
        schema="catalog",
    )


def downgrade() -> None:
    op.drop_table("reference_sheets", schema="catalog")
