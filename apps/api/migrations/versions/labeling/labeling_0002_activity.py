"""labeling: labeler activity log

Revision ID: labeling_0002
Revises: labeling_0001
Create Date: 2026-11-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "labeling_0002"
down_revision = "labeling_0001"
branch_labels = None
depends_on = None

S = "labeling"


def upgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        schema=S,
    )
    op.create_index("ix_activity_actor", "activity", ["actor_user_id", "created_at"], schema=S)
    op.create_index("ix_activity_action", "activity", ["action", "created_at"], schema=S)


def downgrade() -> None:
    op.drop_table("activity", schema=S)
