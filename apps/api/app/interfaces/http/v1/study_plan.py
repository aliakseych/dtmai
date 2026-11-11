from datetime import date, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

from app.modules.study_plan.application.views import (
    AnalyticsView,
    DailyQuestionsView,
    DayView,
    HomeView,
    RangeView,
    SectionView,
    SettingsCmd,
    SettingsView,
    TaskView,
    TodayView,
)
from app.modules.study_plan.domain.exam import Certificate
from app.modules.study_plan.domain.models import TaskKind, TaskStatus
from app.modules.study_plan.wiring import PlanServiceDep
from app.shared.deps import CurrentUser
from app.shared.errors import ProblemDetails
from app.shared.locale import pick_locale

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}

router = APIRouter(tags=["study-plan"])
AcceptLanguage = Annotated[str | None, Header()]


class CertificateIO(BaseModel):
    section_id: UUID
    cert_type: str
    value: float
    language_subject_id: UUID | None = None


class SettingsIn(BaseModel):
    direction_code: str
    language: str = Field(description="Education language: uz | ru")
    minutes_school_day: int = 45
    minutes_weekend_day: int = 90
    target_lyceum_ids: list[UUID] = []
    certificates: list[CertificateIO] = []
    choice_subject_id: UUID | None = None
    exam_date: date | None = Field(None, description="Defaults to the exam profile's date")
    start_date: date | None = Field(None, description="Defaults to today")

    def cmd(self) -> SettingsCmd:
        return SettingsCmd(
            direction_code=self.direction_code,
            language=self.language,
            minutes_school_day=self.minutes_school_day,
            minutes_weekend_day=self.minutes_weekend_day,
            target_lyceum_ids=tuple(self.target_lyceum_ids),
            certificates=tuple(Certificate(**c.model_dump()) for c in self.certificates),
            choice_subject_id=self.choice_subject_id,
            exam_date=self.exam_date,
            start_date=self.start_date,
        )


class SettingsOut(BaseModel):
    direction_code: str
    language: str
    start_date: date
    exam_date: date
    plan_end: date | None
    minutes_school_day: int
    minutes_weekend_day: int
    target_lyceum_ids: list[UUID]
    certificates: list[CertificateIO]
    choice_subject_id: UUID | None
    exempt_section_ids: list[UUID]
    sections: list["SectionOut"]

    @classmethod
    def of(cls, v: SettingsView) -> "SettingsOut":
        s = v.settings
        return cls(
            direction_code=s.direction_code,
            language=s.language,
            start_date=s.start_date,
            exam_date=s.exam_date,
            plan_end=v.plan_end,
            minutes_school_day=s.minutes_school_day,
            minutes_weekend_day=s.minutes_weekend_day,
            target_lyceum_ids=list(s.target_lyceum_ids),
            certificates=[
                CertificateIO(
                    section_id=c.section_id,
                    cert_type=c.cert_type,
                    value=c.value,
                    language_subject_id=c.language_subject_id,
                )
                for c in s.certificates
            ],
            choice_subject_id=s.choice_subject_id,
            exempt_section_ids=list(v.exempt_section_ids),
            sections=[SectionOut.of(x) for x in v.sections],
        )


class SectionOut(BaseModel):
    section_id: UUID
    role: str
    subject_id: UUID | None
    subject_name: str | None
    max_points: float
    exempt: bool
    in_app: bool = Field(description="False: not preparable in the app (e.g. drawing)")
    choice_group: str | None
    subject_options: list[UUID]

    @classmethod
    def of(cls, s: SectionView) -> "SectionOut":
        return cls(
            section_id=s.section_id,
            role=s.role,
            subject_id=s.subject_id,
            subject_name=s.subject_name,
            max_points=s.max_points,
            exempt=s.exempt,
            in_app=s.in_app,
            choice_group=s.choice_group,
            subject_options=list(s.subject_options),
        )


