"""assessment: mock attempts

Revision ID: assessment_0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "assessment_0001"
down_revision = None
branch_labels = ("assessment",)
depends_on = None

S = "assessment"
U = sa.Uuid()


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "mock_attempts",
        sa.Column("id", U, nullable=False),
        sa.Column("user_id", U, nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("blueprint_id", U),
        sa.Column("blueprint_version", sa.Integer()),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("questions", sa.JSON(), nullable=False),
        sa.Column("sections", sa.JSON(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("flags", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON()),
        sa.Column("submit_reason", sa.String(10)),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("score", sa.Float()),
        sa.PrimaryKeyConstraint("id", name="pk_mock_attempts"),
        schema=S,
    )
    op.create_index(
        "uq_mock_attempts_one_active", "mock_attempts", ["user_id"], unique=True,
        schema=S, postgresql_where=sa.text("status = 'in_progress'"),
    )
    op.create_index("ix_mock_attempts_user_started", "mock_attempts", ["user_id", "started_at"], schema=S)
    op.create_index(
        "ix_mock_attempts_deadline", "mock_attempts", ["deadline"],
        schema=S, postgresql_where=sa.text("status = 'in_progress'"),
    )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
