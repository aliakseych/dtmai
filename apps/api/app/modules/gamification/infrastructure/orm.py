import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "gamification"


class UserStatsRow(Base):
    __tablename__ = "user_stats"
    __table_args__ = (Index("ix_user_stats_target_lyceum_id", "target_lyceum_id"), {"schema": SCHEMA})

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    xp_total: Mapped[int] = mapped_column(Integer, default=0)
    gems: Mapped[int] = mapped_column(Integer, default=0)
    streak_current: Mapped[int] = mapped_column(Integer, default=0)
    streak_longest: Mapped[int] = mapped_column(Integer, default=0)
    streak_last_day: Mapped[date | None] = mapped_column(Date)
    streak_freezes: Mapped[int] = mapped_column(Integer, default=0)
    hearts: Mapped[int] = mapped_column(Integer)
    hearts_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    correct_total: Mapped[int] = mapped_column(Integer, default=0)
    mocks_submitted: Mapped[int] = mapped_column(Integer, default=0)
    daily_goal_xp: Mapped[int] = mapped_column(Integer, default=20, server_default="20")
    league_tier: Mapped[int] = mapped_column(Integer, default=0)
    # Soft reference to the identity profile, refreshed lazily (no cross-schema FK).
    target_lyceum_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    display_name: Mapped[str] = mapped_column(String(200), default="")
    profile_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class XpLogRow(Base):
    __tablename__ = "xp_log"
    __table_args__ = (
        UniqueConstraint("user_id", "ref", name="uq_xp_log_user_ref"),
        Index("ix_xp_log_user_day", "user_id", "day"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    day: Mapped[date] = mapped_column(Date)
    amount: Mapped[int] = mapped_column(Integer)
    ref: Mapped[str] = mapped_column(String(120))


class GemLedgerRow(Base):
    __tablename__ = "gem_ledger"
    __table_args__ = (
        UniqueConstraint("user_id", "ref", name="uq_gem_ledger_user_ref"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    delta: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(40))
    ref: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEventRow(Base):
    __tablename__ = "processed_events"
    __table_args__ = {"schema": SCHEMA}

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    handler: Mapped[str] = mapped_column(String(40), primary_key=True)


class QuestTemplateRow(Base):
    __tablename__ = "quest_templates"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), unique=True)
    metric: Mapped[str] = mapped_column(String(40))
    target: Mapped[int] = mapped_column(Integer)
    reward_gems: Mapped[int] = mapped_column(Integer, default=0)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)  # per UI locale
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserQuestRow(Base):
    __tablename__ = "user_quests"
    __table_args__ = (
        UniqueConstraint("user_id", "day", "template_id", name="uq_user_quests_day"),
        Index("ix_user_quests_user_day", "user_id", "day"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    day: Mapped[date] = mapped_column(Date)
    template_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    # Snapshot so later template edits never change today's quest.
    code: Mapped[str] = mapped_column(String(60))
    metric: Mapped[str] = mapped_column(String(40))
    title: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[int] = mapped_column(Integer)
    reward_gems: Mapped[int] = mapped_column(Integer, default=0)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LeagueTierRow(Base):
    __tablename__ = "league_tiers"
    __table_args__ = {"schema": SCHEMA}

    idx: Mapped[int] = mapped_column(Integer, primary_key=True)  # 0 = lowest
    code: Mapped[str] = mapped_column(String(30), unique=True)
    name: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    cohort_size: Mapped[int] = mapped_column(Integer, default=30)
    promote_count: Mapped[int] = mapped_column(Integer, default=5)
    demote_count: Mapped[int] = mapped_column(Integer, default=5)


class LeagueCohortRow(Base):
    __tablename__ = "league_cohorts"
    __table_args__ = (
        Index("ix_league_cohorts_week_tier", "week_start", "tier_idx"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date)
    tier_idx: Mapped[int] = mapped_column(Integer)
    settled: Mapped[bool] = mapped_column(Boolean, default=False)


class LeagueMemberRow(Base):
    __tablename__ = "league_members"
    __table_args__ = (
        UniqueConstraint("user_id", "week_start", name="uq_league_members_user_week"),
        {"schema": SCHEMA},
    )

    cohort_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{SCHEMA}.league_cohorts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    joined_order: Mapped[int] = mapped_column(Integer, default=0)
    final_rank: Mapped[int | None] = mapped_column(Integer)
    outcome: Mapped[str | None] = mapped_column(String(10))


class FollowRow(Base):
    __tablename__ = "follows"
    __table_args__ = {"schema": SCHEMA}

    follower_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    followee_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AchievementDefRow(Base):
    __tablename__ = "achievement_defs"
    __table_args__ = {"schema": SCHEMA}

    code: Mapped[str] = mapped_column(String(60), primary_key=True)
    metric: Mapped[str] = mapped_column(String(40))
    threshold: Mapped[int] = mapped_column(Integer)
    reward_gems: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserAchievementRow(Base):
    __tablename__ = "user_achievements"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    code: Mapped[str] = mapped_column(String(60), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GameConfigRow(Base):
    __tablename__ = "game_config"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    values: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
