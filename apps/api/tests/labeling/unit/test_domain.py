import pytest

from app.modules.labeling.domain.agreement import (
    Event,
    IllegalTransition,
    SolverVote,
    Status,
    evaluate_escalation,
    evaluate_solve,
    next_status,
)
from app.modules.labeling.domain.answers import canonical, same_answer
from app.modules.labeling.domain.audit import AgreementStat, allocate_sample, is_audit_match
from app.modules.labeling.domain.extraction import (
    answer_from_key,
    parse_page,
    placeholder_answer,
)


def v(model, choice, conf=0.9, ok=True):
    return SolverVote(model, {"choice": choice} if choice else None, conf, ok)


def test_unanimous_auto_agreed():
    d = evaluate_solve("single_choice", [v("a", "b"), v("b", "b"), v("c", "b")], official_key=None)
    assert (
        d.status is Status.AUTO_AGREED and d.response == {"choice": "b"} and d.reason == "unanimous"
    )


def test_disagreement_escalates():
    d = evaluate_solve("single_choice", [v("a", "b"), v("b", "c")], official_key=None)
    assert d.status is Status.ESCALATED and d.reason == "disagreement"


def test_low_confidence_and_few_solvers():
    assert (
        evaluate_solve(
            "single_choice", [v("a", "b", 0.3), v("b", "b", 0.4)], official_key=None
        ).reason
        == "low_confidence"
    )
    d = evaluate_solve("single_choice", [v("a", "b"), v("b", None, ok=False)], official_key=None)
    assert d.status is Status.ESCALATED and d.reason == "insufficient_solvers"


def test_official_key_verifies_and_flags_conflict():
    key = {"choice": "a"}
    ok = evaluate_solve("single_choice", [v("a", "a"), v("b", "a")], official_key=key)
    assert ok.status is Status.VERIFIED and not ok.key_conflict
    bad = evaluate_solve("single_choice", [v("a", "c"), v("b", "c")], official_key=key)
    assert bad.status is Status.VERIFIED and bad.key_conflict and bad.response == key


def test_escalation_always_ends_with_human():
    prior = evaluate_solve("single_choice", [v("a", "b"), v("b", "c")], official_key=None)
    assert evaluate_escalation("single_choice", prior, None).status is Status.NEEDS_HUMAN
    assert evaluate_escalation("single_choice", prior, v("j", "c")).status is Status.NEEDS_HUMAN


def test_transitions():
    assert next_status(Status.DRAFT, Event.SOLVE_AGREED) is Status.AUTO_AGREED
    assert next_status(Status.ESCALATED, Event.ESCALATION_DONE) is Status.NEEDS_HUMAN
    assert next_status(Status.AUTO_AGREED, Event.AUDIT_MISMATCH) is Status.NEEDS_HUMAN
    assert next_status(Status.NEEDS_HUMAN, Event.HUMAN_VERIFIED) is Status.VERIFIED
    assert next_status(Status.AUTO_AGREED, Event.FLAGGED) is Status.HIDDEN
    with pytest.raises(IllegalTransition):
        next_status(Status.HIDDEN, Event.KEY_APPLIED)
    with pytest.raises(IllegalTransition):
        next_status(Status.VERIFIED, Event.SOLVE_AGREED)


def test_canonical_answers():
    assert same_answer("multi_choice", {"choices": ["b", "a"]}, {"choices": ["a", "b"]})
    assert same_answer("numeric", {"value": "0.5"}, {"value": 0.5})
    assert same_answer("short_text", {"text": " Tashkent "}, {"text": "tashkent"})
    assert not same_answer("single_choice", {"choice": "a"}, {"choice": "b"})
    assert canonical("single_choice", {}) is None


def test_allocate_sample():
    a = allocate_sample({"x": 90, "y": 10, "z": 0}, 10)
    assert sum(a.values()) == 10 and a["y"] >= 1 and "z" not in a
    assert allocate_sample({"x": 3}, 10) == {"x": 3}
    assert allocate_sample({"x": 5, "y": 3, "z": 1}, 2) == {"x": 1, "y": 1}
    assert allocate_sample({"x": 5}, 0) == {}
    assert allocate_sample(
        {"x": 50, "y": 50},
        10,
    ) == {"x": 5, "y": 5}


def test_audit_match_and_rate():
    assert (
        is_audit_match("a", "a") and not is_audit_match("a", "b") and not is_audit_match(None, None)
    )
    assert AgreementStat(0, 0).rate is None
    assert AgreementStat(4, 3).rate == 0.75


def test_parse_page_and_key():
    page = parse_page(
        {
            "passages": [{"key": "p1", "text": " text "}],
            "questions": [
                {
                    "number": "1",
                    "kind": "single_choice",
                    "stem": "Q",
                    "options": [{"text": "x"}, {"text": "y"}],
                    "passage_key": "p1",
                },
                {"number": 2, "kind": "single_choice", "stem": "bad", "options": [{"text": "x"}]},
                {"number": 3, "kind": "matching", "stem": "no"},
                {"number": 4, "kind": "numeric", "stem": "2+2"},
            ],
            "answer_key": {"1": "B", "x": "A", "4": ""},
        }
    )
    assert [q.number for q in page.questions] == [1, 4]
    assert page.questions[0].options == [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]
    assert page.passages[0].text == "text" and page.questions[0].passage_key == "p1"
    assert page.answer_key == {1: "B"}


