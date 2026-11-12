"""catalog: archived flag on question bases; archive smoke/pilot bases

Revision ID: catalog_0004
Revises: catalog_0003
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op

revision = "catalog_0004"
down_revision = "catalog_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_bases",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="catalog",
    )
    # Archive, never delete: questions keep their source. Admin can unarchive.
    op.execute(
        "UPDATE catalog.question_bases SET archived = true "
        "WHERE code ILIKE 'smoke%' OR code ILIKE 'pilot-%'"
    )


def downgrade() -> None:
    op.drop_column("question_bases", "archived", schema="catalog")
