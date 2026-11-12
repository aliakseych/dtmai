"""exam_info: seeded_key ledger (deleted seed rows stay deleted), convention-aligned CHECK names

Revision ID: exam_info_0002
Revises: exam_info_0001
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op

revision = "exam_info_0002"
down_revision = "exam_info_0001"
branch_labels = None
depends_on = None

S = "exam_info"

# Migration 0001 passed full names through the ck naming convention, doubling the prefix.
# (table, name in the database, name the convention derives from the ORM short name)
_SHORT = (
    ("exam_profile", "ck_exam_profile_taper", "taper"),
    ("exam_profile_section", "ck_exam_section_iq_slot", "iq_slot"),
    ("exam_profile_section", "ck_exam_section_iq_not_exemptible", "iq_not_exemptible"),
    ("exam_profile_section", "ck_exam_section_role", "role"),
    ("exam_certificate_rule", "ck_exam_cert_rule_fraction", "fraction"),
    ("exam_certificate_rule", "ck_exam_cert_rule_active_min", "active_min"),
    ("exam_certificate_rule", "ck_exam_cert_rule_type", "type"),
    ("exam_event", "ck_exam_event_range", "range"),
    ("exam_event", "ck_exam_event_kind", "kind"),
)
RENAMES = tuple((t, f"ck_{t}_{full}", f"ck_{t}_{short}") for t, full, short in _SHORT)


def upgrade() -> None:
    op.create_table(
        "seeded_key",
        sa.Column("kind", sa.String(16), primary_key=True),
        sa.Column("key", sa.String(96), primary_key=True),
        schema=S,
    )
    for table, old, new in RENAMES:
        op.execute(f'ALTER TABLE {S}.{table} RENAME CONSTRAINT "{old}" TO "{new}"')


def downgrade() -> None:
    for table, old, new in RENAMES:
        op.execute(f'ALTER TABLE {S}.{table} RENAME CONSTRAINT "{new}" TO "{old}"')
    op.drop_table("seeded_key", schema=S)
