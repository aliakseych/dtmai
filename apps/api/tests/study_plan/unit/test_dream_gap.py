from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.modules.notify.domain.policy import reminder_due
from app.modules.study_plan.application.service import PlanService
from app.modules.study_plan.domain.gap import compute_gap
from app.modules.study_plan.domain.models import PlanSettings
from app.modules.study_plan.ports import DreamTarget
from app.shared.errors import ValidationFailed


def _settings(**kw) -> PlanSettings:
    return PlanSettings("dir", "uz", date(2027, 3, 1), date(2027, 7, 25), **kw)


# ---- gap computation ---------------------------------------------------------------------


def test_gap_points_and_next_step():
    g = compute_gap(100.0, 146.0, 112.0, 4.2)
    assert g.gap == 12.0 and g.on_track is False and g.milestone is False
    assert g.next_points == 12.0 and g.next_questions == 40
    assert g.competition_ratio == 4.2


def test_gap_closed_when_at_the_bar():
    g = compute_gap(120.0, 146.0, 112.0, 3.0)
    assert g.gap == -8.0 and g.on_track is True
    assert g.next_points is None and g.next_questions is None


def test_big_gap_is_a_milestone_with_a_small_step():
    g = compute_gap(30.0, 146.0, 120.0, None)
    assert g.milestone is True
    assert g.next_points == 12.0  # the step stays reachable, not the whole gap


def test_small_gap_step_is_the_gap():
    g = compute_gap(100.0, 146.0, 104.0, None)
    assert g.next_points == 4.0 and g.next_questions == 13


def test_ratio_only_when_score_or_bar_unknown():
    no_score = compute_gap(None, 146.0, 112.0, 5.0)
    assert no_score.gap is None and no_score.competition_ratio == 5.0
    no_bar = compute_gap(90.0, 146.0, None, 5.0)
    assert no_bar.gap is None and no_bar.on_track is None


# ---- implementation intention storage ----------------------------------------------------


def test_study_intention_round_trips_through_json():
    s = _settings(study_time="18:30", study_days=(0, 2, 4))
    back = PlanSettings.from_json(s.to_json())
    assert back.study_time == "18:30" and back.study_days == (0, 2, 4)


def test_old_settings_json_without_intention_loads():
    d = _settings().to_json()
    d.pop("study_time")
    d.pop("study_days")
    s = PlanSettings.from_json(d)
    assert s.study_time is None and s.study_days == ()


@pytest.mark.parametrize("value", ["7:00", "24:00", "12:60", "ab:cd", "1200"])
def test_invalid_study_time_rejected(value):
    with pytest.raises(ValidationFailed) as e:
        _settings(study_time=value)
    assert e.value.code == "invalid_study_time"


@pytest.mark.parametrize("days", [(7,), (-1,), (1, 1)])
def test_invalid_study_days_rejected(days):
    with pytest.raises(ValidationFailed) as e:
        _settings(study_days=days)
    assert e.value.code == "invalid_study_days"


# ---- reminders honour the intention ------------------------------------------------------


def _tashkent(h, m, day=1):  # 2027-03-01 is a Monday; Tashkent = UTC+5
    return datetime(2027, 3, day, h - 5, m, tzinfo=UTC)


def test_default_slot_is_seven_pm():
    assert reminder_due(_tashkent(19, 10), None)
    assert not reminder_due(_tashkent(18, 40), None)


def test_own_study_time_and_days():
    assert reminder_due(_tashkent(18, 30), "18:30", (0,))
    assert not reminder_due(_tashkent(19, 0), "18:30", (0,))
    assert not reminder_due(_tashkent(18, 30, day=2), "18:30", (0,))  # Tuesday


# ---- dream gap use case ------------------------------------------------------------------


class _Dream:
    def __init__(self, target):
        self._t = target

    async def target(self, user_id):
        return self._t


class _NoPlanRepo:
    async def get_plan(self, user_id):
        return None


def _svc(target) -> PlanService:
    return PlanService(
        _NoPlanRepo(),
        None,
        None,
        None,
        None,
        None,  # type: ignore[arg-type]
        now=lambda: datetime(2027, 3, 1, tzinfo=UTC),
        max_day_minutes=150,
        dream=_Dream(target),
    )


async def test_no_dream_lyceum():
    v = await _svc(None).dream_gap(uuid4(), "en")
    assert v.lyceum_id is None and v.gap is None


async def test_dream_without_plan_still_exposes_the_competition_ratio():
    lid = uuid4()
    v = await _svc(DreamTarget(lid, 2026, 118.0, 6.1)).dream_gap(uuid4(), "en")
    assert v.lyceum_id == lid and v.year == 2026
    assert v.gap is not None and v.gap.gap is None and v.gap.competition_ratio == 6.1
    assert v.gap.passing_score == 118.0
