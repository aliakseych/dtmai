"""learning: sessions, attempts, ratings, mastery, review cards, placements

Revision ID: learning_0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "learning_0001"
down_revision = None
branch_labels = ("learning",)
depends_on = None

S = "learning"
U = sa.Uuid()


def _now(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "sessions",
        sa.Column("id", U, nullable=False),
        sa.Column("user_id", U, nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("subject_id", U),
        sa.Column("topic_id", U),
        sa.Column("lesson_id", U),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_sessions"),
        schema=S,
    )
    op.create_index("ix_sessions_user_status", "sessions", ["user_id", "status"], schema=S)

    op.create_table(
        "attempts",
        sa.Column("id", U, nullable=False),
        sa.Column("session_id", U, nullable=False),
        sa.Column("user_id", U, nullable=False),
        sa.Column("question_id", U, nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("response", sa.JSON(), nullable=False),
        sa.Column("time_ms", sa.Integer()),
        sa.Column("elo_delta", sa.Integer(), nullable=False, server_default="0"),
        _now("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_attempts"),
        sa.UniqueConstraint("session_id", "question_id", name="uq_attempts_session_question"),
        schema=S,
    )
    op.create_index("ix_attempts_session_id", "attempts", ["session_id"], schema=S)
    op.create_index("ix_attempts_user_id", "attempts", ["user_id"], schema=S)

    op.create_table(
        "ratings",
        sa.Column("user_id", U, nullable=False),
        sa.Column("subject_id", U, nullable=False),
        sa.Column("elo", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "subject_id", name="pk_ratings"),
        schema=S,
    )

    op.create_table(
        "mastery",
        sa.Column("user_id", U, nullable=False),
        sa.Column("topic_id", U, nullable=False),
        sa.Column("type_id", U, nullable=False),
        sa.Column("subject_id", U, nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        _now("updated_at"),
        sa.PrimaryKeyConstraint("user_id", "topic_id", "type_id", name="pk_mastery"),
        schema=S,
    )
    op.create_index("ix_mastery_user_subject", "mastery", ["user_id", "subject_id"], schema=S)

    op.create_table(
        "review_cards",
        sa.Column("user_id", U, nullable=False),
        sa.Column("question_id", U, nullable=False),
        sa.Column("subject_id", U, nullable=False),
        sa.Column("topic_id", U, nullable=False),
        sa.Column("type_id", U, nullable=False),
        sa.Column("ease", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("lapses", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "question_id", name="pk_review_cards"),
        schema=S,
    )
    op.create_index(
        "ix_review_cards_due", "review_cards", ["user_id", "subject_id", "due_at"], schema=S
    )

    op.create_table(
        "placements",
        sa.Column("user_id", U, nullable=False),
        sa.Column("subject_id", U, nullable=False),
        sa.Column("start_unit_index", sa.Integer(), nullable=False),
        sa.Column("ability", sa.Float()),
        sa.Column("skipped", sa.Boolean(), nullable=False, server_default=sa.false()),
        _now("completed_at"),
        sa.PrimaryKeyConstraint("user_id", "subject_id", name="pk_placements"),
        schema=S,
    )

    op.create_table(
        "processed_events",
        sa.Column("event_id", U, nullable=False),
        sa.Column("handler", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("event_id", "handler", name="pk_processed_events"),
        schema=S,
    )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
