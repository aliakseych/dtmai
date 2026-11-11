from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SourceLyceum:
    external_id: int
    code: str
    name_uz: str
    name_en: str
    name_ru: str


@dataclass(frozen=True, slots=True)
class SourceLanguage:
    external_id: int
    code: str
    name_uz: str
    name_en: str
    name_ru: str


@dataclass(frozen=True, slots=True)
class SourceSpeciality:
    code: str
    name: str
    quota: int
    applications: int


class ImportStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(slots=True)
class ImportRun:
    id: UUID
    year: int
    status: ImportStatus
    requested_by: UUID | None
    created_at: datetime | None = None
    finished_at: datetime | None = None
    lyceums: int = 0
    stats: int = 0
    errors: int = 0
    error: str | None = None


def competition_ratio(applications: int, quota: int) -> float | None:
    """Applicants per seat; None when the quota is unknown/zero."""
    if quota <= 0:
        return None
    return round(applications / quota, 2)


def validate_year(year: int) -> int:
    from app.shared.errors import ValidationFailed

    if not 2000 <= year <= 2100:
        raise ValidationFailed("year out of range", code="invalid_year")
    return year


def validate_passing_score(score: float | None) -> float | None:
    from app.shared.errors import ValidationFailed

    if score is not None and not 0 <= score <= 1000:
        raise ValidationFailed("passing score out of range", code="invalid_passing_score")
    return score
