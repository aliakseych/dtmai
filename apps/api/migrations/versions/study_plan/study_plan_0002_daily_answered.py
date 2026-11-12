"""study_plan: record answered daily questions

Revision ID: study_plan_0002
Revises: study_plan_0001
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op

revision = "study_plan_0002"
down_revision = "study_plan_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "daily_set",
        sa.Column("answered", sa.JSON(), nullable=False, server_default="[]"),
        schema="study_plan",
    )


def downgrade() -> None:
    op.drop_column("daily_set", "answered", schema="study_plan")
