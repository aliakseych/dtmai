import pytest

from app.modules.bank.domain.kinds import (
    Grade,
    InvalidQuestion,
    aggregate_group,
    empirical_difficulty,
    grade_response,
    normalize_text,
    parse_number,
    validate_question,
)
from app.modules.bank.domain.models import transition_allowed

OPTS = {"options": [{"id": "a", "text": "1"}, {"id": "b", "text": "2"}, {"id": "c", "text": "3"}]}


def g(kind, payload, answer, response):
    return grade_response(kind, payload, answer, response)


def test_single_choice():
    assert g("single_choice", OPTS, {"choice": "b"}, {"choice": "b"}) == Grade(True, 1.0)
    assert not g("single_choice", OPTS, {"choice": "b"}, {"choice": "a"}).correct
    assert not g("single_choice", OPTS, {"choice": "b"}, {}).correct


def test_multi_choice_partial():
    ans = {"choices": ["a", "b"]}
    assert g("multi_choice", OPTS, ans, {"choices": ["b", "a"]}).correct
    part = g("multi_choice", OPTS, ans, {"choices": ["a"]})
    assert not part.correct and part.score == 0.5
    assert g("multi_choice", OPTS, ans, {"choices": ["a", "c"]}).score == 0.0
    assert not g("multi_choice", OPTS, ans, {"choices": "a"}).correct


def test_numeric_formats_and_tolerance():
    ans = {"value": 1.5}
    for v in (1.5, "1,5", "3/2", " 1.5 "):
        assert g("numeric", {}, ans, {"value": v}).correct, v
    assert not g("numeric", {}, ans, {"value": "abc"}).correct
    assert g("numeric", {}, {"value": 10, "tolerance": 0.5}, {"value": 10.4}).correct
    assert not g("numeric", {}, {"value": 10, "tolerance": 0.5}, {"value": 11}).correct
    assert not g("numeric", {}, ans, {"value": True}).correct
    assert parse_number("1 000") == 1000


def test_short_text_normalisation():
    ans = {"accepted": ["Tashkent", "Toshkent"]}
    assert g("short_text", {}, ans, {"text": "  toshkent "}).correct
    assert not g("short_text", {}, ans, {"text": "samarkand"}).correct
    assert not g("short_text", {}, {"accepted": ["Abc"], "case_sensitive": True}, {"text": "abc"}).correct
    assert normalize_text("A  b") == "a b"


def test_matching_partial():
    ans = {"pairs": {"l1": "r1", "l2": "r2"}}
    assert g("matching", {}, ans, {"pairs": {"l1": "r1", "l2": "r2"}}).correct
    p = g("matching", {}, ans, {"pairs": {"l1": "r1", "l2": "r1"}})
    assert not p.correct and p.score == 0.5
    assert not g("matching", {}, ans, {"pairs": []}).correct


def test_ordering():
    ans = {"order": ["a", "b", "c"]}
    assert g("ordering", {}, ans, {"order": ["a", "b", "c"]}).correct
    p = g("ordering", {}, ans, {"order": ["a", "c", "b"]})
    assert not p.correct and abs(p.score - 1 / 3) < 1e-9
    assert not g("ordering", {}, ans, {"order": "abc"}).correct


def test_passage_group_aggregate():
    assert aggregate_group([Grade(True, 1), Grade(True, 1)]).correct
    r = aggregate_group([Grade(True, 1), Grade(False, 0)])
    assert not r.correct and r.score == 0.5
    assert not aggregate_group([]).correct


def test_group_not_directly_gradable_and_malformed():
    with pytest.raises(InvalidQuestion):
        g("passage_group", {}, {}, {"answers": {}})
    assert not g("single_choice", OPTS, {"choice": "a"}, "a").correct


def test_validate_question():
    validate_question("single_choice", OPTS, {"choice": "a"})
    with pytest.raises(InvalidQuestion):
        validate_question("single_choice", OPTS, {"choice": "zzz"})
    with pytest.raises(InvalidQuestion):
        validate_question("single_choice", {"options": [{"id": "a", "text": "x"}]}, {"choice": "a"})
    validate_question("numeric", {}, {"value": 3})
    with pytest.raises(InvalidQuestion):
        validate_question("numeric", {}, {"value": "x"})
    with pytest.raises(InvalidQuestion):
        validate_question("short_text", {}, {"accepted": []})
    with pytest.raises(InvalidQuestion):
        validate_question("nope", {}, {})


def test_empirical_difficulty():
    assert empirical_difficulty(5, 5) is None
    assert empirical_difficulty(100, 50) == 1000.0
    assert empirical_difficulty(100, 90) < 1000 < empirical_difficulty(100, 10)


def test_transitions():
    assert transition_allowed("draft", "verified")
    assert transition_allowed("verified", "hidden")
    assert not transition_allowed("retired", "verified")
    assert transition_allowed("retired", "draft")
    assert not transition_allowed("draft", "bogus")
