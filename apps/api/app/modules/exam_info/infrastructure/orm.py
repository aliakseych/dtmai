from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

_S = "exam_info"


class ExamProfileRow(Base):
    __tablename__ = "exam_profile"
    __table_args__ = (
        UniqueConstraint("direction_code", "exam_year", name="uq_exam_profile_direction_year"),
        CheckConstraint("taper_days between 5 and 7", name="taper"),
        {"schema": _S},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    kind: Mapped[str] = mapped_column(String(32))
    direction_code: Mapped[str | None] = mapped_column(String(16))
    group_code: Mapped[str | None] = mapped_column(String(32))
    names: Mapped[dict[str, str]] = mapped_column(JSONB)
    exam_year: Mapped[int] = mapped_column(Integer)
    exam_date: Mapped[date | None] = mapped_column(Date)
    date_verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    max_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    trust_self_declared: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    taper_days: Mapped[int] = mapped_column(Integer, server_default=text("6"))
    mock_blueprint_id: Mapped[UUID | None] = mapped_column(Uuid)
    source_url: Mapped[str | None] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class SectionRow(Base):
    __tablename__ = "exam_profile_section"
    __table_args__ = (
        UniqueConstraint("profile_id", "slot", name="uq_exam_section_slot"),
        CheckConstraint("(role = 'iq') = (slot = 0)", name="iq_slot"),
        CheckConstraint("role <> 'iq' or not exemptible", name="iq_not_exemptible"),
        CheckConstraint("role in ('iq', 'subject', 'creative')", name="role"),
        {"schema": _S},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_S}.exam_profile.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(16))
    slot: Mapped[int] = mapped_column(Integer)
    subject_id: Mapped[UUID | None] = mapped_column(Uuid)  # soft ref to catalog.subject
    subject_code: Mapped[str | None] = mapped_column(String(64))
    names: Mapped[dict[str, str]] = mapped_column(JSONB)
    choice_group: Mapped[str | None] = mapped_column(String(32))
    question_count: Mapped[int | None] = mapped_column(Integer)
    points_per_question: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    max_points: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    exemptible: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class SubjectChoiceRow(Base):
    __tablename__ = "exam_subject_choice"
    __table_args__ = {"schema": _S}

    choice_group: Mapped[str] = mapped_column(String(32), primary_key=True)
    subject_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)  # soft ref to catalog.subject
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class CertRuleRow(Base):
    __tablename__ = "exam_certificate_rule"
    __table_args__ = (
        UniqueConstraint(
            "section_id",
            "cert_type",
            "language_subject_id",
            "min_value",
            name="uq_exam_cert_rule_key",
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint("awarded_fraction between 0 and 1", name="fraction"),
        CheckConstraint("not active or min_value is not null", name="active_min"),
        CheckConstraint(
            "cert_type in ('cefr', 'ielts', 'toefl', 'national', 'other_intl')", name="type"
        ),
        {"schema": _S},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    section_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{_S}.exam_profile_section.id", ondelete="CASCADE")
    )
    cert_type: Mapped[str] = mapped_column(String(16))
    language_subject_id: Mapped[UUID | None] = mapped_column(Uuid)
    level_label: Mapped[str | None] = mapped_column(String(64))
    min_value: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    awarded_fraction: Mapped[Decimal] = mapped_column(Numeric(3, 2), server_default=text("1.0"))
    note: Mapped[dict[str, str]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    source_url: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class ExamEventRow(Base):
    __tablename__ = "exam_event"
    __table_args__ = (
        UniqueConstraint("exam_year", "kind", name="uq_exam_event_year_kind"),
        CheckConstraint("ends_on is null or ends_on >= starts_on", name="range"),
        CheckConstraint("kind in ('applications', 'test', 'results', 'appeal')", name="kind"),
        {"schema": _S},
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    exam_year: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(16))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    label: Mapped[dict[str, str]] = mapped_column(JSONB)
    verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    source_url: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))


class SeededKeyRow(Base):
    """Seed keys already offered once; a deleted seeded event/FAQ stays deleted."""

    __tablename__ = "seeded_key"
    __table_args__ = {"schema": _S}

    kind: Mapped[str] = mapped_column(String(16), primary_key=True)
    key: Mapped[str] = mapped_column(String(96), primary_key=True)


class FaqRow(Base):
    __tablename__ = "faq_item"
    __table_args__ = {"schema": _S}

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    category: Mapped[str] = mapped_column(String(32))
    question: Mapped[dict[str, str]] = mapped_column(JSONB)
    answer: Mapped[dict[str, str]] = mapped_column(JSONB)
    position: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    published: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    source_url: Mapped[str | None] = mapped_column(Text)
    verified: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[UUID | None] = mapped_column(Uuid)


__all__: list[Any] = [
    "CertRuleRow",
    "ExamEventRow",
    "ExamProfileRow",
    "FaqRow",
    "SectionRow",
    "SeededKeyRow",
    "SubjectChoiceRow",
]
