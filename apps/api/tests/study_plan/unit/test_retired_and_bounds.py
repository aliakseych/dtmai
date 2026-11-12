from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.study_plan.application.service import PlanService
from app.modules.study_plan.infrastructure.adapters import QuestionAdapter
from app.shared.errors import ValidationFailed

DAY = date(2027, 3, 1)
EXAM = date(2027, 6, 1)


class _Repo:
    def __init__(self, ids=None, answered=()):
        self.plan = SimpleNamespace(
            id=uuid4(),
            settings=SimpleNamespace(
                direction_code="gone", language="uz", exam_date=EXAM, choice_subject_id=None
            ),
            plan_end=date(2027, 5, 25),
            last_replanned_on=None,
        )
        self.ids = ids
        self.answered = list(answered)
        self.saved_plans = 0

    async def get_plan(self, user_id):
        return self.plan

    async def get_plan_for_update(self, user_id):
        return self.plan

    async def save_plan(self, plan):
        self.saved_plans += 1

    async def tasks_between(self, plan_id, a, b):
        return []

    async def get_daily_set(self, user_id, day):
        return self.ids

    async def get_daily_answered(self, user_id, day):
        return self.answered


class _Exam:
    async def profile(self, code):
        return None  # retired


class _Cat:
    async def subjects(self):
        return []


class _Q:
    async def pick(self, *a):
        return []

    async def get(self, ids):
        return []


def _svc(repo) -> PlanService:
    return PlanService(
        repo,
        _Exam(),
        None,  # type: ignore[arg-type]
        _Cat(),
        _Q(),
        None,  # type: ignore[arg-type]
        now=lambda: datetime(2027, 3, 1, 9, tzinfo=UTC),
        max_day_minutes=150,
        dream=SimpleNamespace(target=_none),  # type: ignore[arg-type]
    )


async def _none(user_id):
    return None


async def test_retired_direction_still_serves_stored_plan():
    repo = _Repo()
    svc = _svc(repo)
    today = await svc.today(uuid4(), "en")
    assert today.plan_end == repo.plan.plan_end
    await svc.week(uuid4(), None, "en")
    home = await svc.home(uuid4(), "en")
    assert home.configured and home.exam_date == EXAM and home.predicted_score is None
    assert (await svc.daily_questions(uuid4())).questions == ()


async def test_retired_direction_dream_gap():
    repo = _Repo()
    svc = _svc(repo)

    async def target(user_id):
        return SimpleNamespace(
            lyceum_id=uuid4(), year=2026, passing_score=None, competition_ratio=None
        )

    svc._dream = SimpleNamespace(target=target)  # type: ignore[assignment]
    view = await svc.dream_gap(uuid4(), "en")
    assert view.lyceum_id is not None


async def test_failed_replan_stamps_day():
    repo = _Repo()
    await _svc(repo)._fresh_plan(uuid4())
    assert repo.plan.last_replanned_on == DAY and repo.saved_plans == 1


async def test_week_start_is_bounded():
    svc = _svc(_Repo())
    with pytest.raises(ValidationFailed):
        await svc.week(uuid4(), date(9999, 12, 31), "en")


async def test_daily_questions_report_answered_ids():
    q = uuid4()

    class Q(_Q):
        async def get(self, ids):
            return [SimpleNamespace(id=i) for i in ids]

    svc = _svc(_Repo([q], answered=[str(q)]))
    svc._q = Q()  # type: ignore[assignment]
    view = await svc.daily_questions(uuid4())
    assert view.answered == (q,)


async def test_pick_skips_passage_groups_in_query(monkeypatch):
    group, single = uuid4(), uuid4()
    calls: list[list] = []

    def dto(i, kind):
        return SimpleNamespace(id=i, subject_id=uuid4(), kind=kind, stem="s", media=[], payload={})

    async def fake_pick(session, **kw):
        calls.append(list(kw["exclude_ids"]))
        if group in kw["exclude_ids"]:
            return [dto(single, "single_choice")]
        return [dto(group, "passage_group")]

    from app.modules.study_plan.infrastructure import adapters

    monkeypatch.setattr(adapters.bank, "pick_questions", fake_pick)
    out = await QuestionAdapter(None).pick(uuid4(), "uz", 1, [])  # type: ignore[arg-type]
    assert [q.id for q in out] == [single]
    assert group in calls[-1]
