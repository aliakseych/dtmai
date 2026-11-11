"""billing: plans, subscriptions, invoices (+ seed free and premium_1m plans)

Revision ID: billing_0001
Revises:
Create Date: 2026-11-11
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "billing_0001"
down_revision = None
branch_labels = ("billing",)
depends_on = None

S = "billing"


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "plans",
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("names", sa.JSON(), nullable=False),
        sa.Column("price_uzs", sa.BigInteger(), nullable=False),
        sa.Column("period_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("features", postgresql.ARRAY(sa.String(60)), nullable=False, server_default="{}"),
        sa.Column("limits", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("code", name="pk_plans"),
        sa.CheckConstraint("price_uzs >= 0", name="ck_plans_price"),
        sa.CheckConstraint("period_months IN (1, 3, 12)", name="ck_plans_period"),
        schema=S,
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_code", sa.String(40), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("source", sa.String(12), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_subscriptions"),
        sa.ForeignKeyConstraint(["plan_code"], [f"{S}.plans.code"], name="fk_subscriptions_plan_code_plans"),
        schema=S,
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], schema=S)
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seq", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_code", sa.String(40), nullable=False),
        sa.Column("period_months", sa.Integer(), nullable=False),
        sa.Column("amount_uzs", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("click_trans_id", sa.String(40)),
        sa.Column("click_paydoc_id", sa.String(40)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("canceled_at", sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint("id", name="pk_invoices"),
        sa.ForeignKeyConstraint(["plan_code"], [f"{S}.plans.code"], name="fk_invoices_plan_code_plans"),
        sa.UniqueConstraint("seq", name="uq_invoices_seq"),
        sa.UniqueConstraint("click_trans_id", name="uq_invoices_click_trans_id"),
        schema=S,
    )
    op.create_index("ix_invoices_user_id", "invoices", ["user_id"], schema=S)

    plans = sa.table(
        "plans",
        sa.column("code", sa.String),
        sa.column("names", sa.JSON),
        sa.column("price_uzs", sa.BigInteger),
        sa.column("period_months", sa.Integer),
        sa.column("features", postgresql.ARRAY(sa.String)),
        sa.column("limits", sa.JSON),
        sa.column("active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
        schema=S,
    )
    op.bulk_insert(
        plans,
        [
            {
                "code": "free",
                "names": {"uz-Latn": "Bepul", "uz-Cyrl": "Бепул", "ru": "Бесплатно", "en": "Free"},
                "price_uzs": 0, "period_months": 1, "features": [],
                "limits": {"hearts_max": 5, "ai_explanations_per_day": 3},
                "active": True, "sort_order": 0,
            },
            {
                "code": "premium_1m",
                "names": {
                    "uz-Latn": "Premium", "uz-Cyrl": "Премиум", "ru": "Премиум", "en": "Premium",
                },
                "price_uzs": 49000, "period_months": 1,
                "features": [
                    "unlimited_hearts", "ai_tutor", "personal_mock", "private_analytics",
                    "personal_review",
                ],
                "limits": {"ai_explanations_per_day": -1},
                "active": True, "sort_order": 10,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("invoices", schema=S)
    op.drop_table("subscriptions", schema=S)
    op.drop_table("plans", schema=S)
    op.execute(f"DROP SCHEMA IF EXISTS {S}")
