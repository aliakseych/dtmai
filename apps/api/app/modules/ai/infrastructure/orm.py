import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "ai"


class ModelRouteRow(Base):
    __tablename__ = "model_routes"
    __table_args__ = {"schema": SCHEMA}

    task: Mapped[str] = mapped_column(String(20), primary_key=True)
    slot: Mapped[int] = mapped_column(Integer, primary_key=True)
    model: Mapped[str] = mapped_column(String(120))
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    price_in_micro_per_mtok: Mapped[int] = mapped_column(BigInteger, default=0)
    price_out_micro_per_mtok: Mapped[int] = mapped_column(BigInteger, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LimitsRow(Base):
    """Single row (id=1)."""

    __tablename__ = "limits"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    daily_spend_cap_micro: Mapped[int] = mapped_column(BigInteger)
    user_daily_token_budget: Mapped[int] = mapped_column(BigInteger)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LedgerRow(Base):
    __tablename__ = "ledger"
    __table_args__ = (
        Index("ix_ledger_day_user", "day", "user_id"),
        Index("ix_ledger_day_purpose", "day", "purpose"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    day: Mapped[date] = mapped_column(Date)  # Asia/Tashkent day
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    purpose: Mapped[str] = mapped_column(String(40))
    task: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(120))
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_micro: Mapped[int] = mapped_column(BigInteger, default=0)
    ok: Mapped[bool] = mapped_column(Boolean, default=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ref: Mapped[str | None] = mapped_column(String(80))
    error: Mapped[str | None] = mapped_column(Text)


class ExplainUsageRow(Base):
    """One row per (user, Tashkent day, question): the free-tier explanation counter."""

    __tablename__ = "explain_usage"
    __table_args__ = {"schema": SCHEMA}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
