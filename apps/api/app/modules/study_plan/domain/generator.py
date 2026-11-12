"""Deterministic study-plan generation: pure function of inputs, no I/O.

Why deterministic: replanning must be reproducible and testable; the subject mix follows a
deficit rule (largest gap between target share and time already spent) instead of randomness.
"""

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any
from uuid import UUID

from app.modules.study_plan.domain.errors import ExamDateTooSoon, NoActiveSubjects
from app.modules.study_plan.domain.models import TaskKind
from app.modules.study_plan.domain.prediction import clamp_taper

MAX_DAY_MINUTES = 150
LESSON_MIN = 10
RUSH_MIN = 2
DRILL_MIN_FIT = 13  # 8 fixed + 5 questions
MIN_TASK = 10
REVIEW_FIRST_DAY = 15
REVIEW_DAILY = 8
DRILL_COUNT = 10
MAX_PER_SUBJECT_DAY = 5
MOCK_MIN_GAP_DAYS = 7
SUNDAY = 6
WEEKEND = (5, 6)


UNLIMITED_POOL = 10**9
DRILL_MIN_POOL = 5  # fewer verified questions than this cannot fill a drill session
RUSH_MIN_POOL = 1


@dataclass(frozen=True, slots=True)
class SubjectInput:
    subject_id: UUID
    points: float
    mastery: float | None
    lessons: tuple[UUID, ...] = ()  # remaining lesson queue, in order
    weak: tuple[tuple[UUID | None, UUID | None], ...] = ()  # (topic_id, type_id), weakest first
    due_reviews: int = 0
    # Verified questions available in the plan language: drills/rush need a servable pool.
    pool: int = UNLIMITED_POOL


@dataclass(frozen=True, slots=True)
class GenInput:
    today: date
    start: date
    exam_date: date
    taper_days: int
    school_minutes: int
    weekend_minutes: int
    language: str
    subjects: tuple[SubjectInput, ...]
    mock_blueprint_id: UUID | None = None
    mock_minutes: int = 0
    mock_servable: bool = True  # every blueprint section can be filled from verified questions
    max_day_minutes: int = MAX_DAY_MINUTES
    used_minutes: dict[date, int] = field(default_factory=dict)  # already-planned/done per day


@dataclass(frozen=True, slots=True)
class PlannedTask:
    day: date
    position: int
    kind: TaskKind
    subject_id: UUID | None
    target: dict[str, Any]
    est_minutes: int


def plan_end_for(exam_date: date, taper_days: int) -> date:
    return exam_date - timedelta(days=clamp_taper(taper_days))


def _weights(subjects: tuple[SubjectInput, ...]) -> dict[UUID, float]:
    raw = {
        s.subject_id: s.points
        * (0.25 + (1 - min(max(s.mastery if s.mastery is not None else 0.4, 0), 1)))
        for s in subjects
    }
    total = sum(raw.values()) or 1.0
    return {k: v / total for k, v in raw.items()}


