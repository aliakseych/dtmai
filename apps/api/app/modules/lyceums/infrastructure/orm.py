import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    JSON,
    Boolean,
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


class CityRow(Base):
    __tablename__ = "cities"
    __table_args__ = {"schema": SCHEMA}

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name_uz_latn: Mapped[str] = mapped_column(Text)
    name_uz_cyrl: Mapped[str] = mapped_column(Text)
    name_ru: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text)


class LyceumRow(Base):
    __tablename__ = "lyceums"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    external_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    code: Mapped[str] = mapped_column(String(20))
    name_uz: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text, default="")
    name_ru: Mapped[str] = mapped_column(Text, default="")
    logo_url: Mapped[str | None] = mapped_column(Text)
    campus_photo_url: Mapped[str | None] = mapped_column(Text)
    gallery_urls: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, server_default="{}")
    description: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, server_default="{}")
    courses: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, server_default="{}")
    university_name: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(
        String(50), ForeignKey(f"{SCHEMA}.cities.code", ondelete="SET NULL"), index=True
    )
    website: Mapped[str | None] = mapped_column(Text)
    contacts: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, server_default="{}")
    verified_rep: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    dormitory_status: Mapped[str] = mapped_column(
        String(10), default="unknown", server_default="unknown"
    )
    dormitory_description: Mapped[dict[str, str]] = mapped_column(
        JSON, default=dict, server_default="{}"
    )


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


class RepMembershipRow(Base):
    __tablename__ = "rep_memberships"
    __table_args__ = {"schema": SCHEMA}

    # Soft reference to identity.users (other module's schema).
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    lyceum_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.lyceums.id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: Mapped[str] = mapped_column(String(10))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LyceumPostRow(Base):
    __tablename__ = "posts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    lyceum_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.lyceums.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    link: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), index=True)
    reject_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
