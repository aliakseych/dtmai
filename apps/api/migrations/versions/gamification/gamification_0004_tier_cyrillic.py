"""gamification: uz-Cyrl league tier names (were copies of uz-Latn)

Revision ID: gamification_0004
Revises: gamification_0003
Create Date: 2026-11-15
"""

import sqlalchemy as sa
from alembic import op

revision = "gamification_0004"
down_revision = "gamification_0003"
branch_labels = None
depends_on = None

TIERS_CYRL = {
    "bronze": "Бронза",
    "silver": "Кумуш",
    "gold": "Олтин",
    "platinum": "Платина",
    "diamond": "Олмос",
}


def upgrade() -> None:
    """Idempotent: only rows whose uz-Cyrl is missing, empty or equal to uz-Latn are touched."""
    bind = op.get_bind()
    for code, cyrl in TIERS_CYRL.items():
        bind.execute(
            sa.text(
                """
                UPDATE gamification.league_tiers
                SET name = CAST(jsonb_set(CAST(name AS jsonb), '{uz-Cyrl}', to_jsonb(CAST(:c AS text))) AS json)
                WHERE code = :code
                  AND COALESCE(NULLIF(name->>'uz-Cyrl', ''), name->>'uz-Latn') = COALESCE(name->>'uz-Latn', '')
                """
            ),
            {"c": cyrl, "code": code},
        )


def downgrade() -> None:
    """Data-only fix; nothing to revert."""
