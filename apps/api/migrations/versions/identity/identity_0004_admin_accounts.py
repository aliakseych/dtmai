"""identity: telegram username, account status, system accounts

Revision ID: identity_0004
Revises: identity_0003
Create Date: 2026-11-20
"""

import sqlalchemy as sa
from alembic import op

revision = "identity_0004"
down_revision = "identity_0003"
branch_labels = None
depends_on = None

S = "identity"


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_username", sa.String(64), nullable=True), schema=S)
    op.add_column(
        "users",
        sa.Column("status", sa.String(10), nullable=False, server_default="active"),
        schema=S,
    )
    op.add_column(
        "users",
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        schema=S,
    )


def downgrade() -> None:
    op.drop_column("users", "is_system", schema=S)
    op.drop_column("users", "status", schema=S)
    op.drop_column("users", "telegram_username", schema=S)
