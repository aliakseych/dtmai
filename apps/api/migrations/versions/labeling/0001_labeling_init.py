"""labeling: solve runs, review queue, decisions, audits, generation runs, ingestion batches

Revision ID: labeling_0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "labeling_0001"
down_revision = None
branch_labels = ("labeling",)
depends_on = None

S = "labeling"
UUID = postgresql.UUID(as_uuid=True)


def _now() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def _id() -> sa.Column:
    return sa.Column("id", UUID, nullable=False)


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "solve_runs",
        _id(),
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("trigger", sa.String(20), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("key_conflict", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("response", sa.JSON()),
        _now(),
        sa.PrimaryKeyConstraint("id", name="pk_solve_runs"),
        schema=S,
    )
    op.create_index("ix_solve_runs_question_id", "solve_runs", ["question_id"], schema=S)
    op.create_table(
        "solver_votes",
        _id(),
        sa.Column("run_id", UUID, nullable=False),
        sa.Column("stage", sa.String(12), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("response", sa.JSON()),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reasoning", sa.Text()),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error", sa.String(300)),
        sa.PrimaryKeyConstraint("id", name="pk_solver_votes"),
        sa.ForeignKeyConstraint(
            ["run_id"],
            [f"{S}.solve_runs.id"],
            name="fk_solver_votes_run_id_solve_runs",
            ondelete="CASCADE",
        ),
        schema=S,
    )
    op.create_index("ix_solver_votes_run_id", "solver_votes", ["run_id"], schema=S)
    op.create_table(
        "queue_items",
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("suggested", sa.JSON()),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("topic_id", UUID),
        sa.Column("type_id", UUID),
        sa.Column("language", sa.String(10), nullable=False),
        _now(),
        sa.Column("claimed_by", UUID),
        sa.Column("claimed_until", sa.DateTime(timezone=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("question_id", name="pk_queue_items"),
        schema=S,
    )
    op.create_index(
        "ix_queue_open", "queue_items", ["state", "resolved_at", "confidence"], schema=S
    )
    op.create_index("ix_queue_items_subject_id", "queue_items", ["subject_id"], schema=S)
    op.create_index("ix_queue_items_language", "queue_items", ["language"], schema=S)
    op.create_table(
        "decisions",
        _id(),
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("labeler_id", UUID, nullable=False),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("response", sa.JSON()),
        sa.Column("time_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prev_status", sa.String(20)),
        sa.Column("new_status", sa.String(20)),
        sa.Column("prev_response", sa.JSON()),
        sa.Column("prev_queue_state", sa.String(20)),
        sa.Column("audit_sample_id", UUID),
        sa.Column("reason", sa.String(200)),
        _now(),
        sa.Column("undone_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_decisions"),
        schema=S,
    )
    op.create_index("ix_decisions_question", "decisions", ["question_id", "created_at"], schema=S)
    op.create_index("ix_decisions_labeler", "decisions", ["labeler_id", "created_at"], schema=S)
    op.create_table(
        "audit_samples",
        _id(),
        sa.Column("batch_id", UUID, nullable=False),
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("machine_response", sa.JSON()),
        sa.Column("human_response", sa.JSON()),
        sa.Column("labeler_id", UUID),
        sa.Column("matched", sa.Boolean()),
        sa.Column(
            "sampled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_audit_samples"),
        schema=S,
    )
    op.create_index(
        "ix_audit_open", "audit_samples", ["completed_at", "subject_id", "language"], schema=S
    )
    op.create_index("ix_audit_samples_batch_id", "audit_samples", ["batch_id"], schema=S)
    op.create_index("ix_audit_samples_question_id", "audit_samples", ["question_id"], schema=S)
    op.create_table(
        "generation_runs",
        _id(),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("topic_id", UUID),
        sa.Column("type_id", UUID, nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("requested", sa.Integer(), nullable=False),
        sa.Column("difficulty", sa.Float()),
        sa.Column("prompt_template", sa.Text()),
        sa.Column("status", sa.String(12), nullable=False, server_default="pending"),
        sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("created_by", UUID),
        _now(),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_generation_runs"),
        schema=S,
    )
    op.create_table(
        "import_batches",
        _id(),
        sa.Column("source_code", sa.String(80), nullable=False),
        sa.Column("source_name", sa.String(200)),
        sa.Column("source_year", sa.Integer()),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("base", sa.String(120)),
        sa.Column("topic_id", UUID),
        sa.Column("type_ids", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("has_answer_key", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("root", sa.String(500), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="pending"),
        sa.Column("files_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("questions_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text()),
        sa.Column("created_by", UUID),
        _now(),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_import_batches"),
        schema=S,
    )
    op.create_table(
        "import_files",
        _id(),
        sa.Column("batch_id", UUID, nullable=False),
        sa.Column("path", sa.String(600), nullable=False),
        sa.Column("page", sa.Integer()),
        sa.Column("status", sa.String(12), nullable=False, server_default="pending"),
        sa.Column("extracted", sa.JSON()),
        sa.Column("question_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("error", sa.Text()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_import_files"),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            [f"{S}.import_batches.id"],
            name="fk_import_files_batch_id_import_batches",
            ondelete="CASCADE",
        ),
        schema=S,
    )
    op.create_index("ix_import_files_batch", "import_files", ["batch_id", "status"], schema=S)


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
