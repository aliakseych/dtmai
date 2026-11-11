"""Pure payload validation + grading for the closed set of question kinds.

Shapes (answer shape == client response shape == GradeResult.correct_response):
- single_choice: payload {"options":[{"id","text"?,"media"?}]}      answer/response {"choice": id}
- multi_choice:  payload {"options":[...]}                         answer/response {"choices": [ids]}
- numeric:       payload {"unit"?}                                 answer {"value": n, "tolerance"?: t}; response {"value": n|str}
- short_text:    payload {}                                        answer {"accepted":[str], "case_sensitive"?: bool}; response {"text": s}
- matching:      payload {"left":[{id,text}], "right":[{id,text}]} answer/response {"pairs": {left_id: right_id}}
- ordering:      payload {"items":[{id,text}]}                     answer/response {"order": [ids]}
- passage_group: payload {"child_ids":[uuid str]}                  answer {}; response {"answers": {child_id: response}}
"""

import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from app.shared.question_kinds import PASSAGE_GROUP, QUESTION_KINDS


class InvalidQuestion(ValueError):
    """Payload/answer does not satisfy the kind's schema."""


@dataclass(frozen=True, slots=True)
class Grade:
    correct: bool
    score: float  # 0..1


WRONG = Grade(False, 0.0)


def _need(cond: bool, msg: str) -> None:
    if not cond:
        raise InvalidQuestion(msg)


def _items(payload: Mapping[str, Any], key: str, minimum: int = 2) -> list[str]:
    raw = payload.get(key)
    _need(isinstance(raw, list) and len(raw) >= minimum, f"payload.{key} needs >= {minimum} entries")
    ids: list[str] = []
    for it in raw:
        _need(isinstance(it, dict), f"payload.{key} entries must be objects")
        iid = it.get("id")
        _need(isinstance(iid, str) and iid != "", f"payload.{key} entry needs a string id")
        text, media = it.get("text"), it.get("media")
        _need(bool(text) or bool(media), f"payload.{key}[{iid}] needs text or media")
        ids.append(iid)
    _need(len(set(ids)) == len(ids), f"payload.{key} ids must be unique")
    return ids


