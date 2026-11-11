"""notify: preferences, devices, telegram chats, link codes, activity, deliveries

Revision ID: notify_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "notify_0001"
down_revision = None
branch_labels = ("notify",)
depends_on = None

S = "notify"


def _uuid(name: str, **kw: bool) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(name, postgresql.UUID(as_uuid=True), **kw)


def _created() -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "preferences",
        _uuid("user_id", nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("channels", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("kinds", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("quiet_start", sa.Time(), nullable=False, server_default="22:00"),
        sa.Column("quiet_end", sa.Time(), nullable=False, server_default="08:00"),
        sa.Column("max_per_day", sa.Integer(), nullable=False, server_default="2"),
        sa.PrimaryKeyConstraint("user_id", name="pk_preferences"),
        schema=S,
    )
    op.create_table(
        "devices",
        sa.Column("token", sa.Text(), nullable=False),
        _uuid("user_id", nullable=False),
        sa.Column("platform", sa.String(10), nullable=False),
        _created(),
        sa.PrimaryKeyConstraint("token", name="pk_devices"),
        schema=S,
    )
    op.create_index("ix_devices_user_id", "devices", ["user_id"], schema=S)
    op.create_table(
        "telegram_chats",
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        _uuid("user_id", nullable=True),
        sa.Column("locale", sa.String(10), nullable=False, server_default="uz-Latn"),
        _created(),
        sa.PrimaryKeyConstraint("chat_id", name="pk_telegram_chats"),
        schema=S,
    )
    op.create_index("ix_telegram_chats_user_id", "telegram_chats", ["user_id"], schema=S)
    op.create_table(
        "link_codes",
        sa.Column("code", sa.String(64), nullable=False),
        _uuid("user_id", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_link_codes"),
        schema=S,
    )
    op.create_table(
        "activity",
        _uuid("user_id", nullable=False),
        sa.Column("last_day", sa.Date(), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("user_id", name="pk_activity"),
        schema=S,
    )
    op.create_table(
        "deliveries",
        _uuid("id", nullable=False),
        _uuid("user_id", nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("channel", sa.String(10), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        _created(),
        sa.PrimaryKeyConstraint("id", name="pk_deliveries"),
        schema=S,
    )
    op.create_index("ix_deliveries_user_id", "deliveries", ["user_id"], schema=S)
    op.create_index("ix_deliveries_day", "deliveries", ["day"], schema=S)


def downgrade() -> None:
    for t in ("deliveries", "activity", "link_codes", "telegram_chats", "devices", "preferences"):
        op.drop_table(t, schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
