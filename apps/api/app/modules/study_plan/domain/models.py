from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from app.modules.study_plan.domain.exam import Certificate
from app.shared.errors import ValidationFailed

MAX_TARGET_LYCEUMS = 3
LANGUAGES = frozenset({"uz", "ru"})
MAX_HORIZON_DAYS = 400  # longest span between start and exam date
MAX_START_AHEAD_DAYS = 30  # how far in the future a plan may start


def matches_blueprint(target: dict[str, Any], blueprint_id: UUID | None) -> bool:
    """A mock task is ticked only by a mock of the blueprint it plans; no filter matches anything."""
    return blueprint_id is None or str(target.get("blueprint_id")) == str(blueprint_id)


def valid_study_time(value: str) -> bool:
    if len(value) != 5 or value[2] != ":" or not (value[:2] + value[3:]).isdigit():
        return False
    return int(value[:2]) < 24 and int(value[3:]) < 60


class TaskKind(StrEnum):
    LESSON = "lesson"
    DRILL = "drill"
    REVIEW = "review"
    MOCK = "mock"
    RUSH = "rush"


class TaskStatus(StrEnum):
    TODO = "todo"
    DONE = "done"
    MISSED = "missed"


@dataclass(frozen=True, slots=True)
class PlanSettings:
    direction_code: str
    language: str  # education language: uz | ru
    start_date: date
    exam_date: date
    minutes_school_day: int = 45
    minutes_weekend_day: int = 90
    target_lyceum_ids: tuple[UUID, ...] = ()
    certificates: tuple[Certificate, ...] = ()
    choice_subject_id: UUID | None = None  # chosen foreign language
    study_time: str | None = None  # implementation intention: "HH:MM" local (Asia/Tashkent)
    study_days: tuple[int, ...] = ()  # weekdays 0=Mon..6=Sun; empty = every day

    def __post_init__(self) -> None:
        if self.language not in LANGUAGES:
            raise ValidationFailed("unsupported language", code="invalid_language")
        if not 10 <= self.minutes_school_day <= 240 or not 10 <= self.minutes_weekend_day <= 360:
            raise ValidationFailed("minutes out of range", code="invalid_minutes")
        if self.exam_date <= self.start_date:
            raise ValidationFailed(
                "exam date must follow the start date", code="exam_date_too_soon"
            )
        if (self.exam_date - self.start_date).days > MAX_HORIZON_DAYS:
            raise ValidationFailed("exam date is too far ahead", code="exam_date_too_far")
        if len(self.target_lyceum_ids) > MAX_TARGET_LYCEUMS:
            raise ValidationFailed("at most 3 target lyceums", code="too_many_lyceums")
        if self.study_time is not None and not valid_study_time(self.study_time):
            raise ValidationFailed("study time must be HH:MM", code="invalid_study_time")
        if any(not 0 <= d <= 6 for d in self.study_days) or len(set(self.study_days)) != len(
            self.study_days
        ):
            raise ValidationFailed("study days are weekdays 0-6", code="invalid_study_days")

    def to_json(self) -> dict[str, Any]:
        return {
            "direction_code": self.direction_code,
            "language": self.language,
            "start_date": self.start_date.isoformat(),
            "exam_date": self.exam_date.isoformat(),
            "minutes_school_day": self.minutes_school_day,
            "minutes_weekend_day": self.minutes_weekend_day,
            "target_lyceum_ids": [str(i) for i in self.target_lyceum_ids],
            "certificates": [
                {
                    "section_id": str(c.section_id),
                    "cert_type": c.cert_type,
                    "value": c.value,
                    "language_subject_id": str(c.language_subject_id)
                    if c.language_subject_id
                    else None,
                }
                for c in self.certificates
            ],
            "choice_subject_id": str(self.choice_subject_id) if self.choice_subject_id else None,
            "study_time": self.study_time,
            "study_days": list(self.study_days),
        }

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> "PlanSettings":
        return cls(
            direction_code=d["direction_code"],
            language=d["language"],
            start_date=date.fromisoformat(d["start_date"]),
            exam_date=date.fromisoformat(d["exam_date"]),
            minutes_school_day=d["minutes_school_day"],
            minutes_weekend_day=d["minutes_weekend_day"],
            target_lyceum_ids=tuple(UUID(i) for i in d["target_lyceum_ids"]),
            certificates=tuple(
                Certificate(
                    UUID(c["section_id"]),
                    c["cert_type"],
                    float(c["value"]),
                    UUID(c["language_subject_id"]) if c.get("language_subject_id") else None,
                )
                for c in d["certificates"]
            ),
            choice_subject_id=UUID(d["choice_subject_id"]) if d.get("choice_subject_id") else None,
            study_time=d.get("study_time"),
            study_days=tuple(d.get("study_days") or ()),
        )


@dataclass(slots=True)
class Plan:
    id: UUID
    user_id: UUID
    settings: PlanSettings
    version: int = 1
    plan_end: date | None = None  # None until the first generation
    last_replanned_on: date | None = None


@dataclass(slots=True)
class Task:
    id: UUID
    plan_id: UUID
    day: date
    position: int
    kind: TaskKind
    subject_id: UUID | None
    target: dict[str, Any]
    est_minutes: int
    status: TaskStatus = TaskStatus.TODO
    done_at: datetime | None = None
    source_ref: UUID | None = None

    def complete(self, at: datetime, source_ref: UUID | None) -> None:
        self.status = TaskStatus.DONE
        self.done_at = at
        self.source_ref = source_ref

    @property
    def undoable(self) -> bool:
        """Only a hand-ticked task can be reopened; activity-completed ones reflect real work."""
        return self.status is TaskStatus.DONE and self.source_ref is None

    def reopen(self) -> None:
        self.status = TaskStatus.TODO
        self.done_at = None
