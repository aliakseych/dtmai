from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.modules.study_plan.domain.errors import ExamDateTooSoon, NoActiveSubjects
from app.modules.study_plan.domain.generator import GenInput, SubjectInput, generate, plan_end_for
from app.modules.study_plan.domain.models import TaskKind

TODAY = date(2027, 3, 1)  # Monday
EXAM = date(2027, 7, 25)
MATH, PHYS, IQ = uuid4(), uuid4(), uuid4()


def _subjects(lessons: int = 200, due: int = 0) -> tuple[SubjectInput, ...]:
    return tuple(
        SubjectInput(s, pts, 0.3, tuple(uuid4() for _ in range(lessons)), due_reviews=due)
        for s, pts in ((MATH, 62.0), (PHYS, 62.0), (IQ, 22.0))
    )


def _inp(**kw) -> GenInput:
    base = dict(
        today=TODAY,
        start=TODAY,
        exam_date=EXAM,
        taper_days=6,
        school_minutes=45,
        weekend_minutes=90,
        language="uz",
        subjects=_subjects(),
    )
    base.update(kw)
    return GenInput(**base)


def test_day_minutes_respect_school_weekend_and_cap() -> None:
    tasks = generate(_inp(school_minutes=45, weekend_minutes=300))
    per_day: dict[date, int] = {}
    for t in tasks:
        per_day[t.day] = per_day.get(t.day, 0) + t.est_minutes
    for day, minutes in per_day.items():
        limit = 150 if day.weekday() >= 5 else 45
        assert minutes <= limit
    sat = next(d for d in per_day if d.weekday() == 5)
    assert per_day[sat] > 45


def test_weekend_uses_weekend_minutes() -> None:
    tasks = generate(_inp(weekend_minutes=90))
    sat = next(t.day for t in tasks if t.day.weekday() == 5)
    assert 60 < sum(t.est_minutes for t in tasks if t.day == sat) <= 90


@pytest.mark.parametrize("taper", [5, 6, 7])
def test_plan_ends_before_exam(taper: int) -> None:
    tasks = generate(_inp(taper_days=taper))
    assert max(t.day for t in tasks) <= EXAM - timedelta(days=taper)
    assert plan_end_for(EXAM, taper) == EXAM - timedelta(days=taper)


def test_taper_is_clamped() -> None:
    assert plan_end_for(EXAM, 1) == EXAM - timedelta(days=5)
    assert plan_end_for(EXAM, 30) == EXAM - timedelta(days=7)


def test_iq_always_scheduled() -> None:
    tasks = generate(_inp())
    assert any(t.subject_id == IQ and t.kind != TaskKind.RUSH for t in tasks)


def test_only_given_subjects_planned() -> None:
    subs = tuple(s for s in _subjects() if s.subject_id != PHYS)
    assert PHYS not in {t.subject_id for t in generate(_inp(subjects=subs))}


def test_every_day_ends_with_rush() -> None:
    tasks = generate(_inp())
    last: dict[date, TaskKind] = {}
    for t in tasks:
        last[t.day] = t.kind
    assert set(last.values()) == {TaskKind.RUSH}


def test_review_first_when_due() -> None:
    tasks = generate(_inp(subjects=_subjects(due=40)))
    day0 = [t for t in tasks if t.day == TODAY]
    assert day0[0].kind == TaskKind.REVIEW and day0[0].target["count"] == 15


def test_weekly_mock_on_sunday_only_with_blueprint() -> None:
    bp = uuid4()
    with_mock = generate(_inp(mock_blueprint_id=bp, mock_minutes=120, weekend_minutes=150))
    mocks = [t for t in with_mock if t.kind == TaskKind.MOCK]
    assert mocks and all(t.day.weekday() == 6 and t.est_minutes == 120 for t in mocks)
    assert all(t.day - TODAY >= timedelta(days=7) for t in mocks)
    assert not [t for t in generate(_inp()) if t.kind == TaskKind.MOCK]


def test_drills_after_lessons_run_out() -> None:
    tasks = generate(_inp(subjects=_subjects(lessons=1)))
    assert any(t.kind == TaskKind.DRILL for t in tasks)


def test_used_minutes_reduce_budget() -> None:
    tasks = generate(_inp(used_minutes={TODAY: 45}))
    assert not [t for t in tasks if t.day == TODAY]


def test_replan_starts_today_not_start() -> None:
    later = TODAY + timedelta(days=30)
    assert min(t.day for t in generate(_inp(today=later))) == later


def test_exam_too_soon() -> None:
    with pytest.raises(ExamDateTooSoon):
        generate(_inp(today=EXAM - timedelta(days=3)))


def test_no_subjects() -> None:
    with pytest.raises(NoActiveSubjects):
        generate(_inp(subjects=()))
