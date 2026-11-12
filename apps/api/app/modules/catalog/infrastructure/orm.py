from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
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

S = "catalog"


class _Common:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)


class SubjectRow(_Common, Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("code"), {"schema": S})
    code: Mapped[str] = mapped_column(String(64))
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class TopicRow(_Common, Base):
    __tablename__ = "topics"
    __table_args__ = {"schema": S}
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{S}.subjects.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{S}.topics.id", ondelete="SET NULL"), index=True
    )
    code: Mapped[str | None] = mapped_column(String(64))
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    position: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class QuestionTypeRow(_Common, Base):
    __tablename__ = "question_types"
    __table_args__ = (UniqueConstraint("code"), {"schema": S})
    code: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(20))
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    generation_prompt: Mapped[str] = mapped_column(Text, default="")
    rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class PathRow(_Common, Base):
    __tablename__ = "paths"
    __table_args__ = (UniqueConstraint("subject_id", "language"), {"schema": S})
    subject_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{S}.subjects.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str] = mapped_column(String(8))
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(12), default="draft")
    position: Mapped[int] = mapped_column(Integer, default=0)


class UnitRow(_Common, Base):
    __tablename__ = "units"
    __table_args__ = {"schema": S}
    path_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{S}.paths.id", ondelete="CASCADE"), index=True
    )
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    position: Mapped[int] = mapped_column(Integer, default=0)


class LessonRow(_Common, Base):
    __tablename__ = "lessons"
    __table_args__ = {"schema": S}
    unit_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{S}.units.id", ondelete="CASCADE"), index=True
    )
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    topic_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    type_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    question_count: Mapped[int] = mapped_column(Integer, default=10)
    legendary: Mapped[bool] = mapped_column(Boolean, default=False)
    theory: Mapped[list[Any]] = mapped_column(JSONB, default=list, server_default="[]")
    position: Mapped[int] = mapped_column(Integer, default=0)


class BlueprintRow(_Common, Base):
    __tablename__ = "blueprints"
    __table_args__ = (UniqueConstraint("code", "version"), {"schema": S})
    code: Mapped[str] = mapped_column(String(64))
    version: Mapped[int] = mapped_column(Integer, default=0)
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    kind: Mapped[str] = mapped_column(String(12))
    sections: Mapped[list[Any]] = mapped_column(JSONB)
    duration_min: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_id: Mapped[UUID | None] = mapped_column(Uuid)


class QuestionBaseRow(_Common, Base):
    __tablename__ = "question_bases"
    __table_args__ = (UniqueConstraint("code"), {"schema": S})
    code: Mapped[str] = mapped_column(String(64))
    names: Mapped[dict[str, Any]] = mapped_column(JSONB)
    kind: Mapped[str] = mapped_column(String(20))
    year: Mapped[int | None] = mapped_column(Integer)
    provenance: Mapped[str] = mapped_column(Text, default="")
    license_note: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class AuditRow(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"schema": S}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    actor: Mapped[str | None] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(20))
    entity: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[UUID | None] = mapped_column(Uuid, index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


ENTITIES: dict[str, type[Base]] = {
    "subject": SubjectRow,
    "topic": TopicRow,
    "question_type": QuestionTypeRow,
    "path": PathRow,
    "unit": UnitRow,
    "lesson": LessonRow,
    "blueprint": BlueprintRow,
    "question_base": QuestionBaseRow,
}
