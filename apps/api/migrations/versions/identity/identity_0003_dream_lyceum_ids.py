"""identity: ordered dream_lyceum_ids replaces target_lyceum_id; city holds a city code

Revision ID: identity_0003
Revises: identity_0002
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "identity_0003"
down_revision = "identity_0002"
branch_labels = None
depends_on = "lyceums_0003"

S = "identity"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "dream_lyceum_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        schema=S,
    )
    op.execute(
        "UPDATE identity.users SET dream_lyceum_ids = ARRAY[target_lyceum_id] "
        "WHERE target_lyceum_id IS NOT NULL"
    )
    op.drop_column("users", "target_lyceum_id", schema=S)
    op.alter_column("users", "city", type_=sa.String(50), schema=S)
    # Free-text cities become codes only when they already are one; the rest mean "any city".
    op.execute(
        "UPDATE identity.users SET city = NULL "
        "WHERE city IS NOT NULL AND city NOT IN (SELECT code FROM lyceums.cities)"
    )


def downgrade() -> None:
    op.alter_column("users", "city", type_=sa.String(100), schema=S)
    op.add_column("users", sa.Column("target_lyceum_id", postgresql.UUID(as_uuid=True)), schema=S)
    op.execute(
        "UPDATE identity.users SET target_lyceum_id = dream_lyceum_ids[1] "
        "WHERE cardinality(dream_lyceum_ids) > 0"
    )
    op.drop_column("users", "dream_lyceum_ids", schema=S)
