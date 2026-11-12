"""lyceums: field of study -> required subjects mapping

Revision ID: lyceums_0004
Revises: lyceums_0003
Create Date: 2026-11-21
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "lyceums_0004"
down_revision = "lyceums_0003"
branch_labels = None
depends_on = None

S = "lyceums"


def upgrade() -> None:
    op.create_table(
        "field_subjects",
        sa.Column("speciality_code", sa.String(20), nullable=False),
        sa.Column(
            "subject_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("speciality_code", name="pk_field_subjects"),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("field_subjects", schema=S)
