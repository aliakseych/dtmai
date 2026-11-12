import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.modules.study_plan.application.views import (
    AnalyticsView,
    DailyQuestionsView,
    DayView,
    DreamGapView,
    HomeView,
    MockTrendPoint,
    RangeView,
    SectionView,
    SettingsCmd,
    SettingsView,
    SubjectMastery,
    TaskView,
    TodayView,
)
from app.modules.study_plan.domain.errors import (
    DailyQuestionAnswered,
    DirectionNotFound,
    ExamDateTooSoon,
    NoActiveSubjects,
    PlanNotFound,
    QuestionNotInSet,
    TaskAlreadyDone,
    TaskNotFound,
    TaskNotUndoable,
)
from app.modules.study_plan.domain.exam import (
    ROLE_CREATIVE,
    ExamProfile,
    exemptions,
    resolve_subject,
)
from app.modules.study_plan.domain.gap import compute_gap
from app.modules.study_plan.domain.generator import (
    GenInput,
    SubjectInput,
    generate,
    plan_end_for,
)
from app.modules.study_plan.domain.models import (
    MAX_START_AHEAD_DAYS,
    Plan,
    PlanSettings,
    Task,
    TaskKind,
    TaskStatus,
)
from app.modules.study_plan.domain.prediction import countdown, predicted_score
from app.modules.study_plan.ports import (
    CatalogPort,
    DailyGrade,
    DreamPort,
    EntitlementPort,
    ExamRulesPort,
    LearningPort,
    PlanRepository,
    QuestionPort,
    SubjectInfo,
)
from app.shared.errors import DomainError, NotFound, ValidationFailed

log = logging.getLogger(__name__)

TASHKENT = ZoneInfo("Asia/Tashkent")
ANALYTICS_FEATURE = "study_plan_analytics"
DEFAULT_MAX_SCORE = 146.0  # lyceum exam maximum, used before a plan names its profile
DAILY_QUESTION_COUNT = 3
# Learning session modes that complete the task of the same kind.
MODE_TO_KIND = {
    "lesson": TaskKind.LESSON,
    "drill": TaskKind.DRILL,
    "review": TaskKind.REVIEW,
    "rush": TaskKind.RUSH,
}


def _name(names: dict[str, str], locale: str) -> str | None:
    return names.get(locale) or names.get("en") or next(iter(names.values()), None)


