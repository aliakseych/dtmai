from app.modules.ai.domain.budget import remaining, within_quota
from app.modules.ai.domain.quiz import extract_quiz
from app.modules.ai.domain.suggestions import MAX_SUGGESTIONS, build_suggestions


def test_remaining_counts_down_and_never_negative() -> None:
    assert remaining(20, 0) == 20
    assert remaining(20, 7) == 13
    assert remaining(20, 25) == 0


def test_remaining_unlimited() -> None:
    assert remaining(-1, 999) == -1


def test_quota_exhausted_exactly_at_limit() -> None:
    assert within_quota(3, 2) and not within_quota(3, 3)
    assert remaining(3, 3) == 0 and not within_quota(3, 3)


GOOD = 'Try this:\n```quiz\n{"stem": "2+2?", "options": ["3", "4"], "correct_index": 1, "explanation": "sum"}\n```'


def test_extract_quiz_strips_block() -> None:
    text, quiz = extract_quiz(GOOD)
    assert text == "Try this:" and quiz is not None
    assert (quiz.stem, quiz.options, quiz.correct_index) == ("2+2?", ["3", "4"], 1)


def test_extract_quiz_rejects_bad_index_but_strips() -> None:
    bad = GOOD.replace('"correct_index": 1', '"correct_index": 5')
    text, quiz = extract_quiz(bad)
    assert quiz is None and "```" not in text


def test_extract_quiz_rejects_invalid_json_and_plain_text() -> None:
    assert extract_quiz("```quiz\nnot json\n```")[1] is None
    assert extract_quiz("hello") == ("hello", None)


def test_suggestions_prefer_weak_topics_and_cap() -> None:
    out = build_suggestions("en", ["Fractions", "Fractions", "Tenses", "Logic", "Angles"])
    assert len(out) == MAX_SUGGESTIONS
    assert "Fractions" in out[0] and "Tenses" in out[1]


def test_suggestions_fallback_without_weak_topics_and_unknown_locale() -> None:
    assert len(build_suggestions("ru", [])) == 3
    assert build_suggestions("xx", []) == build_suggestions("en", [])
