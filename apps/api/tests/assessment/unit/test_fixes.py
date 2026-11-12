import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.assessment.application.service import AssessmentService, served_weight
from app.modules.assessment.domain.attempt import rewardable
from app.modules.assessment.domain.scoring import Scored, score
from app.modules.assessment.ports import Blueprint, Item
from app.modules.study_plan.domain.models import matches_blueprint
from app.shared.errors import Conflict, NotFound

NOW = datetime(2026, 3, 1, 9, tzinfo=UTC)


def item() -> Item:
    return Item(uuid4(), uuid4(), None, uuid4(), "mcq", "uz", "s", [], {}, None)


class FakeContent:
    def __init__(self, bp: Blueprint | None = None, pool: int = 3) -> None:
        self.bp, self.pool = bp, pool
        self.all: dict = {}

    async def blueprint(self, _id):
        return self.bp

    async def pick(self, *, n, **_):
        out = [item() for _ in range(min(n, self.pool))]
        self.all.update({i.id: i for i in out})
        return out

    async def items(self, ids):
        return [self.all[i] for i in ids if i in self.all]

    async def grade(self, *_):
        return SimpleNamespace(correct=True, correct_response={})


class FakeRepo:
    def __init__(self, fail: bool = False) -> None:
        self.added, self.fail, self.hist_args = [], fail, None

    async def active_for(self, *_, **__):
        return None

    async def add(self, a):
        if self.fail:
            raise IntegrityError("x", {}, Exception())
        self.added.append(a)

    async def history(self, user_id, limit, **kw):
        self.hist_args = kw
        return []


def svc(content, repo=None) -> AssessmentService:
    users = SimpleNamespace(target_lyceum_id=lambda _u: None)
    return AssessmentService(repo or FakeRepo(), content, users, lambda: None, None, lambda: NOW)  # type: ignore[arg-type]


def bp(kind="official", status="published", count=5) -> Blueprint:
    sec = {"subject_id": str(uuid4()), "count": count, "weight": 1.0}
    return Blueprint(uuid4(), "c", {}, kind, 1, 60, [sec], None, status)


def run(c):
    return asyncio.run(c)


@pytest.mark.parametrize("kind,status", [("template", "published"), ("official", "draft")])
def test_unrunnable_blueprint_rejected(kind: str, status: str) -> None:
    b = bp(kind, status)
    with pytest.raises(NotFound):
        run(svc(FakeContent(b)).start(uuid4(), b.id, "uz"))


def test_integrity_error_becomes_conflict() -> None:
    b = bp()
    with pytest.raises(Conflict) as e:
        run(svc(FakeContent(b), FakeRepo(fail=True)).start(uuid4(), b.id, "uz"))
    assert e.value.code == "active_attempt_exists"


def test_underfill_scales_weight_and_max_total() -> None:
    assert served_weight(1.0, 3, 5) == pytest.approx(0.6)
    assert served_weight(2.0, 5, 5) == 2.0
    b = bp(count=5)
    repo = FakeRepo()
    run(svc(FakeContent(b, pool=3), repo).start(uuid4(), b.id, "uz"))
    w = repo.added[0].sections[0]["weight"]
    assert w == pytest.approx(0.6)
    res = score([Scored(0, "A", None, "t", True)], [w])
    assert res.max_total == pytest.approx(12.0) and res.total == pytest.approx(12.0)


def test_max_total_ignores_unserved_sections() -> None:
    assert score([Scored(0, "A", None, "t", True)], [1.0, 2.0]).max_total == 20.0


def test_personal_result_has_no_comparison() -> None:
    called = []

    class Users:
        async def target_lyceum_id(self, _u):
            called.append(1)
            return uuid4()

    s = AssessmentService(FakeRepo(), FakeContent(), Users(), lambda: None, None, lambda: NOW)  # type: ignore[arg-type]
    a = SimpleNamespace(kind="personal", user_id=uuid4(), score=5.0)
    r = run(s._result_view(a))  # type: ignore[arg-type]
    assert r.comparison is None and not called


def test_prediction_excludes_personal() -> None:
    repo = FakeRepo()
    run(svc(FakeContent(), repo).prediction(uuid4()))
    assert repo.hist_args == {"exclude_personal": True}


def test_rewardable_threshold() -> None:
    assert not rewardable(0, 10) and not rewardable(3, 10) and not rewardable(0, 0)
    assert rewardable(4, 10) and rewardable(1, 3)


def test_plan_tick_matches_blueprint() -> None:
    bid = uuid4()
    assert matches_blueprint({"blueprint_id": str(bid)}, bid)
    assert not matches_blueprint({"blueprint_id": str(uuid4())}, bid)
    assert not matches_blueprint({}, bid)
    assert matches_blueprint({}, None)


def test_finalize_skips_unanswered_graded_and_reports_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list = []

    async def pub(_s, ev):
        events.append(ev)

    monkeypatch.setattr("app.modules.assessment.application.service.publish", pub)
    from app.modules.assessment.domain.attempt import MockAttempt, deadline_for

    qs = [
        {"id": str(uuid4()), "subject_id": "A", "topic_id": None, "type_id": "t", "section": 0}
        for _ in range(3)
    ]
    a = MockAttempt(
        uuid4(),
        uuid4(),
        "official",
        uuid4(),
        1,
        "uz",
        NOW,
        deadline_for(NOW, 60),
        qs,
        [{"subject_id": "A", "weight": 1.0, "count": 3}],
    )
    a.answers = {qs[0]["id"]: {"v": 1}}

    class Repo(FakeRepo):
        async def save(self, _a):
            pass

    s = svc(FakeContent(), Repo())
    run(s._finalize(a, reason="manual"))
    graded = [e for e in events if e.name == "AttemptGraded"]
    done = [e for e in events if e.name == "MockSubmitted"][0].payload
    assert len(graded) == 1
    assert done["answered"] == 1 and done["questions"] == 3 and done["rewardable"] is True
    assert done["kind"] == "official" and done["blueprint_id"] == str(a.blueprint_id)


def test_unanswered_review_still_carries_correct_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def pub(_s, _ev):
        return None

    monkeypatch.setattr("app.modules.assessment.application.service.publish", pub)
    from app.modules.assessment.domain.attempt import MockAttempt, deadline_for

    q = {"id": str(uuid4()), "subject_id": "A", "topic_id": None, "type_id": "t", "section": 0}
    a = MockAttempt(
        uuid4(), uuid4(), "official", uuid4(), 1, "uz", NOW, deadline_for(NOW, 60), [q],
        [{"subject_id": "A", "weight": 1.0, "count": 1}],
    )  # fmt: skip

    class Content(FakeContent):
        async def grade(self, *_):
            return SimpleNamespace(correct=True, correct_response={"choice": "b"})

    class Repo(FakeRepo):
        async def save(self, _a):
            pass

    run(svc(Content(), Repo())._finalize(a, reason="manual"))
    row = a.result["review"][0]
    assert row["answered"] is False and row["correct"] is False
    assert row["correct_response"] == {"choice": "b"}
