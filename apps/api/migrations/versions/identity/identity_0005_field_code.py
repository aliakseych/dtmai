"""identity: users.field_code (chosen field of study)

Revision ID: identity_0005
Revises: identity_0004
Create Date: 2026-11-21
"""

import sqlalchemy as sa
from alembic import op

revision = "identity_0005"
down_revision = "identity_0004"
branch_labels = None
depends_on = None

S = "identity"


def upgrade() -> None:
    op.add_column("users", sa.Column("field_code", sa.String(20), nullable=True), schema=S)


def downgrade() -> None:
    op.drop_column("users", "field_code", schema=S)