class PlanService:
    def __init__(
        self,
        repo: PlanRepository,
        exam: ExamRulesPort,
        learning: LearningPort,
        catalog: CatalogPort,
        questions: QuestionPort,
        entitlements: EntitlementPort,
        now: Callable[[], datetime],
        max_day_minutes: int,
        dream: DreamPort,
    ) -> None:
        self._r = repo
        self._exam = exam
        self._learn = learning
        self._cat = catalog
        self._q = questions
        self._ent = entitlements
        self._now = now
        self._max_day = max_day_minutes
        self._dream = dream

    def _today(self) -> date:
        return self._now().astimezone(TASHKENT).date()

    async def _profile(self, direction_code: str) -> ExamProfile:
        profile = await self._exam.profile(direction_code)
        if profile is None:
            raise DirectionNotFound("direction not found")
        return profile

    async def _plan(self, user_id: UUID) -> Plan:
        plan = await self._r.get_plan(user_id)
        if plan is None:
            raise PlanNotFound("no study plan yet")
        return plan

    # ---- settings & generation ------------------------------------------------------------

    async def save_settings(self, user_id: UUID, cmd: SettingsCmd) -> Plan:
        """Store the wizard answers and (re)build the schedule from today."""
        profile = await self._profile(cmd.direction_code)
        exam_date = cmd.exam_date or profile.exam_date
        if exam_date is None:
            raise ValidationFailed("exam date is unknown", code="exam_date_required")
        today = self._today()
        start = cmd.start_date or today
        if start > today + timedelta(days=MAX_START_AHEAD_DAYS):
            raise ValidationFailed("start date is too far ahead", code="start_date_too_far")
        settings = PlanSettings(
            direction_code=cmd.direction_code,
            language=cmd.language,
            start_date=start,
            exam_date=exam_date,
            minutes_school_day=cmd.minutes_school_day,
            minutes_weekend_day=cmd.minutes_weekend_day,
            target_lyceum_ids=cmd.target_lyceum_ids,
            certificates=cmd.certificates,
            choice_subject_id=cmd.choice_subject_id,
            study_time=cmd.study_time,
            study_days=tuple(sorted(set(cmd.study_days))),
        )
        plan = await self._r.get_plan_for_update(user_id)
        if plan is None:
            plan = Plan(uuid4(), user_id, settings)
            if not await self._r.insert_plan(plan):
                # A double-submitted first save won the insert race: update its row instead.
                existing = await self._r.get_plan_for_update(user_id)
                if existing is None:
                    raise PlanNotFound("no study plan yet")
                plan = existing
                plan.settings = settings
        else:
            plan.settings = settings
        await self._regenerate(plan, profile, today)
        return plan

    async def generate(self, user_id: UUID) -> Plan:
        """On-demand replan: keeps what is done, rebuilds everything still open from today."""
        plan = await self._plan(user_id)
        await self._regenerate(
            plan, await self._profile(plan.settings.direction_code), self._today()
        )
        return plan

    def _plannable(
        self, plan: Plan, profile: ExamProfile
    ) -> tuple[dict[UUID, float], list[tuple[UUID, float]]]:
        """(exempt section -> fraction, [(subject, points)] to study)."""
        st = plan.settings
        exempt = exemptions(profile.sections, profile.cert_rules, st.certificates)
        subjects: dict[UUID, float] = {}
        for s in profile.sections:
            if s.role == ROLE_CREATIVE or s.section_id in exempt:
                continue
            sid = resolve_subject(s, st.choice_subject_id)
            if sid is not None:
                subjects[sid] = subjects.get(sid, 0.0) + s.max_points
        return exempt, list(subjects.items())

    async def _regenerate(self, plan: Plan, profile: ExamProfile, today: date) -> None:
        st = plan.settings
        _, wanted = self._plannable(plan, profile)
        active = {s.id for s in await self._cat.subjects()}
        mastery = await self._learn.mastery(plan.user_id)
        inputs: list[SubjectInput] = []
        for sid, points in wanted:
            if sid not in active:
                continue
            weak = await self._learn.weak_spots(plan.user_id, sid)
            inputs.append(
                SubjectInput(
                    sid,
                    points,
                    mastery.get(sid),
                    tuple(await self._learn.lesson_queue(plan.user_id, sid, st.language)),
                    tuple((w.topic_id, w.type_id) for w in weak),
                    await self._learn.due_reviews(plan.user_id, sid),
                    await self._learn.pool(sid, st.language),
                )
            )
        mock_minutes = 0
        mock_servable = False
        if profile.mock_blueprint_id:
            try:
                mock_minutes = await self._cat.mock_minutes(profile.mock_blueprint_id)
                mock_servable = await self._cat.mock_servable(
                    profile.mock_blueprint_id, st.language
                )
            except NotFound:
                mock_minutes = 0  # blueprint retired: plan without weekly mocks
        end = plan_end_for(st.exam_date, profile.taper_days)
        first = max(today, st.start_date)
        used = await self._r.used_minutes(plan.id, first, end)
        planned = generate(
            GenInput(
                today=today,
                start=st.start_date,
                exam_date=st.exam_date,
                taper_days=profile.taper_days,
                school_minutes=st.minutes_school_day,
                weekend_minutes=st.minutes_weekend_day,
                language=st.language,
                subjects=tuple(inputs),
                mock_blueprint_id=profile.mock_blueprint_id,
                mock_minutes=mock_minutes,
                mock_servable=mock_servable,
                max_day_minutes=self._max_day,
                used_minutes=used,
            )
        )
        # Writes only after a successful generation, so a failure leaves the old plan intact.
        if plan.plan_end is not None:
            plan.version += 1
        plan.plan_end = end
        plan.last_replanned_on = today
        await self._r.save_plan(plan)
        await self._r.mark_missed_before(plan.id, today)
        await self._r.delete_todo_from(plan.id, today)
        await self._r.add_tasks(
            [
                Task(
                    uuid4(),
                    plan.id,
                    p.day,
                    p.position,
                    p.kind,
                    p.subject_id,
                    p.target,
                    p.est_minutes,
                )
                for p in planned
            ]
        )

    async def stale_plan_users(self) -> list[UUID]:
        """User ids whose running plan was not replanned today."""
        return await self._r.stale_plans(self._today())

    async def replan_user(self, user_id: UUID) -> bool:
        """Nightly refresh of one plan (mastery and due reviews moved); False when skipped."""
        today = self._today()
        plan = await self._r.get_plan_for_update(user_id)
        if plan is None or not self._needs_replan(plan, today):
            return False
        try:
            await self._regenerate(plan, await self._profile(plan.settings.direction_code), today)
        except DomainError:
            log.warning("study plan replan skipped", extra={"user_id": str(user_id)})
            return False
        return True

    # ---- reads ----------------------------------------------------------------------------

    async def _names(self) -> dict[UUID, SubjectInfo]:
        return {s.id: s for s in await self._cat.subjects()}

    def _views(
        self, tasks: list[Task], subjects: dict[UUID, SubjectInfo], locale: str
    ) -> tuple[TaskView, ...]:
        return tuple(
            TaskView.of(
                t, _name(subjects[t.subject_id].names, locale) if t.subject_id in subjects else None
            )
            for t in tasks
        )

    async def get_settings(self, user_id: UUID, locale: str) -> SettingsView:
        plan = await self._plan(user_id)
        profile = await self._exam.profile(plan.settings.direction_code)
        if profile is None:  # direction retired since the plan was saved: still show the plan
            return SettingsView(plan.settings, plan.plan_end, (), ())
        exempt = exemptions(profile.sections, profile.cert_rules, plan.settings.certificates)
        subjects = await self._names()
        sections: list[SectionView] = []
        for s in profile.sections:
            sid = resolve_subject(s, plan.settings.choice_subject_id)
            info = subjects.get(sid) if sid else None
            sections.append(
                SectionView(
                    s.section_id,
                    s.role,
                    sid,
                    _name(info.names, locale) if info else None,
                    s.max_points,
                    s.section_id in exempt,
                    s.role != ROLE_CREATIVE and (info is not None or bool(s.subject_options)),
                    s.choice_group,
                    s.subject_options,
                )
            )
        return SettingsView(plan.settings, plan.plan_end, tuple(exempt), tuple(sections))

    async def _fresh_plan(self, user_id: UUID) -> Plan:
        """The plan, replanned once per day on first touch (the nightly job may not have run)."""
        plan = await self._plan(user_id)
        today = self._today()
        if not self._needs_replan(plan, today):
            return plan
        # Lock the row and re-check: a parallel /home and /today must not both regenerate.
        locked = await self._r.get_plan_for_update(user_id)
        if locked is None:
            raise PlanNotFound("no study plan yet")
        plan = locked
        if self._needs_replan(plan, today):
            try:
                await self._regenerate(
                    plan, await self._profile(plan.settings.direction_code), today
                )
            except (ExamDateTooSoon, NoActiveSubjects):
                pass  # keep serving the stored plan
        return plan

    @staticmethod
    def _needs_replan(plan: Plan, today: date) -> bool:
        return (
            plan.plan_end is not None
            and today <= plan.plan_end
            and (plan.last_replanned_on is None or plan.last_replanned_on < today)
        )

    async def today(self, user_id: UUID, locale: str) -> TodayView:
        plan = await self._fresh_plan(user_id)
        today = self._today()
        tasks = await self._r.tasks_between(plan.id, today, today)
        assert plan.plan_end is not None  # _fresh_plan only serves generated plans
        days_left = max((plan.settings.exam_date - today).days, 0)
        return TodayView(
            today,
            self._views(tasks, await self._names(), locale),
            days_left,
            plan.plan_end,
            not tasks,
        )

    async def _range(self, user_id: UUID, start: date, end: date, locale: str) -> RangeView:
        plan = await self._fresh_plan(user_id)
        tasks = await self._r.tasks_between(plan.id, start, end)
        subjects = await self._names()
        days: list[DayView] = []
        d = start
        while d <= end:
            day_tasks = [t for t in tasks if t.day == d]
            days.append(
                DayView(
                    d,
                    sum(t.est_minutes for t in day_tasks),
                    sum(t.status is TaskStatus.DONE for t in day_tasks),
                    len(day_tasks),
                    self._views(day_tasks, subjects, locale),
                )
            )
            d += timedelta(days=1)
        return RangeView(
            tuple(days), plan.settings.exam_date, plan.plan_end or plan.settings.exam_date
        )

    async def week(self, user_id: UUID, start: date | None, locale: str) -> RangeView:
        first = start or self._today() - timedelta(days=self._today().weekday())
        return await self._range(user_id, first, first + timedelta(days=6), locale)

    async def month(
        self, user_id: UUID, year: int | None, month: int | None, locale: str
    ) -> RangeView:
        today = self._today()
        y, m = (year or today.year), (month or today.month)
        try:
            first = date(y, m, 1)
        except ValueError:
            raise ValidationFailed("invalid month", code="invalid_month") from None
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        return await self._range(user_id, first, nxt - timedelta(days=1), locale)

    async def complete_task(self, user_id: UUID, task_id: UUID, locale: str) -> TaskView:
        task = await self._r.get_task(user_id, task_id)
        if task is None:
            raise TaskNotFound("task not found")
        if task.status is TaskStatus.DONE:
            raise TaskAlreadyDone("task already done")
        task.complete(self._now(), None)
        await self._r.save_task(task)
        return self._views([task], await self._names(), locale)[0]

    async def uncomplete_task(self, user_id: UUID, task_id: UUID, locale: str) -> TaskView:
        task = await self._r.get_task(user_id, task_id)
        if task is None:
            raise TaskNotFound("task not found")
        if not task.undoable:
            raise TaskNotUndoable("only a manually completed task can be undone")
        task.reopen()
        await self._r.save_task(task)
        return self._views([task], await self._names(), locale)[0]

    # ---- events ---------------------------------------------------------------------------

    async def on_activity(
        self, event_id: UUID, user_id: UUID, kind: TaskKind, blueprint_id: UUID | None = None
    ) -> None:
        """A learning session/mock finished: tick the matching open task. Idempotent per event."""
        plan = await self._r.get_plan(user_id)
        if plan is None or await self._r.has_source(plan.id, event_id):
            return
        task = await self._r.first_open(plan.id, kind, self._today(), blueprint_id=blueprint_id)
        if task is None:
            return
        task.complete(self._now(), event_id)
        await self._r.save_task(task)

    async def merge_guest(self, from_id: UUID, into_id: UUID) -> None:
        if from_id != into_id:
            await self._r.merge(from_id, into_id)

    async def today_counts(self, user_id: UUID) -> tuple[int, int]:
        """(open, total) tasks planned for today; (0, 0) without a plan."""
        plan = await self._r.get_plan(user_id)
        if plan is None:
            return 0, 0
        today = self._today()
        tasks = await self._r.tasks_between(plan.id, today, today)
        return sum(t.status is TaskStatus.TODO for t in tasks), len(tasks)

    # ---- home -----------------------------------------------------------------------------

    async def _predicted(
        self, user_id: UUID, plan: Plan, profile: ExamProfile
    ) -> tuple[float | None, dict[UUID, float | None], dict[UUID, float]]:
        exempt = exemptions(profile.sections, profile.cert_rules, plan.settings.certificates)
        mastery = await self._learn.mastery(user_id)
        score: float | None = None
        if exempt or any(v is not None for v in mastery.values()):
            score = predicted_score(
                profile.sections,
                exempt,
                mastery,
                {s.section_id: plan.settings.choice_subject_id for s in profile.sections},
                profile.max_score,
            )
        return score, mastery, exempt

    async def home(self, user_id: UUID, locale: str) -> HomeView:
        if await self._r.get_plan(user_id) is None:
            return HomeView(configured=False)
        plan = await self._fresh_plan(user_id)
        profile = await self._profile(plan.settings.direction_code)
        today = self._today()
        cd = countdown(today, plan.settings.exam_date, profile.taper_days)
        score, _, _ = await self._predicted(user_id, plan, profile)
        tasks = await self._r.tasks_between(plan.id, today, today)
        return HomeView(
            True,
            cd.days_left,
            cd.exam_date,
            cd.plan_end,
            cd.phase,
            score,
            profile.max_score,
            sum(t.status is TaskStatus.DONE for t in tasks),
            len(tasks),
            sum(t.est_minutes for t in tasks),
            self._views(tasks, await self._names(), locale),
            profile.date_verified and plan.settings.exam_date == profile.exam_date,
        )

    # ---- dream lyceum gap -----------------------------------------------------------------

    async def dream_gap(self, user_id: UUID, locale: str) -> DreamGapView:
        """Predicted score vs. the dream lyceum's bar, plus the weakest topic as the next step."""
        target = await self._dream.target(user_id)
        if target is None:
            return DreamGapView(None, None, None)
        plan = await self._r.get_plan(user_id)
        if plan is None:
            gap = compute_gap(
                None, DEFAULT_MAX_SCORE, target.passing_score, target.competition_ratio
            )
            return DreamGapView(target.lyceum_id, target.year, gap)
        profile = await self._profile(plan.settings.direction_code)
        score, mastery, exempt = await self._predicted(user_id, plan, profile)
        gap = compute_gap(score, profile.max_score, target.passing_score, target.competition_ratio)
        topic_id: UUID | None = None
        topic_name: str | None = None
        subject_id: UUID | None = None
        if gap.next_points is not None:
            studied = {
                sid
                for s in profile.sections
                if s.section_id not in exempt
                and (sid := resolve_subject(s, plan.settings.choice_subject_id)) is not None
            }
            for sid in sorted(studied, key=lambda x: mastery.get(x) or 0.0):
                spots = [w for w in await self._learn.weak_spots(user_id, sid) if w.topic_id]
                if spots:
                    subject_id, topic_id = sid, spots[0].topic_id
                    break
            if topic_id is not None:
                try:
                    topic_name = _name(await self._cat.topic_names(topic_id), locale)
                except NotFound:
                    topic_id = subject_id = None
        return DreamGapView(target.lyceum_id, target.year, gap, topic_id, topic_name, subject_id)

    # ---- daily questions ------------------------------------------------------------------

    async def daily_questions(self, user_id: UUID) -> DailyQuestionsView:
        plan = await self._plan(user_id)
        today = self._today()
        ids = await self._r.get_daily_set(user_id, today)
        if ids is None:
            profile = await self._profile(plan.settings.direction_code)
            _, wanted = self._plannable(plan, profile)
            chosen: list[UUID] = []
            for _round in range(DAILY_QUESTION_COUNT):
                for sid, _points in wanted:
                    if len(chosen) == DAILY_QUESTION_COUNT:
                        break
                    picked = await self._q.pick(sid, plan.settings.language, 1, chosen)
                    chosen.extend(q.id for q in picked)
                if len(chosen) == DAILY_QUESTION_COUNT or not wanted:
                    break
            if not chosen:  # nothing to ask yet: do not freeze an empty set for the day
                return DailyQuestionsView(today, ())
            await self._r.save_daily_set(user_id, today, chosen)
            ids = await self._r.get_daily_set(user_id, today) or chosen
        return DailyQuestionsView(today, tuple(await self._q.get(ids)))

    async def answer_daily_question(
        self, user_id: UUID, question_id: UUID, response: dict[str, Any]
    ) -> DailyGrade:
        today = self._today()
        ids = await self._r.get_daily_set(user_id, today)
        if not ids or question_id not in ids:
            raise QuestionNotInSet("question is not in today's set")
        if not await self._r.claim_daily_answer(user_id, today, question_id):
            raise DailyQuestionAnswered("question already answered today")
        return await self._q.grade(question_id, response)

    # ---- analytics ------------------------------------------------------------------------

    async def analytics(self, user_id: UUID, locale: str) -> AnalyticsView:
        if not await self._ent.has_feature(user_id, ANALYTICS_FEATURE):
            return AnalyticsView(locked=True)
        plan = await self._plan(user_id)
        subjects = await self._names()
        mastery = await self._learn.mastery(user_id)
        counts = await self._r.count_by_status(
            plan.id, plan.settings.start_date, plan.plan_end or plan.settings.exam_date
        )
        done, done_min = counts.get(TaskStatus.DONE, (0, 0))
        missed, _ = counts.get(TaskStatus.MISSED, (0, 0))
        todo, _ = counts.get(TaskStatus.TODO, (0, 0))
        planned_min = sum(m for _, m in counts.values())
        closed = done + missed
        return AnalyticsView(
            False,
            tuple(
                SubjectMastery(
                    sid, _name(subjects[sid].names, locale) if sid in subjects else None, m
                )
                for sid, m in mastery.items()
            ),
            tuple(
                MockTrendPoint(m.taken_at, m.score, m.max_score)
                for m in await self._learn.mocks(user_id)
            ),
            done,
            missed,
            todo,
            done_min,
            planned_min,
            round(done / closed, 3) if closed else 0.0,
        )
