from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol, Sequence
from uuid import UUID

from app.modules.learning.domain.stats import MockResult, Progress, SubjectAnswers


@dataclass(frozen=True, slots=True)
class Item:
    """A question as presented to the learner (no answer)."""

    id: UUID
    subject_id: UUID
    topic_id: UUID
    type_id: UUID
    kind: str
    language: str
    difficulty: float
    stem: str
    media: list[Any]
    payload: dict[str, Any]
    passage_id: UUID | None
    official: bool
    children: list["Item"] = field(default_factory=list)  # passage_group only


@dataclass(frozen=True, slots=True)
class Graded:
    correct: bool
    correct_response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LessonRef:
    lesson_id: UUID
    subject_id: UUID
    topic_ids: list[UUID]
    type_ids: list[UUID]
    count: int
    language: str
    unit_count: int
    path_units: list[list[UUID]] = field(default_factory=list)  # lesson ids per unit, path order


class ContentPort(Protocol):
    """Question bank + catalog, behind their public facades."""

    async def items(self, ids: Sequence[UUID]) -> list[Item]: ...
    async def pick(
        self,
        *,
        subject_id: UUID,
        topic_ids: Sequence[UUID] | None,
        type_ids: Sequence[UUID] | None,
        language: str,
        n: int,
        exclude_ids: Sequence[UUID] = (),
        difficulty: float | None = None,
        source_id: UUID | None = None,
        level: str | None = None,
    ) -> list[Item]: ...
    async def grade(self, question_id: UUID, response: dict[str, Any]) -> Graded: ...
    async def lesson(self, lesson_id: UUID, language: str | None) -> LessonRef | None: ...
    async def unit_count(self, subject_id: UUID, language: str) -> int: ...


class HeartsPort(Protocol):
    async def state(self, user_id: UUID) -> tuple[int, bool]:
        """(hearts, unlimited)."""
        ...

    async def lose(self, user_id: UUID) -> int:
        """Deduct one heart; returns hearts left. Never blocks."""
        ...


class AnswerStatsPort(Protocol):
    async def daily(self, user_id: UUID, since: date) -> dict[date, tuple[int, int]]:
        """Tashkent day -> (answered, correct) from `since` on."""
        ...

    async def by_subject(self, user_id: UUID) -> list[SubjectAnswers]: ...


class ProgressPort(Protocol):
    async def progress(self, user_id: UUID, since: date) -> Progress:
        """Lifetime counters and xp per Tashkent day from `since` on."""
        ...


class MockResultsPort(Protocol):
    async def recent(self, user_id: UUID, limit: int) -> list[MockResult]:
        """Submitted mocks, newest first."""
        ...
