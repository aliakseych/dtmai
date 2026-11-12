"""labeling: archived flag on import batches; archive smoke/pilot batches

Revision ID: labeling_0004
Revises: labeling_0003
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op

revision = "labeling_0004"
down_revision = "labeling_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "import_batches",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="labeling",
    )
    op.execute(
        "UPDATE labeling.import_batches SET archived = true "
        "WHERE status NOT IN ('pending', 'running') "
        "AND (source_code ILIKE 'smoke%' OR source_code ILIKE 'pilot-%')"
    )


def downgrade() -> None:
    op.drop_column("import_batches", "archived", schema="labeling")
