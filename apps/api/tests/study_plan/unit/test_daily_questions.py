from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.study_plan.application.service import PlanService
from app.modules.study_plan.domain.errors import DailyQuestionAnswered
from app.modules.study_plan.ports import DailyGrade
from app.shared.errors import DomainError

DAY = date(2027, 3, 1)


class _Repo:
    def __init__(self, ids=None):
        self.ids = ids
        self.answered: set = set()
        self.saved = 0

    async def get_plan(self, user_id):
        return SimpleNamespace(settings=SimpleNamespace(direction_code="d", language="uz"))

    async def get_daily_set(self, user_id, day):
        return self.ids

    async def save_daily_set(self, user_id, day, ids):
        self.saved += 1
        self.ids = ids

    async def claim_daily_answer(self, user_id, day, question_id):
        if question_id in self.answered:
            return False
        self.answered.add(question_id)
        return True


class _Questions:
    async def pick(self, *a):
        return []

    async def get(self, ids):
        return []

    async def grade(self, question_id, response):
        return DailyGrade(True, {})


def _svc(repo) -> PlanService:
    svc = PlanService(
        repo,
        None,
        None,
        None,
        _Questions(),
        None,  # type: ignore[arg-type]
        now=lambda: datetime(2027, 3, 1, 9, tzinfo=UTC),
        max_day_minutes=150,
        dream=None,  # type: ignore[arg-type]
    )

    async def _profile(code):
        return None

    svc._profile = _profile  # type: ignore[method-assign]
    svc._plannable = lambda plan, profile: (None, [])  # type: ignore[method-assign]
    return svc


async def test_daily_answer_cannot_be_replayed():
    q = uuid4()
    svc = _svc(_Repo([q]))
    assert (await svc.answer_daily_question(uuid4(), q, {})).correct
    with pytest.raises(DailyQuestionAnswered) as e:
        await svc.answer_daily_question(uuid4(), q, {})
    assert isinstance(e.value, DomainError) and e.value.status == 409


async def test_empty_daily_set_is_not_frozen_for_the_day():
    repo = _Repo(None)
    view = await _svc(repo).daily_questions(uuid4())
    assert view.questions == () and repo.saved == 0
