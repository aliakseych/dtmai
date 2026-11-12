"""lyceums: campus map, building floor plans, specializations, special offerings

Revision ID: lyceums_0007
Revises: lyceums_0006
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "lyceums_0007"
down_revision = "lyceums_0006"
branch_labels = None
depends_on = None

S = "lyceums"
COLUMNS = (
    ("campus_map", "{}"),
    ("buildings", "[]"),
    ("specializations", "[]"),
    ("offerings", "[]"),
)


def upgrade() -> None:
    for name, default in COLUMNS:
        op.add_column(
            "lyceums",
            sa.Column(name, sa.JSON(), nullable=False, server_default=default),
            schema=S,
        )


def downgrade() -> None:
    for name, _ in reversed(COLUMNS):
        op.drop_column("lyceums", name, schema=S)
