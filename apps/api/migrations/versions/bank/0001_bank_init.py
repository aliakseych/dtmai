"""bank: passages, questions, explanations, reports, audit

Revision ID: bank_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "bank_0001"
down_revision = None
branch_labels = ("bank",)
depends_on = None

S = "bank"
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()


def _ts(name: str) -> sa.Column:
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "passages",
        sa.Column("id", UUID, nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("title", sa.String(300)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("media", JSONB, nullable=False, server_default="[]"),
        sa.Column("source_id", UUID),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_passages"),
        schema=S,
    )
    op.create_table(
        "questions",
        sa.Column("id", UUID, nullable=False),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("topic_id", UUID, nullable=False),
        sa.Column("type_id", UUID, nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("media", JSONB, nullable=False, server_default="[]"),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("answer", JSONB, nullable=False),
        sa.Column("answer_official", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("difficulty", sa.Float(), nullable=False, server_default="1000"),
        sa.Column("passage_id", UUID),
        sa.Column("parent_id", UUID),
        sa.Column("source_id", UUID),
        sa.Column("source_ref", JSONB),
        sa.Column("translation_group_id", UUID),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("report_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.String(64)),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_questions"),
        sa.ForeignKeyConstraint(
            ["passage_id"], [f"{S}.passages.id"], name="fk_questions_passage_id_passages"
        ),
        sa.CheckConstraint(
            "status IN ('draft','auto_agreed','escalated','needs_human','verified','hidden','retired')",
            name="ck_questions_status",
        ),
        schema=S,
    )
    op.create_index(
        "ix_questions_pick", "questions", ["subject_id", "language", "status"], schema=S
    )
    op.create_index("ix_questions_topic", "questions", ["topic_id", "status"], schema=S)
    for col in ("type_id", "passage_id", "parent_id", "source_id", "translation_group_id"):
        op.create_index(f"ix_questions_{col}", "questions", [col], schema=S)
    op.create_table(
        "question_explanations",
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("model", sa.String(100), nullable=False, server_default=""),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("question_id", "locale", name="pk_question_explanations"),
        sa.ForeignKeyConstraint(
            ["question_id"],
            [f"{S}.questions.id"],
            ondelete="CASCADE",
            name="fk_question_explanations_question_id_questions",
        ),
        schema=S,
    )
    op.create_table(
        "question_reports",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("question_id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_question_reports"),
        sa.ForeignKeyConstraint(
            ["question_id"],
            [f"{S}.questions.id"],
            ondelete="CASCADE",
            name="fk_question_reports_question_id_questions",
        ),
        sa.UniqueConstraint("question_id", "user_id", name="uq_question_reports_question_id"),
        schema=S,
    )
    op.create_index(
        "ix_question_reports_question_id", "question_reports", ["question_id"], schema=S
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", UUID, nullable=False),
        _ts("at"),
        sa.PrimaryKeyConstraint("event_id", name="pk_processed_events"),
        schema=S,
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor", sa.String(64)),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("entity_id", UUID),
        sa.Column("before", JSONB),
        sa.Column("after", JSONB),
        sa.Column("reason", sa.String(500), nullable=False, server_default=""),
        _ts("at"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        schema=S,
    )
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"], schema=S)


def downgrade() -> None:
    for t in (
        "audit_log",
        "processed_events",
        "question_reports",
        "question_explanations",
        "questions",
        "passages",
    ):
        op.drop_table(t, schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
