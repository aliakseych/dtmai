"""catalog: lesson theory cards

Revision ID: catalog_0002
Revises: catalog_0001
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "catalog_0002"
down_revision = "catalog_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lessons",
        sa.Column("theory", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        schema="catalog",
    )


def downgrade() -> None:
    op.drop_column("lessons", "theory", schema="catalog")
