import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "learning"
NIL = uuid.UUID(int=0)  # stands in for "no topic" inside composite keys


class SessionRow(Base):
    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_status", "user_id", "status"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    mode: Mapped[str] = mapped_column(String(20))
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    language: Mapped[str] = mapped_column(String(10))
    question_ids: Mapped[list[str]] = mapped_column(JSON)  # snapshot taken at start
    status: Mapped[str] = mapped_column(String(20))
    correct: Mapped[int] = mapped_column(Integer, default=0)
    answered: Mapped[int] = mapped_column(Integer, default=0)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AttemptRow(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        UniqueConstraint("session_id", "question_id", name="uq_attempts_session_question"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    correct: Mapped[bool] = mapped_column(Boolean)
    response: Mapped[dict[str, Any]] = mapped_column(JSON)
    time_ms: Mapped[int | None] = mapped_column(Integer)
    elo_delta: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RatingRow(Base):
    __tablename__ = "ratings"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    elo: Mapped[float] = mapped_column(Float)


class MasteryRow(Base):
    __tablename__ = "mastery"
    __table_args__ = (Index("ix_mastery_user_subject", "user_id", "subject_id"), {"schema": SCHEMA})

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    type_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    score: Mapped[float] = mapped_column(Float)
    attempts: Mapped[int] = mapped_column(Integer)
    correct: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewCardRow(Base):
    __tablename__ = "review_cards"
    __table_args__ = (Index("ix_review_cards_due", "user_id", "subject_id", "due_at"), {"schema": SCHEMA})

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    topic_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    type_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    ease: Mapped[float] = mapped_column(Float)
    interval_days: Mapped[int] = mapped_column(Integer)
    reps: Mapped[int] = mapped_column(Integer)
    lapses: Mapped[int] = mapped_column(Integer)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlacementRow(Base):
    __tablename__ = "placements"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    start_unit_index: Mapped[int] = mapped_column(Integer)
    ability: Mapped[float | None] = mapped_column(Float)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEventRow(Base):
    __tablename__ = "processed_events"
    __table_args__ = {"schema": SCHEMA}

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    handler: Mapped[str] = mapped_column(String(40), primary_key=True)
