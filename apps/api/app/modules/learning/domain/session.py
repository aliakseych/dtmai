"""Practice session rules."""

from enum import StrEnum

from app.shared.errors import Conflict, ValidationFailed


class Mode(StrEnum):
    LESSON = "lesson"
    DRILL = "drill"
    REVIEW = "review"
    PLACEMENT = "placement"
    RUSH = "rush"


HEART_MODES = frozenset({Mode.LESSON, Mode.DRILL})  # only these cost hearts
PERFECT_BONUS = 5
XP_PER_CORRECT = 2


def costs_hearts(mode: Mode) -> bool:
    return mode in HEART_MODES


def can_start(mode: Mode, hearts: int, unlimited: bool) -> None:
    if costs_hearts(mode) and not unlimited and hearts <= 0:
        raise Conflict("no hearts left: review to earn hearts or wait", code="no_hearts")


def xp_base(mode: Mode, correct: int, total: int) -> int:
    if mode in (Mode.PLACEMENT, Mode.RUSH) or total <= 0:  # rush xp lives in domain.rush
        return 0
    base = correct * XP_PER_CORRECT
    if mode in HEART_MODES and correct == total:
        base += PERFECT_BONUS
    return base


def validate_count(n: int, *, maximum: int = 30) -> int:
    if not 1 <= n <= maximum:
        raise ValidationFailed(f"count must be 1..{maximum}", code="invalid_count")
    return n


from dataclasses import dataclass, field  # noqa: E402
from datetime import datetime  # noqa: E402
from typing import Any  # noqa: E402
from uuid import UUID  # noqa: E402

IN_PROGRESS = "in_progress"
COMPLETED = "completed"
ABANDONED = "abandoned"


@dataclass(slots=True)
class SessionRec:
    id: UUID
    user_id: UUID
    mode: Mode
    subject_id: UUID | None
    topic_id: UUID | None
    lesson_id: UUID | None
    language: str
    question_ids: list[UUID]
    started_at: datetime
    status: str = IN_PROGRESS
    correct: int = 0
    answered: int = 0
    meta: dict[str, Any] = field(default_factory=dict)
    finished_at: datetime | None = None

    @property
    def total(self) -> int:
        return len(self.question_ids)

    @property
    def done(self) -> bool:
        return self.answered >= self.total
