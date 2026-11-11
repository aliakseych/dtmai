"""Canonical forms for kind-specific responses so independent solvers can be compared.

Shapes (frozen with bank): single_choice{"choice"}, multi_choice{"choices"}, numeric{"value"},
short_text{"text"}, matching{"pairs"}, ordering{"order"}.
"""

import re
import unicodedata
from fractions import Fraction
from typing import Any

SOLVABLE_KINDS = frozenset(
    {"single_choice", "multi_choice", "numeric", "short_text", "matching", "ordering"}
)
# Kinds whose equivalence cannot be decided by canonical form alone (judge model may merge).
FREE_FORM_KINDS = frozenset({"numeric", "short_text"})

RESPONSE_SHAPES: dict[str, str] = {
    "single_choice": '{"choice": "<option id>"}',
    "multi_choice": '{"choices": ["<option id>", ...]}',
    "numeric": '{"value": <number>}',
    "short_text": '{"text": "<short answer>"}',
    "matching": '{"pairs": {"<left id>": "<right id>", ...}}',
    "ordering": '{"order": ["<item id>", ...]}',
}


def _num(raw: Any) -> Fraction | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int | float):
        return Fraction(raw).limit_denominator(10**9)
    if isinstance(raw, str):
        t = raw.strip().replace(",", ".").replace(" ", "").replace("−", "-")
        try:
            return Fraction(t).limit_denominator(10**9)
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _text(raw: Any) -> str:
    t = unicodedata.normalize("NFKC", str(raw)).casefold().strip()
    t = re.sub(r"[\s]+", " ", t)
    return t.strip(" .,;:!?\"'«»")


def canonical(kind: str, response: dict[str, Any]) -> str | None:
    """Stable comparison key, or None when the response is malformed for the kind."""
    try:
        match kind:
            case "single_choice":
                return f"c:{_text(response['choice'])}"
            case "multi_choice":
                items = response["choices"]
                if not isinstance(items, list) or not items:
                    return None
                return "m:" + "|".join(sorted({_text(i) for i in items}))
            case "numeric":
                n = _num(response["value"])
                return None if n is None else f"n:{n.numerator}/{n.denominator}"
            case "short_text":
                t = _text(response["text"])
                return f"t:{t}" if t else None
            case "matching":
                pairs = response["pairs"]
                if not isinstance(pairs, dict) or not pairs:
                    return None
                return "p:" + "|".join(sorted(f"{_text(k)}>{_text(v)}" for k, v in pairs.items()))
            case "ordering":
                order = response["order"]
                if not isinstance(order, list) or not order:
                    return None
                return "o:" + "|".join(_text(i) for i in order)
    except (KeyError, TypeError, ValueError):
        return None
    return None


def same_answer(kind: str, a: dict[str, Any], b: dict[str, Any]) -> bool:
    ca, cb = canonical(kind, a), canonical(kind, b)
    return ca is not None and ca == cb
