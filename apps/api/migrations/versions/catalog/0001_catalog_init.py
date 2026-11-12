"""catalog: subjects, topics, question types, paths, blueprints, bases, audit

Revision ID: catalog_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "catalog_0001"
down_revision = None
branch_labels = ("catalog",)
depends_on = None

S = "catalog"
UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()


def _id(t: str) -> sa.Column:
    return sa.Column("id", UUID, nullable=False)


def _fk(col: str, table: str, name_t: str, ondelete: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [col], [f"{S}.{table}.id"], ondelete=ondelete, name=f"fk_{name_t}_{col}_{table}"
    )


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "subjects",
        _id("subjects"),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.UniqueConstraint("code", name="uq_subjects_code"),
        schema=S,
    )
    op.create_table(
        "topics",
        _id("topics"),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("parent_id", UUID),
        sa.Column("code", sa.String(64)),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id", name="pk_topics"),
        _fk("subject_id", "subjects", "topics", "CASCADE"),
        _fk("parent_id", "topics", "topics", "SET NULL"),
        schema=S,
    )
    op.create_index("ix_topics_subject_id", "topics", ["subject_id"], schema=S)
    op.create_index("ix_topics_parent_id", "topics", ["parent_id"], schema=S)
    op.create_table(
        "question_types",
        _id("question_types"),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("generation_prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("rules", JSONB, nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_question_types"),
        sa.UniqueConstraint("code", name="uq_question_types_code"),
        schema=S,
    )
    op.create_table(
        "paths",
        _id("paths"),
        sa.Column("subject_id", UUID, nullable=False),
        sa.Column("language", sa.String(8), nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_paths"),
        _fk("subject_id", "subjects", "paths", "CASCADE"),
        sa.UniqueConstraint("subject_id", "language", name="uq_paths_subject_id"),
        schema=S,
    )
    op.create_index("ix_paths_subject_id", "paths", ["subject_id"], schema=S)
    op.create_table(
        "units",
        _id("units"),
        sa.Column("path_id", UUID, nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_units"),
        _fk("path_id", "paths", "units", "CASCADE"),
        schema=S,
    )
    op.create_index("ix_units_path_id", "units", ["path_id"], schema=S)
    op.create_table(
        "lessons",
        _id("lessons"),
        sa.Column("unit_id", UUID, nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("topic_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("type_ids", JSONB, nullable=False, server_default="[]"),
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("legendary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_lessons"),
        _fk("unit_id", "units", "lessons", "CASCADE"),
        schema=S,
    )
    op.create_index("ix_lessons_unit_id", "lessons", ["unit_id"], schema=S)
    op.create_table(
        "blueprints",
        _id("blueprints"),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("kind", sa.String(12), nullable=False),
        sa.Column("sections", JSONB, nullable=False),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("source_id", UUID),
        sa.PrimaryKeyConstraint("id", name="pk_blueprints"),
        sa.UniqueConstraint("code", "version", name="uq_blueprints_code"),
        schema=S,
    )
    op.create_table(
        "question_bases",
        _id("question_bases"),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("names", JSONB, nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer()),
        sa.Column("provenance", sa.Text(), nullable=False, server_default=""),
        sa.Column("license_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_question_bases"),
        sa.UniqueConstraint("code", name="uq_question_bases_code"),
        schema=S,
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("actor", sa.String(64)),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("entity", sa.String(20), nullable=False),
        sa.Column("entity_id", UUID),
        sa.Column("before", JSONB),
        sa.Column("after", JSONB),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
        schema=S,
    )
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"], schema=S)


def downgrade() -> None:
    for t in (
        "audit_log",
        "question_bases",
        "blueprints",
        "lessons",
        "units",
        "paths",
        "question_types",
        "topics",
        "subjects",
    ):
        op.drop_table(t, schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
