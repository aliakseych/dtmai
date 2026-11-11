from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

S = "bank"


class PassageRow(Base):
    __tablename__ = "passages"
    __table_args__ = {"schema": S}

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    language: Mapped[str] = mapped_column(String(8))
    title: Mapped[str | None] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(Text)
    media: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    source_id: Mapped[UUID | None] = mapped_column(Uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class QuestionRow(Base):
    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_pick", "subject_id", "language", "status"),
        Index("ix_questions_topic", "topic_id", "status"),
        {"schema": S},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    subject_id: Mapped[UUID] = mapped_column(Uuid)  # catalog ids: no cross-schema FKs
    topic_id: Mapped[UUID] = mapped_column(Uuid)
    type_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    kind: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(8))
    stem: Mapped[str] = mapped_column(Text)
    media: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    answer: Mapped[dict[str, Any]] = mapped_column(JSONB)
    answer_official: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty: Mapped[float] = mapped_column(Float, default=1000.0)
    passage_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey(f"{S}.passages.id"), index=True)
    parent_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    source_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    source_ref: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    translation_group_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    report_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExplanationRow(Base):
    __tablename__ = "question_explanations"
    __table_args__ = {"schema": S}

    question_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{S}.questions.id", ondelete="CASCADE"), primary_key=True
    )
    locale: Mapped[str] = mapped_column(String(10), primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReportRow(Base):
    __tablename__ = "question_reports"
    __table_args__ = (UniqueConstraint("question_id", "user_id"), {"schema": S})

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{S}.questions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(Uuid)
    reason: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEventRow(Base):
    __tablename__ = "processed_events"
    __table_args__ = {"schema": S}

    event_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditRow(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": S}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor: Mapped[str | None] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    before: Mapped[Any] = mapped_column(JSONB, nullable=True)
    after: Mapped[Any] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str] = mapped_column(String(500), default="")
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
