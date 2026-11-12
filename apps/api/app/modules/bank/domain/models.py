from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

STATUSES: tuple[str, ...] = (
    "draft",
    "auto_agreed",
    "escalated",
    "needs_human",
    "verified",
    "hidden",
    "retired",
)
LIVE_STATUS = "verified"
DEFAULT_DIFFICULTY = 1000.0


def transition_allowed(current: str, new: str) -> bool:
    """Any status may move to any other, except that retired can only be revived as draft."""
    if new not in STATUSES:
        return False
    return not (current == "retired" and new not in ("retired", "draft"))


@dataclass(slots=True)
class Question:
    id: UUID
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    stem: str
    payload: dict[str, Any]
    answer: dict[str, Any]
    difficulty: float = DEFAULT_DIFFICULTY
    media: list[Any] = field(default_factory=list)
    passage_id: UUID | None = None
    parent_id: UUID | None = None
    source_id: UUID | None = None
    source_ref: dict[str, Any] | None = None
    translation_group_id: UUID | None = None
    status: str = "draft"
    answer_official: bool = False
    attempts: int = 0
    correct_count: int = 0
    report_count: int = 0
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def correct_rate(self) -> float | None:
        return self.correct_count / self.attempts if self.attempts else None


@dataclass(slots=True)
class Passage:
    id: UUID
    language: str
    text: str
    title: str | None = None
    media: list[Any] = field(default_factory=list)
    source_id: UUID | None = None


@dataclass(slots=True)
class QuestionFilter:
    subject_id: UUID | None = None
    topic_id: UUID | None = None
    type_id: UUID | None = None
    language: str | None = None
    status: str | None = None
    source_id: UUID | None = None
    kind: str | None = None
    q: str | None = None
    reported: bool = False
    learner_visible: bool = False  # hide questions of archived question bases


# Difficulty levels by Elo (same cut-offs as learning's `level_for`); None = unbounded side.
LEVEL_BOUNDS: dict[str, tuple[float | None, float | None]] = {
    "easy": (None, 1100.0),
    "medium": (1100.0, 1350.0),
    "hard": (1350.0, None),
}


def level_of(difficulty: float) -> str:
    if difficulty < 1100:
        return "easy"
    return "medium" if difficulty < 1350 else "hard"
