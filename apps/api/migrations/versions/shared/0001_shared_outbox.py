"""shared: transactional outbox

Revision ID: shared_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op

revision = "shared_0001"
down_revision = None
branch_labels = ("shared",)
depends_on = None

S = "shared"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_outbox"),
        schema=S,
    )
    op.create_index("ix_outbox_name", "outbox", ["name"], schema=S)
    op.create_index(
        "ix_outbox_pending",
        "outbox",
        ["occurred_at"],
        schema=S,
        postgresql_where=sa.text("dispatched_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table("outbox", schema=S)
