"""lyceums: admission plan seats, contacts, seed document matches

Revision ID: lyceums_0005
Revises: lyceums_0004
Create Date: 2026-12-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "lyceums_0005"
down_revision = "lyceums_0004"
branch_labels = None
depends_on = None

S = "lyceums"


def upgrade() -> None:
    op.create_table(
        "lyceum_admission_plan",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lyceum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("direction_code", sa.String(20), nullable=False),
        sa.Column("language_name", sa.String(40), nullable=True),
        sa.Column("seats_uz", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seats_ru", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seats_qq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seats_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(10), nullable=False, server_default="seed"),
        sa.PrimaryKeyConstraint("id", name="pk_lyceum_admission_plan"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"],
            [f"{S}.lyceums.id"],
            ondelete="CASCADE",
            name="fk_lyceum_admission_plan_lyceum_id",
        ),
        schema=S,
    )
    op.create_index(
        "ix_lyceum_admission_plan_lyceum_id", "lyceum_admission_plan", ["lyceum_id"], schema=S
    )
    op.execute(
        f"CREATE UNIQUE INDEX uq_lyceum_admission_plan_key ON {S}.lyceum_admission_plan "
        "(lyceum_id, year, direction_code, COALESCE(language_name, ''))"
    )
    op.create_table(
        "lyceum_contact",
        sa.Column("lyceum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phones", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("telegram", sa.Text(), nullable=True),
        sa.Column("source", sa.String(10), nullable=False, server_default="seed"),
        sa.PrimaryKeyConstraint("lyceum_id", name="pk_lyceum_contact"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"],
            [f"{S}.lyceums.id"],
            ondelete="CASCADE",
            name="fk_lyceum_contact_lyceum_id",
        ),
        schema=S,
    )
    op.create_table(
        "lyceum_seed_match",
        sa.Column("kind", sa.String(10), nullable=False),
        sa.Column("seed_ref", sa.Integer(), nullable=False),
        sa.Column("lyceum_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(10), nullable=False, server_default="auto"),
        sa.PrimaryKeyConstraint("kind", "seed_ref", name="pk_lyceum_seed_match"),
        sa.ForeignKeyConstraint(
            ["lyceum_id"],
            [f"{S}.lyceums.id"],
            ondelete="SET NULL",
            name="fk_lyceum_seed_match_lyceum_id",
        ),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("lyceum_seed_match", schema=S)
    op.drop_table("lyceum_contact", schema=S)
    op.execute(f"DROP INDEX {S}.uq_lyceum_admission_plan_key")
    op.drop_table("lyceum_admission_plan", schema=S)
