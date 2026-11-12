from datetime import datetime, timezone
from uuid import uuid4

from app.modules.study_plan.domain.generator import SubjectInput, generate
from app.modules.study_plan.domain.models import Task, TaskKind, TaskStatus
from tests.study_plan.unit.test_generator import MATH, PHYS, TODAY, _inp


def _subs(pools: dict) -> tuple[SubjectInput, ...]:
    return tuple(SubjectInput(s, 60.0, 0.3, (), pool=pools[s]) for s in (MATH, PHYS))


def test_empty_subject_gets_no_drill_or_rush() -> None:
    tasks = generate(_inp(subjects=_subs({MATH: 50, PHYS: 0})))
    assert tasks
    assert all(t.subject_id != PHYS for t in tasks if t.kind in (TaskKind.DRILL, TaskKind.RUSH))
    assert any(t.subject_id == MATH and t.kind == TaskKind.DRILL for t in tasks)


def test_too_small_pool_skips_drill_but_allows_rush() -> None:
    tasks = generate(_inp(subjects=_subs({MATH: 2, PHYS: 2})))
    assert not [t for t in tasks if t.kind == TaskKind.DRILL]
    assert [t for t in tasks if t.kind == TaskKind.RUSH]


def test_mock_not_planned_when_blueprint_unservable() -> None:
    kw = dict(mock_blueprint_id=uuid4(), mock_minutes=120, weekend_minutes=150)
    assert [t for t in generate(_inp(**kw)) if t.kind == TaskKind.MOCK]
    assert not [t for t in generate(_inp(mock_servable=False, **kw)) if t.kind == TaskKind.MOCK]


def _task() -> Task:
    return Task(uuid4(), uuid4(), TODAY, 0, TaskKind.LESSON, None, {}, 10)


def test_manual_completion_is_undoable() -> None:
    t = _task()
    t.complete(datetime.now(timezone.utc), None)
    assert t.undoable
    t.reopen()
    assert t.status is TaskStatus.TODO and t.done_at is None and not t.undoable


def test_activity_completion_is_not_undoable() -> None:
    t = _task()
    t.complete(datetime.now(timezone.utc), uuid4())
    assert not t.undoable
    assert not _task().undoable
