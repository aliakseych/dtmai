from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.modules.learning.application.service import LearningService
from app.modules.learning.domain.mastery import Mastery
from app.modules.learning.domain.session import (
    ABANDONED,
    COMPLETED,
    Mode,
    SessionRec,
    lesson_unlocked,
    xp_base,
)
from app.modules.learning.ports import Graded, Item, LessonRef
from app.shared.errors import Conflict

NOW = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
U, SUBJ = uuid4(), uuid4()


class Placement:
    def __init__(self, unit=2, skipped=False):
        self.start_unit_index, self.ability, self.skipped = unit, 0.3, skipped


class Repo:
    def __init__(self, rec=None, placement=None, completed=()):
        self.rec, self.pl, self.completed = rec, placement, set(completed)
        self.open: list[SessionRec] = []
        self.placements: list = []
        self.saved: list[SessionRec] = []
        self.deltas: list = []

    async def get_session(self, sid, lock=False):
        return self.rec

    async def save_session(self, rec):
        self.saved.append(rec)

    async def open_sessions(self, user_id, mode):
        return self.open

    async def add_session(self, rec):
        pass

    async def placement(self, user_id, subject_id):
        return self.pl

    async def set_placement(self, *a):
        self.placements.append(a)

    async def completed_lesson_ids(self, user_id, ids):
        return self.completed

    async def rating(self, *a):
        return 1000.0

    async def set_rating(self, *a): ...

    async def add_attempt(self, **kw):
        self.deltas.append(kw["elo_delta"])
        return True

    async def mastery(self, *a):
        return Mastery()

    async def set_mastery(self, *a): ...

    async def card(self, *a):
        return None

    async def set_card(self, *a): ...


class Hearts:
    async def state(self, user_id):
        return 5, False

    async def lose(self, user_id):
        return 4


class Sess:
    def __init__(self):
        self.added = []

    def add(self, o):
        self.added.append(o)


class Content:
    def __init__(self, item=None, ref=None):
        self.item, self.ref = item, ref

    async def items(self, ids):
        return [self.item]

    async def grade(self, qid, response):
        return Graded(True, {})

    async def lesson(self, lid, lang):
        return self.ref

    async def unit_count(self, *a):
        return 5


def svc(repo, content=None):
    s = Sess()
    return LearningService(repo, content or Content(), Hearts(), s, lambda: NOW), s


def rec(mode=Mode.RUSH, n=3, answered=0, correct=0, meta=None):
    return SessionRec(
        id=uuid4(),
        user_id=U,
        mode=mode,
        subject_id=SUBJ,
        topic_id=None,
        lesson_id=None,
        language="en",
        question_ids=[uuid4() for _ in range(n)],
        started_at=NOW,
        answered=answered,
        correct=correct,
        meta=meta or {},
    )


def names(s):
    return [e.name for e in s.added]


async def test_expired_rush_with_answers_is_completed_not_abandoned():
    r = rec(answered=2, correct=2, meta={"ends_at": (NOW - timedelta(seconds=5)).isoformat()})
    service, s = svc(Repo(r))
    v = await service.finish(U, r.id)
    assert v.status == COMPLETED and "SessionCompleted" in [e.name for e in s.added]


async def test_stale_open_rush_is_settled_on_next_start():
    stale = rec(answered=1, correct=1)
    repo = Repo()
    repo.open = [stale]
    service, s = svc(repo)
    await service._open(
        U, Mode.RUSH, [object()], subject_id=SUBJ, language="en", question_ids=[uuid4()]
    )
    assert stale.status == COMPLETED and names(s) == ["SessionCompleted"]


async def test_answer_completes_session_when_done():
    r = rec(mode=Mode.DRILL, n=1)
    q = r.question_ids[0]
    item = Item(q, SUBJ, uuid4(), uuid4(), "mcq", "en", 1000.0, "s", [], {}, None, False)
    service, s = svc(Repo(r), Content(item))
    res = await service.answer(U, r.id, q, {}, 1000)
    assert res.session_done and r.status == COMPLETED
    assert "SessionCompleted" in names(s)


async def test_zero_time_is_not_treated_as_missing():
    r = rec(mode=Mode.DRILL, n=2)
    q = r.question_ids[0]
    item = Item(q, SUBJ, uuid4(), uuid4(), "mcq", "en", 1000.0, "s", [], {}, None, False)
    seen = []
    import app.modules.learning.application.service as m

    orig = m.compute_elo_delta
    m.compute_elo_delta = lambda *a: seen.append(a[-1]) or 0
    try:
        service, _ = svc(Repo(r), Content(item))
        await service.answer(U, r.id, q, {}, 0)
    finally:
        m.compute_elo_delta = orig
    assert seen == [0.0]


async def test_placement_not_finished_is_abandoned_even_if_asked():
    pool = [{"id": str(uuid4()), "d": 1000.0} for _ in range(24)]
    r = rec(
        mode=Mode.PLACEMENT,
        meta={"pool": pool, "theta": 1000.0, "asked": [pool[0]["id"]], "deltas": [5.0]},
    )
    repo = Repo(r)
    service, _ = svc(repo)
    v = await service.finish(U, r.id)
    assert v.status == ABANDONED and repo.placements == []


async def test_skip_placement_keeps_earned_one():
    repo = Repo(placement=Placement(2, False))
    service, _ = svc(repo)
    out = await service.skip_placement(U, SUBJ)
    assert out.start_unit_index == 2 and repo.placements == []


async def test_start_lesson_locked_conflicts():
    a, b = uuid4(), uuid4()
    ref = LessonRef(b, SUBJ, [], [], 5, "en", 1, path_units=[[a, b]])
    service, _ = svc(Repo(), Content(ref=ref))
    with pytest.raises(Conflict) as e:
        await service.start_lesson(U, b, "en")
    assert e.value.code == "lesson_locked"


def test_lesson_unlocked_sequence():
    a, b = uuid4(), uuid4()
    assert lesson_unlocked([[a, b]], set(), 0, a)
    assert not lesson_unlocked([[a, b]], set(), 0, b)
    assert lesson_unlocked([[a, b]], {a}, 0, b)


def test_perfect_bonus_needs_five_questions():
    assert xp_base(Mode.DRILL, 3, 3) == 6
    assert xp_base(Mode.DRILL, 5, 5) == 15
