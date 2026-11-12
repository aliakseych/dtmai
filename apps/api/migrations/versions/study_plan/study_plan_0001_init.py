"""study_plan: plan, task, daily_set

Revision ID: study_plan_0001
Revises:
Create Date: 2026-11-20
"""

import sqlalchemy as sa
from alembic import op

revision = "study_plan_0001"
down_revision = None
branch_labels = ("study_plan",)
depends_on = None

S = "study_plan"
_UUID = sa.Uuid()


def _ts(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "plan",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("settings", sa.JSON(), nullable=False),
        sa.Column("plan_end", sa.Date()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_replanned_on", sa.Date()),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_plan"),
        sa.UniqueConstraint("user_id", name="uq_plan_user_id"),
        schema=S,
    )
    op.create_table(
        "task",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("plan_id", _UUID, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("subject_id", _UUID),
        sa.Column("target", sa.JSON(), nullable=False),
        sa.Column("est_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="todo"),
        sa.Column("done_at", sa.DateTime(timezone=True)),
        sa.Column("source_ref", _UUID),
        sa.PrimaryKeyConstraint("id", name="pk_task"),
        sa.ForeignKeyConstraint(
            ["plan_id"], [f"{S}.plan.id"], name="fk_task_plan_id_plan", ondelete="CASCADE"
        ),
        sa.CheckConstraint(
            "kind in ('lesson','drill','review','mock','rush')", name="ck_task_kind"
        ),
        sa.CheckConstraint("status in ('todo','done','missed')", name="ck_task_status"),
        schema=S,
    )
    op.create_index("ix_task_plan_id_day", "task", ["plan_id", "day"], schema=S)
    op.create_index("ix_task_plan_id_status_day", "task", ["plan_id", "status", "day"], schema=S)
    op.create_table(
        "daily_set",
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("question_ids", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "day", name="pk_daily_set"),
        schema=S,
    )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
