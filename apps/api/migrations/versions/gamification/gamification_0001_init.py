"""gamification: stats, xp, gems, quests, leagues, follows, achievements, config

Revision ID: gamification_0001
Revises:
Create Date: 2026-11-12
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "gamification_0001"
down_revision = None
branch_labels = ("gamification",)
depends_on = None

S = "gamification"
_UUID = sa.Uuid()


def _ts(name: str, nullable: bool = False, default: bool = True) -> sa.Column:
    return sa.Column(
        name, sa.DateTime(timezone=True), nullable=nullable,
        server_default=sa.func.now() if default else None,
    )


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {S}")
    op.create_table(
        "user_stats",
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("xp_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("gems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_current", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_longest", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("streak_last_day", sa.Date()),
        sa.Column("streak_freezes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hearts", sa.Integer(), nullable=False),
        _ts("hearts_updated_at", default=False),
        sa.Column("lessons_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mocks_submitted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("league_tier", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_lyceum_id", _UUID),
        sa.Column("display_name", sa.String(200), nullable=False, server_default=""),
        _ts("profile_synced_at", nullable=True, default=False),
        sa.PrimaryKeyConstraint("user_id", name="pk_user_stats"),
        schema=S,
    )
    op.create_index("ix_user_stats_target_lyceum_id", "user_stats", ["target_lyceum_id"], schema=S)

    op.create_table(
        "xp_log",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("ref", sa.String(120), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_xp_log"),
        sa.UniqueConstraint("user_id", "ref", name="uq_xp_log_user_ref"),
        schema=S,
    )
    op.create_index("ix_xp_log_user_day", "xp_log", ["user_id", "day"], schema=S)

    op.create_table(
        "gem_ledger",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(40), nullable=False),
        sa.Column("ref", sa.String(120), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_gem_ledger"),
        sa.UniqueConstraint("user_id", "ref", name="uq_gem_ledger_user_ref"),
        schema=S,
    )
    op.create_index("ix_gem_ledger_user_id", "gem_ledger", ["user_id"], schema=S)

    op.create_table(
        "processed_events",
        sa.Column("event_id", _UUID, nullable=False),
        sa.Column("handler", sa.String(40), nullable=False),
        sa.PrimaryKeyConstraint("event_id", "handler", name="pk_processed_events"),
        schema=S,
    )

    quest_templates = op.create_table(
        "quest_templates",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("reward_gems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id", name="pk_quest_templates"),
        sa.UniqueConstraint("code", name="uq_quest_templates_code"),
        schema=S,
    )

    op.create_table(
        "user_quests",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("template_id", _UUID, nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("title", sa.JSON(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("reward_gems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reward_xp", sa.Integer(), nullable=False, server_default="0"),
        _ts("completed_at", nullable=True, default=False),
        sa.PrimaryKeyConstraint("id", name="pk_user_quests"),
        sa.UniqueConstraint("user_id", "day", "template_id", name="uq_user_quests_day"),
        schema=S,
    )
    op.create_index("ix_user_quests_user_day", "user_quests", ["user_id", "day"], schema=S)

    league_tiers = op.create_table(
        "league_tiers",
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.JSON(), nullable=False),
        sa.Column("cohort_size", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("promote_count", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("demote_count", sa.Integer(), nullable=False, server_default="5"),
        sa.PrimaryKeyConstraint("idx", name="pk_league_tiers"),
        sa.UniqueConstraint("code", name="uq_league_tiers_code"),
        schema=S,
    )

    op.create_table(
        "league_cohorts",
        sa.Column("id", _UUID, nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("tier_idx", sa.Integer(), nullable=False),
        sa.Column("settled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.PrimaryKeyConstraint("id", name="pk_league_cohorts"),
        schema=S,
    )
    op.create_index("ix_league_cohorts_week_tier", "league_cohorts", ["week_start", "tier_idx"], schema=S)

    op.create_table(
        "league_members",
        sa.Column("cohort_id", _UUID, nullable=False),
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("joined_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("final_rank", sa.Integer()),
        sa.Column("outcome", sa.String(10)),
        sa.PrimaryKeyConstraint("cohort_id", "user_id", name="pk_league_members"),
        sa.ForeignKeyConstraint(
            ["cohort_id"], [f"{S}.league_cohorts.id"],
            name="fk_league_members_cohort_id_league_cohorts", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("user_id", "week_start", name="uq_league_members_user_week"),
        schema=S,
    )

    op.create_table(
        "follows",
        sa.Column("follower_id", _UUID, nullable=False),
        sa.Column("followee_id", _UUID, nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("follower_id", "followee_id", name="pk_follows"),
        schema=S,
    )
    op.create_index("ix_follows_followee_id", "follows", ["followee_id"], schema=S)

    achievement_defs = op.create_table(
        "achievement_defs",
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("metric", sa.String(40), nullable=False),
        sa.Column("threshold", sa.Integer(), nullable=False),
        sa.Column("reward_gems", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("code", name="pk_achievement_defs"),
        schema=S,
    )

    op.create_table(
        "user_achievements",
        sa.Column("user_id", _UUID, nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        _ts("earned_at"),
        sa.PrimaryKeyConstraint("user_id", "code", name="pk_user_achievements"),
        schema=S,
    )

    game_config = op.create_table(
        "game_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_game_config"),
        schema=S,
    )

    op.bulk_insert(game_config, [{"id": 1, "values": {
        "heart_refill_minutes": 60, "xp_daily_cap": 600, "xp_session_cap": 150, "xp_per_item_cap": 10,
        "mock_xp": 50, "freeze_cost_gems": 50, "freeze_max": 2, "review_correct_per_heart": 3,
        "daily_quest_count": 3,
    }}])

    tiers = [("bronze", "Bronza", "Бронза", "Bronze"), ("silver", "Kumush", "Серебро", "Silver"),
             ("gold", "Oltin", "Золото", "Gold"), ("platinum", "Platina", "Платина", "Platinum"),
             ("diamond", "Olmos", "Алмаз", "Diamond")]
    op.bulk_insert(league_tiers, [
        {"idx": i, "code": c, "name": {"uz-Latn": u, "uz-Cyrl": u, "ru": r, "en": e},
         "cohort_size": 30, "promote_count": 5, "demote_count": 0 if i == 0 else 5}
        for i, (c, u, r, e) in enumerate(tiers)
    ])

    def t(uz: str, ru: str, en: str) -> dict[str, str]:
        return {"uz-Latn": uz, "uz-Cyrl": uz, "ru": ru, "en": en}

    quests = [
        ("earn_50_xp", "xp_earned", 50, 5, 0, t("50 XP to'plang", "Заработайте 50 XP", "Earn 50 XP")),
        ("earn_100_xp", "xp_earned", 100, 10, 0, t("100 XP to'plang", "Заработайте 100 XP", "Earn 100 XP")),
        ("complete_1_lesson", "lessons_completed", 1, 5, 0, t("1 ta dars tugating", "Пройдите 1 урок", "Complete 1 lesson")),
        ("complete_3_lessons", "lessons_completed", 3, 10, 0, t("3 ta dars tugating", "Пройдите 3 урока", "Complete 3 lessons")),
        ("correct_15", "correct_answers", 15, 5, 0, t("15 ta to'g'ri javob", "15 правильных ответов", "Get 15 answers right")),
        ("perfect_session", "perfect_sessions", 1, 10, 0, t("Xatosiz dars", "Урок без ошибок", "Finish a lesson with no mistakes")),
        ("review_session", "review_sessions", 1, 5, 0, t("Xatolar ustida ishlang", "Повторите ошибки", "Review your mistakes")),
    ]
    op.bulk_insert(quest_templates, [
        {"id": uuid.uuid4(), "code": c, "metric": m, "target": n, "reward_gems": g, "reward_xp": x,
         "title": ti, "active": True}
        for c, m, n, g, x, ti in quests
    ])

    ach = [
        ("streak_7", "streak_longest", 7, 20, t("7 kunlik seriya", "Серия 7 дней", "7-day streak")),
        ("streak_30", "streak_longest", 30, 100, t("30 kunlik seriya", "Серия 30 дней", "30-day streak")),
        ("xp_1000", "xp_total", 1000, 20, t("1000 XP", "1000 XP", "1000 XP")),
        ("xp_10000", "xp_total", 10000, 100, t("10 000 XP", "10 000 XP", "10,000 XP")),
        ("lessons_10", "lessons_completed", 10, 20, t("10 ta dars", "10 уроков", "10 lessons")),
        ("correct_500", "correct_total", 500, 50, t("500 to'g'ri javob", "500 правильных ответов", "500 correct answers")),
        ("first_mock", "mocks_submitted", 1, 20, t("Birinchi mock", "Первый пробный экзамен", "First mock exam")),
    ]
    op.bulk_insert(achievement_defs, [
        {"code": c, "metric": m, "threshold": n, "reward_gems": g, "title": ti, "active": True}
        for c, m, n, g, ti in ach
    ])


def downgrade() -> None:
    op.execute(f"DROP SCHEMA IF EXISTS {S} CASCADE")
