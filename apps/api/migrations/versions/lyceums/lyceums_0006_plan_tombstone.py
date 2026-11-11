"""lyceums: tombstones for admin-deleted seed plan rows

Revision ID: lyceums_0006
Revises: lyceums_0005
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "lyceums_0006"
down_revision = "lyceums_0005"
branch_labels = None
depends_on = None

S = "lyceums"


def upgrade() -> None:
    op.create_table(
        "lyceum_plan_tombstone",
        sa.Column(
            "lyceum_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(f"{S}.lyceums.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("direction_code", sa.String(20), primary_key=True),
        sa.Column("language_name", sa.String(40), primary_key=True, server_default=""),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("lyceum_plan_tombstone", schema=S)
