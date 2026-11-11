"""gamification: per-user daily XP goal

Revision ID: gamification_0002
Revises: gamification_0001
Create Date: 2026-11-13
"""

import sqlalchemy as sa
from alembic import op

revision = "gamification_0002"
down_revision = "gamification_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_stats",
        sa.Column("daily_goal_xp", sa.Integer(), nullable=False, server_default="20"),
        schema="gamification",
    )


def downgrade() -> None:
    op.drop_column("user_stats", "daily_goal_xp", schema="gamification")
