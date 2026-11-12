"""labeling: drop duplicate 'claim' activity rows (cockpit re-claim storm)

Keeps the earliest claim per (labeler, question).

Revision ID: labeling_0003
Revises: labeling_0002
Create Date: 2026-11-21
"""

from alembic import op

revision = "labeling_0003"
down_revision = "labeling_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM labeling.activity a
        USING (
            SELECT id,
                   row_number() OVER (
                       PARTITION BY actor_user_id, question_id ORDER BY created_at, id
                   ) AS rn
            FROM labeling.activity
            WHERE action = 'claim' AND question_id IS NOT NULL
        ) d
        WHERE a.id = d.id AND d.rn > 1
        """
    )


def downgrade() -> None:
    pass
