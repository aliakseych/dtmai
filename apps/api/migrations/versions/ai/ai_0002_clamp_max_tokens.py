"""ai: clamp route max_tokens to the API limit (32000)

The original seed stored 32768 for extract/0, which RouteIO (le=32000) rejects, so the
admin routes list failed to serialize.

Revision ID: ai_0002
Revises: ai_0001
Create Date: 2026-11-21
"""

from alembic import op

revision = "ai_0002"
down_revision = "ai_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE ai.model_routes SET max_tokens = 32000 WHERE max_tokens > 32000")


def downgrade() -> None:
    pass
