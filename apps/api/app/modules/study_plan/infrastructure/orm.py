import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "study_plan"


class PlanRow(Base):
    __tablename__ = "plan"
    __table_args__ = ({"schema": SCHEMA},)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSON)
    plan_end: Mapped[date | None] = mapped_column(Date)
    version: Mapped[int] = mapped_column(Integer, default=1)
    last_replanned_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskRow(Base):
    __tablename__ = "task"
    __table_args__ = (
        CheckConstraint("kind in ('lesson','drill','review','mock','rush')", name="kind"),
        CheckConstraint("status in ('todo','done','missed')", name="status"),
        Index("ix_task_plan_id_day", "plan_id", "day"),
        Index("ix_task_plan_id_status_day", "plan_id", "status", "day"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.plan.id", ondelete="CASCADE"))
    day: Mapped[date] = mapped_column(Date)
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    target: Mapped[dict[str, Any]] = mapped_column(JSON)
    est_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="todo")
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Event id that completed the task: makes event redelivery a no-op.
    source_ref: Mapped[uuid.UUID | None] = mapped_column(Uuid)


class DailySetRow(Base):
    __tablename__ = "daily_set"
    __table_args__ = (
        PrimaryKeyConstraint("user_id", "day", name="pk_daily_set"),
        {"schema": SCHEMA},
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    day: Mapped[date] = mapped_column(Date)
    question_ids: Mapped[list[str]] = mapped_column(JSON)
    answered: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