class TaskOut(BaseModel):
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
    def of(cls, t: TaskView) -> "TaskOut":
        return cls(
            id=t.id,
            day=t.day,
            position=t.position,
            kind=t.kind,
            subject_id=t.subject_id,
            subject_name=t.subject_name,
            target=t.target,
            est_minutes=t.est_minutes,
            status=t.status,
            done_at=t.done_at,
        )


class TodayOut(BaseModel):
    day: date
    tasks: list[TaskOut]
    days_left: int
    plan_end: date
    rest_day: bool

    @classmethod
    def of(cls, v: TodayView) -> "TodayOut":
        return cls(
            day=v.day,
            tasks=[TaskOut.of(t) for t in v.tasks],
            days_left=v.days_left,
            plan_end=v.plan_end,
            rest_day=v.rest_day,
        )


class DayOut(BaseModel):
    day: date
    minutes: int
    done: int
    total: int
    tasks: list[TaskOut]

    @classmethod
    def of(cls, d: DayView) -> "DayOut":
        return cls(
            day=d.day,
            minutes=d.minutes,
            done=d.done,
            total=d.total,
            tasks=[TaskOut.of(t) for t in d.tasks],
        )


class RangeOut(BaseModel):
    days: list[DayOut]
    exam_date: date
    plan_end: date

    @classmethod
    def of(cls, v: RangeView) -> "RangeOut":
        return cls(days=[DayOut.of(d) for d in v.days], exam_date=v.exam_date, plan_end=v.plan_end)


class HomeOut(BaseModel):
    configured: bool
    days_left: int | None
    exam_date: date | None
    plan_end: date | None
    phase: str | None
    predicted_score: float | None
    max_score: float | None
    today_done: int
    today_total: int
    today_minutes: int
    tasks: list[TaskOut]

    @classmethod
    def of(cls, v: HomeView) -> "HomeOut":
        return cls(
            configured=v.configured,
            days_left=v.days_left,
            exam_date=v.exam_date,
            plan_end=v.plan_end,
            phase=v.phase,
            predicted_score=v.predicted_score,
            max_score=v.max_score,
            today_done=v.today_done,
            today_total=v.today_total,
            today_minutes=v.today_minutes,
            tasks=[TaskOut.of(t) for t in v.tasks],
        )


class DailyQuestionOut(BaseModel):
    id: UUID
    subject_id: UUID
    kind: str
    stem: str
    media: list[Any]
    payload: dict[str, Any]


class DailyQuestionsOut(BaseModel):
    day: date
    questions: list[DailyQuestionOut]

    @classmethod
    def of(cls, v: DailyQuestionsView) -> "DailyQuestionsOut":
        return cls(
            day=v.day,
            questions=[
                DailyQuestionOut(
                    id=q.id,
                    subject_id=q.subject_id,
                    kind=q.kind,
                    stem=q.stem,
                    media=q.media,
                    payload=q.payload,
                )
                for q in v.questions
            ],
        )


class DailyAnswerIn(BaseModel):
    response: dict[str, Any]


class DailyAnswerOut(BaseModel):
    correct: bool
    correct_response: dict[str, Any]


class SubjectMasteryOut(BaseModel):
    subject_id: UUID
    subject_name: str | None
    mastery: float | None


class MockTrendOut(BaseModel):
    taken_at: datetime
    score: float
    max_score: float


class AnalyticsOut(BaseModel):
    locked: bool = Field(description="True without the study_plan_analytics entitlement")
    mastery: list[SubjectMasteryOut]
    mocks: list[MockTrendOut]
    tasks_done: int
    tasks_missed: int
    tasks_todo: int
    minutes_done: int
    minutes_planned: int
    completion_rate: float

    @classmethod
    def of(cls, v: AnalyticsView) -> "AnalyticsOut":
        return cls(
            locked=v.locked,
            mastery=[
                SubjectMasteryOut(
                    subject_id=m.subject_id, subject_name=m.subject_name, mastery=m.mastery
                )
                for m in v.mastery
            ],
            mocks=[
                MockTrendOut(taken_at=m.taken_at, score=m.score, max_score=m.max_score)
                for m in v.mocks
            ],
            tasks_done=v.tasks_done,
            tasks_missed=v.tasks_missed,
            tasks_todo=v.tasks_todo,
            minutes_done=v.minutes_done,
            minutes_planned=v.minutes_planned,
            completion_rate=v.completion_rate,
        )


