"""identity: users, email codes, refresh tokens

Revision ID: identity_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "identity_0001"
down_revision = None
branch_labels = ("identity",)
depends_on = None

S = "identity"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(320)),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("password_hash", sa.Text()),
        sa.Column("telegram_id", sa.BigInteger()),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False, server_default="uz-Latn"),
        sa.Column(
            "roles", postgresql.ARRAY(sa.String(20)), nullable=False, server_default="{student}"
        ),
        sa.Column("target_lyceum_id", postgresql.UUID(as_uuid=True)),
        sa.Column("education_language_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
        sa.CheckConstraint(
            "email IS NOT NULL OR telegram_id IS NOT NULL OR 'guest' = ANY(roles)",
            name="ck_users_has_identity",
        ),
        schema=S,
    )
    op.create_table(
        "email_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consumed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name="pk_email_codes"),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{S}.users.id"], ondelete="CASCADE", name="fk_email_codes_user_id_users"
        ),
        schema=S,
    )
    op.create_index("ix_email_codes_user_id", "email_codes", ["user_id"], schema=S)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id", name="pk_refresh_tokens"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            [f"{S}.users.id"],
            ondelete="CASCADE",
            name="fk_refresh_tokens_user_id_users",
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        schema=S,
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], schema=S)


def downgrade() -> None:
    op.drop_table("refresh_tokens", schema=S)
    op.drop_table("email_codes", schema=S)
    op.drop_table("users", schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