def parse_number(value: Any) -> Fraction | None:
    """Accepts ints/floats and strings like '1,5', '1 000', '-3/4'. None when unparsable."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, int):
            return Fraction(value)
        if isinstance(value, float):
            return Fraction(str(value))
        if isinstance(value, str):
            s = value.strip().replace(",", ".").replace("\u00a0", "").replace(" ", "")
            s = s.replace("\u2212", "-")
            return Fraction(s) if s else None
    except (ValueError, ZeroDivisionError):
        return None
    return None


def normalize_text(s: str, *, case_sensitive: bool = False) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2019", "'").replace("\u02bc", "'").replace("\u2018", "'").replace("`", "'")
    s = " ".join(s.split())
    return s if case_sensitive else s.casefold()


def validate_question(kind: str, payload: Mapping[str, Any], answer: Mapping[str, Any]) -> None:
    _need(kind in QUESTION_KINDS, f"unknown kind {kind!r}")
    _need(isinstance(payload, Mapping) and isinstance(answer, Mapping), "payload/answer must be objects")
    match kind:
        case "single_choice":
            ids = _items(payload, "options")
            _need(answer.get("choice") in ids, "answer.choice must be an option id")
        case "multi_choice":
            ids = _items(payload, "options")
            ch = answer.get("choices")
            _need(isinstance(ch, list) and len(ch) > 0, "answer.choices must be a non-empty list")
            _need(len(set(ch)) == len(ch) and set(ch) <= set(ids), "answer.choices must be unique option ids")
        case "numeric":
            _need(parse_number(answer.get("value")) is not None, "answer.value must be a number")
            tol = answer.get("tolerance", 0)
            t = parse_number(tol)
            _need(t is not None and t >= 0, "answer.tolerance must be >= 0")
        case "short_text":
            acc = answer.get("accepted")
            _need(
                isinstance(acc, list) and len(acc) > 0 and all(isinstance(a, str) and a.strip() for a in acc),
                "answer.accepted must be a non-empty list of strings",
            )
        case "matching":
            left = _items(payload, "left")
            right = _items(payload, "right")
            pairs = answer.get("pairs")
            _need(isinstance(pairs, dict) and set(pairs) == set(left), "answer.pairs must cover every left id")
            _need(all(v in right for v in pairs.values()), "answer.pairs values must be right ids")
        case "ordering":
            ids = _items(payload, "items")
            order = answer.get("order")
            _need(isinstance(order, list) and sorted(order) == sorted(ids), "answer.order must be a permutation of items")
        case "passage_group":
            ch = payload.get("child_ids")
            _need(
                isinstance(ch, list) and len(ch) > 0 and all(isinstance(c, str) and c for c in ch),
                "payload.child_ids must be a non-empty list",
            )


def grade_response(
    kind: str, payload: Mapping[str, Any], answer: Mapping[str, Any], response: Any
) -> Grade:
    """Grade one non-group question. Malformed responses are simply wrong (never raise)."""
    if not isinstance(response, Mapping):
        return WRONG
    try:
        match kind:
            case "single_choice":
                ok = response.get("choice") == answer["choice"]
                return Grade(ok, 1.0 if ok else 0.0)
            case "multi_choice":
                ans = set(answer["choices"])
                raw = response.get("choices")
                if not isinstance(raw, list) or not all(isinstance(c, str) for c in raw):
                    return WRONG
                sel = set(raw)
                hits, wrong = len(sel & ans), len(sel - ans)
                return Grade(sel == ans, max(0.0, (hits - wrong) / len(ans)))
            case "numeric":
                got = parse_number(response.get("value"))
                want = parse_number(answer["value"])
                tol = parse_number(answer.get("tolerance", 0)) or Fraction(0)
                ok = got is not None and want is not None and abs(got - want) <= tol
                return Grade(ok, 1.0 if ok else 0.0)
            case "short_text":
                text = response.get("text")
                if not isinstance(text, str):
                    return WRONG
                cs = bool(answer.get("case_sensitive", False))
                got_s = normalize_text(text, case_sensitive=cs)
                ok = any(normalize_text(a, case_sensitive=cs) == got_s for a in answer["accepted"])
                return Grade(ok, 1.0 if ok else 0.0)
            case "matching":
                want_pairs: dict[str, str] = answer["pairs"]
                got_pairs = response.get("pairs")
                if not isinstance(got_pairs, dict):
                    return WRONG
                hits = sum(1 for k, v in want_pairs.items() if got_pairs.get(k) == v)
                return Grade(hits == len(want_pairs), hits / len(want_pairs))
            case "ordering":
                want_order: list[str] = answer["order"]
                got_order = response.get("order")
                if not isinstance(got_order, list):
                    return WRONG
                hits = sum(1 for i, v in enumerate(want_order) if i < len(got_order) and got_order[i] == v)
                return Grade(got_order == want_order, hits / len(want_order))
    except (KeyError, TypeError, ZeroDivisionError):
        return WRONG
    raise InvalidQuestion(f"kind {kind!r} is not directly gradable")


def aggregate_group(grades: Sequence[Grade]) -> Grade:
    """passage_group: correct iff every child is correct; score = mean child score."""
    if not grades:
        return WRONG
    return Grade(all(g.correct for g in grades), sum(g.score for g in grades) / len(grades))


def grade_group(
    children: Sequence[tuple[str, str, Mapping[str, Any], Mapping[str, Any]]], response: Any
) -> tuple[Grade, dict[str, Any]]:
    """Grade a passage_group. `children` = (child_id, kind, payload, answer) in passage order;
    `response` = {"answers": {child_id: child_response}}. Unanswered/malformed children are wrong.
    Returns (aggregate grade, {"answers": {child_id: child answer}})."""
    answers = response.get("answers") if isinstance(response, Mapping) else None
    if not isinstance(answers, Mapping):
        answers = {}
    grades = [
        grade_response(kind, payload, answer, answers[cid]) if cid in answers else WRONG
        for cid, kind, payload, answer in children
    ]
    return aggregate_group(grades), {"answers": {cid: dict(answer) for cid, _, _, answer in children}}


def empirical_difficulty(attempts: int, correct: int, *, min_attempts: int = 20) -> float | None:
    """Elo-scale difficulty from the observed correct rate; None until enough data."""
    import math

    if attempts < min_attempts:
        return None
    p = min(0.95, max(0.05, correct / attempts))
    return round(1000.0 + 400.0 * math.log10((1 - p) / p), 1)


def is_group(kind: str) -> bool:
    return kind == PASSAGE_GROUP


__all__ = [
    "Grade",
    "InvalidQuestion",
    "aggregate_group",
    "empirical_difficulty",
    "grade_group",
    "grade_response",
    "is_group",
    "normalize_text",
    "parse_number",
    "validate_question",
]
