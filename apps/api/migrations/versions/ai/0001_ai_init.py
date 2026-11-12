"""ai: model routes, limits, cost ledger, explanation usage

Revision ID: ai_0001
Revises:
Create Date: 2026-11-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ai_0001"
down_revision = None
branch_labels = ("ai",)
depends_on = None

S = "ai"
UUID = postgresql.UUID(as_uuid=True)

# Model routes seed (micro-USD per 1M tokens); tune in admin.
ROUTES = [
    # Slugs/prices verified against openrouter.ai/api/v1/models (USD/Mtok × 1e6 = micro).
    ("extract", 0, "google/gemini-3.7-flash", 0.1, 32000, 750_000, 3_750_000),
    ("solve", 0, "google/gemini-3.7-flash", 0.1, 4096, 750_000, 3_750_000),
    ("solve", 1, "deepseek/deepseek-v4-pro", 0.1, 4096, 955_260, 1_910_520),
    ("solve", 2, "anthropic/claude-haiku-5.5", 0.1, 4096, 100_000, 500_000),
    ("judge", 0, "anthropic/claude-haiku-5.5", 0.0, 1024, 100_000, 500_000),
    ("judge", 1, "anthropic/claude-sonnet-5.5", 0.0, 2048, 2_000_000, 10_000_000),
    ("explain", 0, "google/gemini-3.7-flash", 0.3, 1500, 750_000, 3_750_000),
    ("tutor", 0, "google/gemini-3.7-flash", 0.4, 1500, 750_000, 3_750_000),
    ("generate", 0, "anthropic/claude-sonnet-5.5", 0.8, 8192, 2_000_000, 10_000_000),
]


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    routes = op.create_table(
        "model_routes",
        sa.Column("task", sa.String(20), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("price_in_micro_per_mtok", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("price_out_micro_per_mtok", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_by", UUID),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("task", "slot", name="pk_model_routes"),
        schema=S,
    )
    limits = op.create_table(
        "limits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("daily_spend_cap_micro", sa.BigInteger(), nullable=False),
        sa.Column("user_daily_token_budget", sa.BigInteger(), nullable=False),
        sa.Column("updated_by", UUID),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id", name="pk_limits"),
        schema=S,
    )
    op.create_table(
        "ledger",
        sa.Column("id", UUID, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("user_id", UUID),
        sa.Column("purpose", sa.String(40), nullable=False),
        sa.Column("task", sa.String(20), nullable=False),
        sa.Column("model", sa.String(120), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_micro", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ref", sa.String(80)),
        sa.Column("error", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_ledger"),
        schema=S,
    )
    op.create_index("ix_ledger_day_user", "ledger", ["day", "user_id"], schema=S)
    op.create_index("ix_ledger_day_purpose", "ledger", ["day", "purpose"], schema=S)
    op.create_table(
        "explain_usage",
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("question_id", UUID, nullable=False),
        sa.PrimaryKeyConstraint("user_id", "day", "question_id", name="pk_explain_usage"),
        schema=S,
    )
    op.bulk_insert(
        routes,
        [
            {
                "task": t,
                "slot": s,
                "model": m,
                "temperature": temp,
                "max_tokens": mt,
                "price_in_micro_per_mtok": pi,
                "price_out_micro_per_mtok": po,
                "enabled": True,
            }
            for t, s, m, temp, mt, pi, po in ROUTES
        ],
    )
    # $20/day global cap, 200k tokens per user per day
    op.bulk_insert(
        limits,
        [
            {
                "id": 1,
                "enabled": True,
                "daily_spend_cap_micro": 20_000_000,
                "user_daily_token_budget": 200_000,
            }
        ],
    )


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