def generate(inp: GenInput) -> list[PlannedTask]:
    if not inp.subjects:
        raise NoActiveSubjects("no subject with content to plan")
    first = max(inp.today, inp.start)
    end = plan_end_for(inp.exam_date, inp.taper_days)
    if first > end:
        raise ExamDateTooSoon("exam is too close to build a plan")

    weights = _weights(inp.subjects)
    by_id = {s.subject_id: s for s in inp.subjects}
    queues = {s.subject_id: list(s.lessons) for s in inp.subjects}
    weak_i = {s.subject_id: 0 for s in inp.subjects}
    spent = {s.subject_id: 0 for s in inp.subjects}
    due_left = {s.subject_id: s.due_reviews for s in inp.subjects}
    out: list[PlannedTask] = []

    def servable(sid: UUID, *, rush: bool) -> bool:
        if rush:
            return by_id[sid].pool >= RUSH_MIN_POOL
        return bool(queues[sid]) or by_id[sid].pool >= DRILL_MIN_POOL

    def pick(per_day: dict[UUID, int], *, rush: bool = False) -> UUID | None:
        cap = MAX_PER_SUBJECT_DAY if len(by_id) > 1 else 10**6
        total = sum(spent.values()) + 1
        cands = [s for s in by_id if per_day.get(s, 0) < cap and servable(s, rush=rush)]
        if not cands:
            return None
        return max(cands, key=lambda s: (weights[s] * total - spent[s], weights[s]))

    day = first
    while day <= end:
        cap = min(
            inp.weekend_minutes if day.weekday() in WEEKEND else inp.school_minutes,
            inp.max_day_minutes,
        )
        budget = cap - inp.used_minutes.get(day, 0)
        tasks: list[PlannedTask] = []

        def add(kind: TaskKind, sid: UUID | None, target: dict[str, Any], minutes: int) -> None:
            nonlocal budget
            tasks.append(PlannedTask(day, len(tasks), kind, sid, target, minutes))
            budget -= minutes
            if sid is not None and kind != TaskKind.MOCK:
                spent[sid] += minutes

        is_mock_day = (
            inp.mock_blueprint_id is not None
            and inp.mock_servable
            and day.weekday() == SUNDAY
            and (day - inp.start).days >= MOCK_MIN_GAP_DAYS
            and 0 < inp.mock_minutes <= inp.max_day_minutes
            and day not in inp.used_minutes
        )
        if is_mock_day:
            assert inp.mock_blueprint_id is not None
            tasks.append(
                PlannedTask(
                    day,
                    0,
                    TaskKind.MOCK,
                    None,
                    {"blueprint_id": str(inp.mock_blueprint_id)},
                    inp.mock_minutes,
                )
            )
            out.extend(tasks)
            day += timedelta(days=1)
            continue

        per_day: dict[UUID, int] = {}

        # 1. spaced-repetition review first: it decays if postponed.
        due_sid = max(due_left, key=lambda s: due_left[s])
        if due_left[due_sid] > 0 and budget - RUSH_MIN >= MIN_TASK:
            count = min(REVIEW_FIRST_DAY if day == first else REVIEW_DAILY, due_left[due_sid])
            minutes = min(max(math.ceil(count * 0.7), 3), budget - RUSH_MIN)
            add(TaskKind.REVIEW, due_sid, {"subject_id": str(due_sid), "count": count}, minutes)
            due_left[due_sid] -= count
            per_day[due_sid] = 1

        # 2. lessons, then drills once a subject's path is exhausted.
        while budget - RUSH_MIN >= MIN_TASK:
            sid = pick(per_day)
            if sid is None:
                break
            queue = queues[sid]
            if queue:
                lesson = queue.pop(0)
                add(
                    TaskKind.LESSON,
                    sid,
                    {"lesson_id": str(lesson), "language": inp.language},
                    LESSON_MIN,
                )
            else:
                if budget - RUSH_MIN < DRILL_MIN_FIT:
                    break
                count = min(DRILL_COUNT, max(int((budget - RUSH_MIN - 8) / 0.7), 5))
                weak = by_id[sid].weak
                topic_id, type_id = weak[weak_i[sid] % len(weak)] if weak else (None, None)
                weak_i[sid] += 1
                target: dict[str, Any] = {"subject_id": str(sid), "count": count}
                if topic_id:
                    target["topic_id"] = str(topic_id)
                if type_id:
                    target["type_id"] = str(type_id)
                add(TaskKind.DRILL, sid, target, 8 + math.ceil(0.7 * count))
            per_day[sid] = per_day.get(sid, 0) + 1

        # 3. rush closes the day: free, 60 s, earns league XP.
        if budget >= RUSH_MIN:
            rsid = pick({}, rush=True)
            if rsid is not None:
                add(TaskKind.RUSH, rsid, {"subject_id": str(rsid)}, RUSH_MIN)

        out.extend(tasks)
        day += timedelta(days=1)
    return out
