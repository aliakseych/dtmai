import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db import Base

SCHEMA = "lyceums"


class LyceumRow(Base):
    __tablename__ = "lyceums"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    code: Mapped[str] = mapped_column(String(20))
    name_uz: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text, default="")
    name_ru: Mapped[str] = mapped_column(Text, default="")


class EducationLanguageRow(Base):
    __tablename__ = "education_languages"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    code: Mapped[str] = mapped_column(String(20))
    name_uz: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text, default="")
    name_ru: Mapped[str] = mapped_column(Text, default="")


class YearlyStatRow(Base):
    __tablename__ = "yearly_stats"
    __table_args__ = (
        UniqueConstraint("lyceum_id", "language_id", "speciality_code", "year",
                         name="uq_yearly_stats_key"),
        {"schema": SCHEMA},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    lyceum_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.lyceums.id", ondelete="CASCADE"), index=True
    )
    language_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.education_languages.id", ondelete="CASCADE")
    )
    speciality_code: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(Text)
    year: Mapped[int] = mapped_column(Integer, index=True)
    quota: Mapped[int] = mapped_column(Integer, default=0)
    applications: Mapped[int] = mapped_column(Integer, default=0)
    passing_score: Mapped[float | None] = mapped_column(Float)


class ImportRunRow(Base):
    __tablename__ = "import_runs"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    year: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12))
    requested_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    counts: Mapped[dict[str, int]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
