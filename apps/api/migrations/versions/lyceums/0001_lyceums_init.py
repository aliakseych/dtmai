"""lyceums: lyceums, languages, yearly stats, import runs

Revision ID: lyceums_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "lyceums_0001"
down_revision = None
branch_labels = ("lyceums",)
depends_on = None

S = "lyceums"


def _uuid(name: str, **kw: object) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(name, postgresql.UUID(as_uuid=True), **kw)  # type: ignore[arg-type]


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    for table in ("lyceums", "education_languages"):
        op.create_table(
            table,
            _uuid("id", nullable=False),
            sa.Column("external_id", sa.BigInteger(), nullable=False),
            sa.Column("code", sa.String(20), nullable=False),
            sa.Column("name_uz", sa.Text(), nullable=False),
            sa.Column("name_en", sa.Text(), nullable=False, server_default=""),
            sa.Column("name_ru", sa.Text(), nullable=False, server_default=""),
            sa.PrimaryKeyConstraint("id", name=f"pk_{table}"),
            sa.UniqueConstraint("external_id", name=f"uq_{table}_external_id"),
            schema=S,
        )
    op.create_table(
        "yearly_stats",
        _uuid("id", nullable=False),
        _uuid("lyceum_id", nullable=False),
        _uuid("language_id", nullable=False),
        sa.Column("speciality_code", sa.String(20), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quota", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applications", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passing_score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_yearly_stats"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"], [f"{S}.lyceums.id"], ondelete="CASCADE", name="fk_yearly_stats_lyceum"
        ),
        sa.ForeignKeyConstraint(
            ["language_id"], [f"{S}.education_languages.id"], ondelete="CASCADE",
            name="fk_yearly_stats_language",
        ),
        sa.UniqueConstraint(
            "lyceum_id", "language_id", "speciality_code", "year", name="uq_yearly_stats_key"
        ),
        schema=S,
    )
    op.create_index("ix_yearly_stats_lyceum_id", "yearly_stats", ["lyceum_id"], schema=S)
    op.create_index("ix_yearly_stats_year", "yearly_stats", ["year"], schema=S)
    op.create_table(
        "import_runs",
        _uuid("id", nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        _uuid("requested_by", nullable=True),
        sa.Column("counts", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_import_runs"),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("import_runs", schema=S)
    op.drop_table("yearly_stats", schema=S)
    op.drop_table("education_languages", schema=S)
    op.drop_table("lyceums", schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
