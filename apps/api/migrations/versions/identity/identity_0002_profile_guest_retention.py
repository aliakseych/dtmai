"""identity: city, subject_ids, last_seen_at (guest retention)

Revision ID: identity_0002
Revises: identity_0001
Create Date: 2026-11-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "identity_0002"
down_revision = "identity_0001"
branch_labels = None
depends_on = None

S = "identity"


def upgrade() -> None:
    op.add_column("users", sa.Column("city", sa.String(100)), schema=S)
    op.add_column(
        "users",
        sa.Column(
            "subject_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        schema=S,
    )
    op.add_column(
        "users",
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        schema=S,
    )
    op.create_index(
        "ix_users_guest_last_seen",
        "users",
        ["last_seen_at"],
        schema=S,
        postgresql_where=sa.text("roles = '{guest}'"),
    )
    op.create_index("ix_users_target_lyceum_id", "users", ["target_lyceum_id"], schema=S)


def downgrade() -> None:
    op.drop_index("ix_users_target_lyceum_id", table_name="users", schema=S)
    op.drop_index("ix_users_guest_last_seen", table_name="users", schema=S)
    op.drop_column("users", "last_seen_at", schema=S)
    op.drop_column("users", "subject_ids", schema=S)
    op.drop_column("users", "city", schema=S)
