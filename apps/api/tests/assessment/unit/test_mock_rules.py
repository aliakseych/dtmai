from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.assessment.domain.attempt import GRACE, MockAttempt, deadline_for
from app.modules.assessment.domain.comparison import compare
from app.modules.assessment.domain.prediction import predict
from app.modules.assessment.domain.scoring import Scored, max_score, score

T0 = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)


def attempt() -> MockAttempt:
    qs = [{"id": str(uuid4()), "section": 0} for _ in range(2)]
    return MockAttempt(
        id=uuid4(), user_id=uuid4(), kind="official", blueprint_id=uuid4(), blueprint_version=1,
        language="uz", started_at=T0, deadline=deadline_for(T0, 60), questions=qs, sections=[],
    )


def test_deadline_and_expiry() -> None:
    a = attempt()
    assert a.deadline == T0 + timedelta(minutes=60)
    assert not a.expired(a.deadline - timedelta(seconds=1))
    assert a.expired(a.deadline)
    assert a.time_left(T0) == 3600 and a.time_left(a.deadline + timedelta(hours=1)) == 0


def test_save_within_grace_and_after() -> None:
    a = attempt()
    q = a.questions[0]["id"]
    assert a.apply_save(a.deadline + GRACE, {q: {"v": 1}}, [q])
    assert a.answers[q] == {"v": 1} and a.flags == [q]
    assert not a.apply_save(a.deadline + GRACE + timedelta(seconds=1), {q: {"v": 2}}, None)
    assert a.answers[q] == {"v": 1}


def test_save_ignores_unknown_and_clears_empty() -> None:
    a = attempt()
    q = a.questions[0]["id"]
    a.apply_save(T0, {q: {"v": 1}, "other": {"v": 9}}, ["other", q, q])
    assert list(a.answers) == [q] and a.flags == [q]
    a.apply_save(T0, {q: {}}, None)
    assert a.answers == {}


def test_close_auto_clamps_time_and_blocks_input() -> None:
    a = attempt()
    late = a.deadline + timedelta(hours=3)
    a.close(late, reason="auto")
    assert a.submitted_at == a.deadline + GRACE and a.submit_reason == "auto"
    assert not a.accepts_input(T0) and not a.expired(late)


def test_scoring_formula() -> None:
    items = [
        Scored(0, "A", "t1", "ty", True), Scored(0, "A", "t1", "ty", False),
        Scored(0, "A", "t1", "ty", False), Scored(0, "A", "t2", "ty", True),
        Scored(1, "B", None, "ty", True),
    ]
    r = score(items, [1.0, 2.0])
    assert r.subject_scores == {"A": 10.0, "B": 40.0}
    assert r.total == 50.0 and r.max_total == max_score([1.0, 2.0]) == 60.0
    assert r.correct == 3 and r.answered_total == 5


def test_prediction_confidence() -> None:
    assert predict([]) is None
    p = predict([(30, 60)])
    assert p and p.value == 30 and not p.confident
    p = predict([(30, 60), (36, 60), (24, 60)])
    assert p and p.confident and p.low <= p.value <= p.high <= 60


def test_comparison() -> None:
    c = compare(50, passing_score=45, competition_ratio=3.2, year=2025)
    assert c.gap == 5 and c.on_track is True
    assert compare(40, passing_score=45, competition_ratio=None).on_track is False
    assert compare(40, passing_score=None, competition_ratio=None).on_track is None
