import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base


class MockAttemptRow(Base):
    __tablename__ = "mock_attempts"
    __table_args__ = (
        Index(
            "uq_mock_attempts_one_active",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'in_progress'"),
        ),
        Index("ix_mock_attempts_user_started", "user_id", "started_at"),
        Index(
            "ix_mock_attempts_deadline", "deadline", postgresql_where=text("status = 'in_progress'")
        ),
        {"schema": "assessment"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    kind: Mapped[str] = mapped_column(String(20))
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    blueprint_version: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    sections: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    answers: Mapped[dict[str, Any]] = mapped_column(JSON)
    flags: Mapped[list[str]] = mapped_column(JSON)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    submit_reason: Mapped[str | None] = mapped_column(String(10))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[float | None] = mapped_column(Float)