@router.post(
    "/settings", response_model=SettingsOut, responses=ERR, operation_id="study_plan_save_settings"
)
async def save_settings(
    body: SettingsIn, user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> SettingsOut:
    await svc.save_settings(user.user_id, body.cmd())
    return SettingsOut.of(await svc.get_settings(user.user_id, pick_locale(accept_language)))


@router.get(
    "/settings", response_model=SettingsOut, responses=ERR, operation_id="study_plan_get_settings"
)
async def get_settings(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> SettingsOut:
    return SettingsOut.of(await svc.get_settings(user.user_id, pick_locale(accept_language)))


@router.post(
    "/generate", response_model=SettingsOut, responses=ERR, operation_id="study_plan_generate"
)
async def generate(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> SettingsOut:
    await svc.generate(user.user_id)
    return SettingsOut.of(await svc.get_settings(user.user_id, pick_locale(accept_language)))


@router.get("/today", response_model=TodayOut, responses=ERR, operation_id="study_plan_today")
async def today(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> TodayOut:
    return TodayOut.of(await svc.today(user.user_id, pick_locale(accept_language)))


@router.get("/week", response_model=RangeOut, responses=ERR, operation_id="study_plan_week")
async def week(
    user: CurrentUser,
    svc: PlanServiceDep,
    start: Annotated[date | None, Query()] = None,
    accept_language: AcceptLanguage = None,
) -> RangeOut:
    return RangeOut.of(await svc.week(user.user_id, start, pick_locale(accept_language)))


@router.get("/month", response_model=RangeOut, responses=ERR, operation_id="study_plan_month")
async def month(
    user: CurrentUser,
    svc: PlanServiceDep,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
    accept_language: AcceptLanguage = None,
) -> RangeOut:
    return RangeOut.of(await svc.month(user.user_id, year, month, pick_locale(accept_language)))


@router.post(
    "/tasks/{task_id}/complete",
    response_model=TaskOut,
    responses=ERR,
    operation_id="study_plan_complete_task",
)
async def complete_task(
    task_id: UUID, user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> TaskOut:
    return TaskOut.of(await svc.complete_task(user.user_id, task_id, pick_locale(accept_language)))


@router.get("/home", response_model=HomeOut, responses=ERR, operation_id="study_plan_home")
async def home(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> HomeOut:
    return HomeOut.of(await svc.home(user.user_id, pick_locale(accept_language)))


@router.get(
    "/daily-questions",
    response_model=DailyQuestionsOut,
    responses=ERR,
    operation_id="study_plan_daily_questions",
)
async def daily_questions(user: CurrentUser, svc: PlanServiceDep) -> DailyQuestionsOut:
    return DailyQuestionsOut.of(await svc.daily_questions(user.user_id))


@router.post(
    "/daily-questions/{question_id}/answer",
    response_model=DailyAnswerOut,
    responses=ERR,
    operation_id="study_plan_answer_daily_question",
)
async def answer_daily_question(
    question_id: UUID, body: DailyAnswerIn, user: CurrentUser, svc: PlanServiceDep
) -> DailyAnswerOut:
    g = await svc.answer_daily_question(user.user_id, question_id, body.response)
    return DailyAnswerOut(correct=g.correct, correct_response=g.correct_response)


@router.get(
    "/analytics", response_model=AnalyticsOut, responses=ERR, operation_id="study_plan_analytics"
)
async def analytics(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> AnalyticsOut:
    return AnalyticsOut.of(await svc.analytics(user.user_id, pick_locale(accept_language)))
