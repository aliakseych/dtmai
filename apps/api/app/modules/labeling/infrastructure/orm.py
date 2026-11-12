import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "labeling"
_UUID = UUID(as_uuid=True)


class SolveRunRow(Base):
    __tablename__ = "solve_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(_UUID, index=True)
    trigger: Mapped[str] = mapped_column(String(20))  # generation|ingestion|manual|recheck
    outcome: Mapped[str] = mapped_column(String(20))  # status chosen by the machine
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(String(40))
    key_conflict: Mapped[bool] = mapped_column(Boolean, default=False)
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SolverVoteRow(Base):
    __tablename__ = "solver_votes"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey(f"{SCHEMA}.solve_runs.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[str] = mapped_column(String(12))  # solve|judge|adjudicate
    model: Mapped[str] = mapped_column(String(120))
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str | None] = mapped_column(Text)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(String(300))


class QueueItemRow(Base):
    """One row per question awaiting (or having had) human review."""

    __tablename__ = "queue_items"
    __table_args__ = (
        Index("ix_queue_open", "state", "resolved_at", "confidence"),
        {"schema": SCHEMA},
    )

    question_id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    state: Mapped[str] = mapped_column(String(20))  # auto_agreed|escalated|needs_human
    suggested: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(String(40))
    subject_id: Mapped[uuid.UUID] = mapped_column(_UUID, index=True)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    type_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    language: Mapped[str] = mapped_column(String(10), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    claimed_by: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    claimed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DecisionRow(Base):
    __tablename__ = "decisions"
    __table_args__ = (
        Index("ix_decisions_question", "question_id", "created_at"),
        Index("ix_decisions_labeler", "labeler_id", "created_at"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    labeler_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    action: Mapped[str] = mapped_column(String(10))  # accept|edit|skip|flag|bulk
    response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    time_ms: Mapped[int] = mapped_column(Integer, default=0)
    prev_status: Mapped[str | None] = mapped_column(String(20))
    new_status: Mapped[str | None] = mapped_column(String(20))
    prev_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    prev_queue_state: Mapped[str | None] = mapped_column(String(20))
    audit_sample_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    reason: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    undone_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditSampleRow(Base):
    __tablename__ = "audit_samples"
    __table_args__ = (
        Index("ix_audit_open", "completed_at", "subject_id", "language"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(_UUID, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(_UUID, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    language: Mapped[str] = mapped_column(String(10))
    machine_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    human_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    labeler_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    matched: Mapped[bool | None] = mapped_column(Boolean)
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ActivityRow(Base):
    """Append-only log of everything a labeler does in the cockpit."""

    __tablename__ = "activity"
    __table_args__ = (
        Index("ix_activity_actor", "actor_user_id", "created_at"),
        Index("ix_activity_action", "action", "created_at"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    action: Mapped[str] = mapped_column(String(10))  # claim|label|approve|reject|edit|skip|release
    question_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, server_default="{}")
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationRunRow(Base):
    __tablename__ = "generation_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    type_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    kind: Mapped[str] = mapped_column(String(20))
    language: Mapped[str] = mapped_column(String(10))
    requested: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[float | None] = mapped_column(Float)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(12), default="pending"
    )  # pending|running|done|failed
    created_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportBatchRow(Base):
    __tablename__ = "import_batches"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    source_code: Mapped[str] = mapped_column(String(80))
    source_name: Mapped[str | None] = mapped_column(String(200))
    source_year: Mapped[int | None] = mapped_column(Integer)
    subject_id: Mapped[uuid.UUID] = mapped_column(_UUID)
    language: Mapped[str] = mapped_column(String(10))
    base: Mapped[str | None] = mapped_column(String(120))  # mock/paper name
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        _UUID
    )  # default topic for extracted questions
    type_ids: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)  # kind -> question type id
    has_answer_key: Mapped[bool] = mapped_column(Boolean, default=False)
    root: Mapped[str] = mapped_column(String(500))  # local path or s3://bucket/prefix
    status: Mapped[str] = mapped_column(
        String(12), default="pending"
    )  # pending|running|done|failed
    files_total: Mapped[int] = mapped_column(Integer, default=0)
    files_done: Mapped[int] = mapped_column(Integer, default=0)
    questions_created: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(_UUID)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ImportFileRow(Base):
    __tablename__ = "import_files"
    __table_args__ = (Index("ix_import_files_batch", "batch_id", "status"), {"schema": SCHEMA})

    id: Mapped[uuid.UUID] = mapped_column(_UUID, primary_key=True)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        _UUID, ForeignKey(f"{SCHEMA}.import_batches.id", ondelete="CASCADE")
    )
    path: Mapped[str] = mapped_column(String(600))
    page: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|done|failed
    extracted: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # raw parsed extraction (per page)
    question_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
