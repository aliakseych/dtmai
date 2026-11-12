"""Ports the study planner needs from the outside. Adapters live in infrastructure/."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from app.modules.study_plan.domain.exam import ExamProfile
from app.modules.study_plan.domain.models import Plan, Task, TaskKind, TaskStatus


@dataclass(frozen=True, slots=True)
class WeakSpot:
    topic_id: UUID | None
    type_id: UUID


@dataclass(frozen=True, slots=True)
class SubjectInfo:
    id: UUID
    code: str
    names: dict[str, str]


@dataclass(frozen=True, slots=True)
class MockPoint:
    taken_at: datetime
    score: float
    max_score: float


@dataclass(frozen=True, slots=True)
class DailyQuestion:
    id: UUID
    subject_id: UUID
    kind: str
    stem: str
    media: list[Any]
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class DailyGrade:
    correct: bool
    correct_response: dict[str, Any]


class ExamRulesPort(Protocol):
    async def profile(self, direction_code: str) -> ExamProfile | None: ...


class LearningPort(Protocol):
    async def mastery(self, user_id: UUID) -> dict[UUID, float | None]: ...
    async def weak_spots(self, user_id: UUID, subject_id: UUID) -> list[WeakSpot]: ...
    async def due_reviews(self, user_id: UUID, subject_id: UUID) -> int: ...
    async def mocks(self, user_id: UUID) -> list[MockPoint]: ...
    async def lesson_queue(self, user_id: UUID, subject_id: UUID, language: str) -> list[UUID]: ...
    async def pool(self, subject_id: UUID, language: str) -> int:
        """Verified questions a drill or rush could draw from."""
        ...


class CatalogPort(Protocol):
    async def subjects(self) -> list[SubjectInfo]: ...
    async def mock_minutes(self, blueprint_id: UUID) -> int: ...
    async def mock_servable(self, blueprint_id: UUID, language: str) -> bool:
        """True when every blueprint section can be filled with at least one question."""
        ...

    async def topic_names(self, topic_id: UUID) -> dict[str, str]: ...


@dataclass(frozen=True, slots=True)
class DreamTarget:
    lyceum_id: UUID
    year: int | None = None
    passing_score: float | None = None
    competition_ratio: float | None = None


class DreamPort(Protocol):
    async def target(self, user_id: UUID) -> DreamTarget | None:
        """The learner's first dream lyceum with its latest admission benchmark."""
        ...


class QuestionPort(Protocol):
    async def pick(
        self, subject_id: UUID, language: str, n: int, exclude: list[UUID]
    ) -> list[DailyQuestion]: ...
    async def get(self, ids: list[UUID]) -> list[DailyQuestion]: ...
    async def grade(self, question_id: UUID, response: dict[str, Any]) -> DailyGrade: ...


class EntitlementPort(Protocol):
    async def has_feature(self, user_id: UUID, feature: str) -> bool: ...


class PlanRepository(Protocol):
    async def get_plan(self, user_id: UUID) -> Plan | None: ...
    async def get_plan_for_update(self, user_id: UUID) -> Plan | None: ...
    async def study_schedules(
        self, user_ids: list[UUID]
    ) -> dict[UUID, tuple[str, tuple[int, ...]]]: ...
    async def insert_plan(self, plan: Plan) -> bool: ...
    async def save_plan(self, plan: Plan) -> None: ...
    async def tasks_between(self, plan_id: UUID, start: date, end: date) -> list[Task]: ...
    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None: ...
    async def first_open(
        self, plan_id: UUID, kind: TaskKind, on_or_before: date, *, blueprint_id: UUID | None = None
    ) -> Task | None: ...
    async def has_source(self, plan_id: UUID, source_ref: UUID) -> bool: ...
    async def mark_missed_before(self, plan_id: UUID, day: date) -> None: ...
    async def delete_todo_from(self, plan_id: UUID, day: date) -> None: ...
    async def add_tasks(self, tasks: list[Task]) -> None: ...
    async def save_task(self, task: Task) -> None: ...
    async def used_minutes(self, plan_id: UUID, start: date, end: date) -> dict[date, int]: ...
    async def count_by_status(
        self, plan_id: UUID, start: date, end: date
    ) -> dict[TaskStatus, tuple[int, int]]: ...
    async def stale_plans(self, today: date) -> list[UUID]:  # user ids
        ...
    async def get_daily_set(self, user_id: UUID, day: date) -> list[UUID] | None: ...
    async def save_daily_set(self, user_id: UUID, day: date, ids: list[UUID]) -> None: ...
    async def merge(self, from_id: UUID, into_id: UUID) -> None:
        """Hand a merged guest's plan and daily sets to `into_id` where it has none."""
        ...

    async def claim_daily_answer(self, user_id: UUID, day: date, question_id: UUID) -> bool:
        """Record the answer once; False when the question was already answered that day."""
        ...
