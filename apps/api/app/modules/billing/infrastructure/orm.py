import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Identity,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "billing"


class PlanRow(Base):
    __tablename__ = "plans"
    __table_args__ = {"schema": SCHEMA}

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    names: Mapped[dict[str, str]] = mapped_column(JSON)
    price_uzs: Mapped[int] = mapped_column(BigInteger)
    period_months: Mapped[int] = mapped_column(Integer, default=1)
    features: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list)
    limits: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SubscriptionRow(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    plan_code: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(12))
    source: Mapped[str] = mapped_column(String(12))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvoiceRow(Base):
    __tablename__ = "invoices"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    seq: Mapped[int] = mapped_column(BigInteger, Identity(always=True), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    plan_code: Mapped[str] = mapped_column(String(40))
    period_months: Mapped[int] = mapped_column(Integer)
    amount_uzs: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(12))
    click_trans_id: Mapped[str | None] = mapped_column(String(40), unique=True)
    click_paydoc_id: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