def test_answer_from_key_and_placeholder():
    assert answer_from_key("single_choice", "B", 4) == {"choice": "b"}
    assert answer_from_key("single_choice", "E", 4) is None
    assert answer_from_key("single_choice", "A,B", 4) is None
    assert answer_from_key("multi_choice", "A, C", 4) == {"choices": ["a", "c"]}
    assert answer_from_key("numeric", "12,5", 0) == {"value": "12.5"}
    assert answer_from_key("numeric", "abc", 0) is None
    opts = [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]
    assert placeholder_answer("single_choice", opts) == {"choice": "a"}
    assert placeholder_answer("numeric", []) == {"value": 0}


def test_extraction_topic_hint_is_parsed_and_resolved():
    from app.modules.labeling.domain.extraction import parse_classification, pick_topic

    page = parse_page(
        {
            "questions": [
                {"number": 1, "kind": "numeric", "stem": "sin x", "topic": 8},
                {"number": 2, "kind": "numeric", "stem": "no hint"},
                {"number": 3, "kind": "numeric", "stem": "bogus", "topic": "99"},
            ]
        }
    )
    ids = ["t1", "t2", "t3"]
    assert [pick_topic(q.topic, ids, "dflt") for q in page.questions] == ["dflt", "dflt", "dflt"]
    assert pick_topic(2, ids, "dflt") == "t2" and pick_topic(0, ids, "dflt") == "dflt"
    assert parse_classification({"topics": {"1": 3, "2": "1", "9": 1, "x": 2}}, 2) == {0: 3, 1: 1}


def test_extract_system_lists_topics():
    from app.modules.labeling.application.prompts import EXTRACT_SYSTEM, extract_system

    assert extract_system([]) == EXTRACT_SYSTEM
    out = extract_system(["Algebra", "Geometry"])
    assert "1. Algebra" in out and "2. Geometry" in out


# ---- extraction hardening ----------------------------------------------------------------------
def _q(**kw):
    base = {
        "number": 1,
        "kind": "single_choice",
        "stem": "S",
        "options": [{"text": "x"}, {"text": "y"}],
    }
    return {"questions": [{**base, **kw}]}


def test_int_leading_digits():
    from app.modules.labeling.domain.extraction import _int

    assert _int("16(1/2-62).") == 16 and _int(" 3. ") == 3 and _int(7) == 7
    assert _int(True) is None and _int("x1") is None and _int(None) is None


def test_figure_options_kept_only_with_figure():
    pics = [{"id": "a", "text": ""}, {"label": "B", "text": ""}, {"text": ""}]
    q = parse_page(_q(has_figure=True, options=pics)).questions[0]
    assert [o["text"] for o in q.options] == ["A", "B", "C"]
    assert parse_page(_q(has_figure=False, options=pics)).questions == []
    assert (
        parse_page(_q(has_figure=True, options=[{"id": "a", "text": ""}, {"text": "t"}]))
        .questions[0]
        .options[1]["text"]
        == "t"
    )
    assert parse_page(_q(has_figure=True, options=[{"id": "a", "text": ""}])).questions == []


def test_answer_raw_and_options_generated():
    q = parse_page(_q(answer=" B ", options_generated=True, bbox=[1, 2, 3, 4])).questions[0]
    assert q.answer_raw == "B" and q.options_generated is True and q.bbox == [1, 2, 3, 4]
    q = parse_page(_q()).questions[0]
    assert q.answer_raw is None and q.options_generated is False and q.bbox is None


def test_crop_box():
    from app.modules.labeling.domain.extraction import crop_box

    assert crop_box([100, 100, 500, 500], 1000, 2000) == (80, 160, 520, 1040)
    assert crop_box([0, 0, 1000, 1000], 100, 100) == (0, 0, 100, 100)
    assert crop_box([10, 10, 300, 300], 1000, 1000) == (0, 0, 320, 320)
    for bad in (
        None,
        [5, 5, 4, 9],
        [0, 0, 1001, 10],
        [0, 0, 10, 500],
        [1, 2, 3],
        [-1, 0, 500, 500],
    ):
        assert crop_box(bad, 100, 100) is None


def _pe(nums, key=None):
    from app.modules.labeling.domain.extraction import ExtractedQuestion, PageExtraction

    return PageExtraction([], [ExtractedQuestion(n, "single_choice", "s") for n in nums], key or {})


def test_resolve_keys_restarted_numbering():
    from app.modules.labeling.domain.extraction import resolve_keys

    pages = [_pe([1, 2], {1: "A", 2: "B"}), _pe([1, 2], {1: "C", 2: "D"})]
    assert resolve_keys(pages) == {(0, 0): "A", (0, 1): "B", (1, 0): "C", (1, 1): "D"}


def test_resolve_keys_fallbacks():
    from app.modules.labeling.domain.extraction import resolve_keys

    assert resolve_keys([_pe([], {1: "A", 2: "B"}), _pe([1, 2])]) == {(1, 0): "A", (1, 1): "B"}
    # duplicate numbers with a key before them: ambiguous, no fallback
    assert resolve_keys([_pe([], {1: "A"}), _pe([1]), _pe([1])]) == {}


def test_answer_from_key_cyrillic_lookalikes():
    assert answer_from_key("single_choice", "В", 5) == {"choice": "b"}
    assert answer_from_key("single_choice", "Е", 5) == {"choice": "e"}
    assert answer_from_key("multi_choice", "А, С", 5) == {"choices": ["a", "c"]}
    assert answer_from_key("single_choice", "д", 5) == {"choice": "d"}
