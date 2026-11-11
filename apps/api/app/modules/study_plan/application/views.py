from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.modules.study_plan.domain.models import PlanSettings, Task, TaskKind, TaskStatus
from app.modules.study_plan.ports import DailyQuestion


@dataclass(frozen=True, slots=True)
class SettingsCmd:
    direction_code: str
    language: str
    minutes_school_day: int
    minutes_weekend_day: int
    target_lyceum_ids: tuple[UUID, ...] = ()
    certificates: tuple[Any, ...] = ()  # domain Certificate
    choice_subject_id: UUID | None = None
    exam_date: date | None = None  # defaults to the exam profile's date
    start_date: date | None = None  # defaults to today


@dataclass(frozen=True, slots=True)
class TaskView:
    id: UUID
    day: date
    position: int
    kind: TaskKind
    subject_id: UUID | None
    subject_name: str | None
    target: dict[str, Any]
    est_minutes: int
    status: TaskStatus
    done_at: datetime | None

    @classmethod
    def of(cls, t: Task, subject_name: str | None) -> "TaskView":
        return cls(
            t.id,
            t.day,
            t.position,
            t.kind,
            t.subject_id,
            subject_name,
            t.target,
            t.est_minutes,
            t.status,
            t.done_at,
        )


@dataclass(frozen=True, slots=True)
class SectionView:
    section_id: UUID
    role: str
    subject_id: UUID | None
    subject_name: str | None
    max_points: float
    exempt: bool
    in_app: bool  # false: the app cannot prepare for it (creative exam) or has no content yet
    choice_group: str | None
    subject_options: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class SettingsView:
    settings: PlanSettings
    plan_end: date | None
    exempt_section_ids: tuple[UUID, ...]
    sections: tuple[SectionView, ...]


@dataclass(frozen=True, slots=True)
class TodayView:
    day: date
    tasks: tuple[TaskView, ...]
    days_left: int
    plan_end: date
    rest_day: bool  # nothing planned: taper days before the exam or no budget


@dataclass(frozen=True, slots=True)
class DayView:
    day: date
    minutes: int
    done: int
    total: int
    tasks: tuple[TaskView, ...]


@dataclass(frozen=True, slots=True)
class RangeView:
    days: tuple[DayView, ...]
    exam_date: date
    plan_end: date


@dataclass(frozen=True, slots=True)
class HomeView:
    configured: bool
    days_left: int | None = None
    exam_date: date | None = None
    plan_end: date | None = None
    phase: str | None = None
    predicted_score: float | None = None
    max_score: float | None = None
    today_done: int = 0
    today_total: int = 0
    today_minutes: int = 0
    tasks: tuple[TaskView, ...] = ()


@dataclass(frozen=True, slots=True)
class DailyQuestionsView:
    day: date
    questions: tuple[DailyQuestion, ...]


@dataclass(frozen=True, slots=True)
class SubjectMastery:
    subject_id: UUID
    subject_name: str | None
    mastery: float | None


@dataclass(frozen=True, slots=True)
class MockTrendPoint:
    taken_at: datetime
    score: float
    max_score: float


@dataclass(frozen=True, slots=True)
class AnalyticsView:
    locked: bool
    mastery: tuple[SubjectMastery, ...] = ()
    mocks: tuple[MockTrendPoint, ...] = ()
    tasks_done: int = 0
    tasks_missed: int = 0
    tasks_todo: int = 0
    minutes_done: int = 0
    minutes_planned: int = 0
    completion_rate: float = 0.0
