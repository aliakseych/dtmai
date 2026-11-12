from datetime import date, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field, field_validator

from app.interfaces.http.v1._bounds import check_response_size
from app.interfaces.http.v1._media import MediaOut, to_media
from app.modules.study_plan.application.views import (
    AnalyticsView,
    DailyQuestionsView,
    DayView,
    DreamGapView,
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
    cert_type: str = Field(max_length=50)
    value: float
    language_subject_id: UUID | None = None


class SettingsIn(BaseModel):
    direction_code: str = Field(max_length=50)
    language: str = Field(max_length=10, description="Education language: uz | ru")
    minutes_school_day: int = Field(45, ge=5, le=600)
    minutes_weekend_day: int = Field(90, ge=5, le=600)
    target_lyceum_ids: list[UUID] = Field([], max_length=20)
    certificates: list[CertificateIO] = Field([], max_length=20)
    choice_subject_id: UUID | None = None
    exam_date: date | None = Field(None, description="Defaults to the exam profile's date")
    start_date: date | None = Field(None, description="Defaults to today")
    study_time: str | None = Field(
        None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="Planned study time, HH:MM"
    )
    study_days: list[Annotated[int, Field(ge=0, le=6)]] = Field(
        [], max_length=7, description="Weekdays 0=Mon..6=Sun; empty = every day"
    )

    @field_validator("exam_date")
    @classmethod
    def _exam_date_in_range(cls, v: date | None) -> date | None:
        if v is None:
            return v
        today = datetime.now(ZoneInfo("Asia/Tashkent")).date()
        if not today <= v <= today + timedelta(days=731):
            raise ValueError("exam_date must be within the next 2 years")
        return v

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
            study_time=self.study_time,
            study_days=tuple(self.study_days),
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
    study_time: str | None
    study_days: list[int]
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
            study_time=s.study_time,
            study_days=list(s.study_days),
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
    undoable: bool

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
            undoable=t.undoable,
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
    exam_date_verified: bool = Field(description="False: the exam date is an estimate")

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
            exam_date_verified=v.exam_date_verified,
        )


class DreamGapOut(BaseModel):
    lyceum_id: UUID | None = Field(description="None: no dream lyceum chosen yet")
    year: int | None = Field(description="Admission year the benchmark comes from")
    predicted_score: float | None
    max_score: float | None
    passing_score: float | None
    competition_ratio: float | None
    gap: float | None = Field(description="Points still missing; <= 0 when at the bar")
    on_track: bool | None
    milestone: bool = Field(description="Large gap: frame it as the next milestone")
    next_points: float | None
    next_questions: int | None
    weakest_topic_id: UUID | None
    weakest_topic_name: str | None
    weakest_subject_id: UUID | None

    @classmethod
    def of(cls, v: DreamGapView) -> "DreamGapOut":
        g = v.gap
        return cls(
            lyceum_id=v.lyceum_id,
            year=v.year,
            predicted_score=g.predicted_score if g else None,
            max_score=g.max_score if g else None,
            passing_score=g.passing_score if g else None,
            competition_ratio=g.competition_ratio if g else None,
            gap=g.gap if g else None,
            on_track=g.on_track if g else None,
            milestone=g.milestone if g else False,
            next_points=g.next_points if g else None,
            next_questions=g.next_questions if g else None,
            weakest_topic_id=v.weakest_topic_id,
            weakest_topic_name=v.weakest_topic_name,
            weakest_subject_id=v.weakest_subject_id,
        )


class DailyQuestionOut(BaseModel):
    id: UUID
    subject_id: UUID
    kind: str
    stem: str
    media: list[MediaOut]
    payload: dict[str, Any]


class DailyQuestionsOut(BaseModel):
    day: date
    questions: list[DailyQuestionOut]
    answered_ids: list[UUID]

    @classmethod
    def of(cls, v: DailyQuestionsView) -> "DailyQuestionsOut":
        return cls(
            day=v.day,
            answered_ids=list(v.answered),
            questions=[
                DailyQuestionOut(
                    id=q.id,
                    subject_id=q.subject_id,
                    kind=q.kind,
                    stem=q.stem,
                    media=to_media(q.media),
                    payload=q.payload,
                )
                for q in v.questions
            ],
        )


class DailyAnswerIn(BaseModel):
    response: dict[str, Any]

    _cap = field_validator("response")(check_response_size)


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
    start: Annotated[date | None, Query(ge=date(2000, 1, 1), le=date(2100, 12, 31))] = None,
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


@router.post(
    "/tasks/{task_id}/uncomplete",
    response_model=TaskOut,
    responses=ERR,
    operation_id="study_plan_uncomplete_task",
)
async def uncomplete_task(
    task_id: UUID, user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> TaskOut:
    return TaskOut.of(
        await svc.uncomplete_task(user.user_id, task_id, pick_locale(accept_language))
    )


@router.get("/home", response_model=HomeOut, responses=ERR, operation_id="study_plan_home")
async def home(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> HomeOut:
    return HomeOut.of(await svc.home(user.user_id, pick_locale(accept_language)))


@router.get(
    "/dream-gap", response_model=DreamGapOut, responses=ERR, operation_id="study_plan_dream_gap"
)
async def dream_gap(
    user: CurrentUser, svc: PlanServiceDep, accept_language: AcceptLanguage = None
) -> DreamGapOut:
    return DreamGapOut.of(await svc.dream_gap(user.user_id, pick_locale(accept_language)))


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
