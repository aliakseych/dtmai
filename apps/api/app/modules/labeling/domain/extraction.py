"""Pure parsing of vision-extraction output into question drafts."""

import re
from dataclasses import dataclass, field
from typing import Any

EXTRACTABLE_KINDS = frozenset({"single_choice", "multi_choice", "numeric", "short_text"})
_LETTERS = "abcdefghijklmnopqrstuvwxyz"


@dataclass(slots=True)
class ExtractedPassage:
    key: str
    title: str | None
    text: str


@dataclass(slots=True)
class ExtractedQuestion:
    number: int | None
    kind: str
    stem: str
    options: list[dict[str, str]] = field(default_factory=list)
    passage_key: str | None = None
    has_figure: bool = False
    answer: dict[str, Any] | None = None
    topic: int | None = None  # 1-based index into the topic list shown to the model


@dataclass(slots=True)
class PageExtraction:
    passages: list[ExtractedPassage]
    questions: list[ExtractedQuestion]
    answer_key: dict[int, str]


def _int(v: Any) -> int | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def parse_page(data: dict[str, Any]) -> PageExtraction:
    passages: list[ExtractedPassage] = []
    for p in data.get("passages") or []:
        if isinstance(p, dict) and str(p.get("text") or "").strip():
            passages.append(
                ExtractedPassage(str(p.get("key") or f"p{len(passages) + 1}"), p.get("title"), str(p["text"]).strip())
            )
    questions: list[ExtractedQuestion] = []
    for q in data.get("questions") or []:
        if not isinstance(q, dict):
            continue
        kind = str(q.get("kind") or "")
        stem = str(q.get("stem") or "").strip()
        if kind not in EXTRACTABLE_KINDS or not stem:
            continue
        opts: list[dict[str, str]] = []
        for i, o in enumerate(q.get("options") or []):
            if isinstance(o, dict) and str(o.get("text") or "").strip() and i < len(_LETTERS):
                opts.append({"id": _LETTERS[i], "text": str(o["text"]).strip()})
        if kind in ("single_choice", "multi_choice") and len(opts) < 2:
            continue
        questions.append(
            ExtractedQuestion(
                number=_int(q.get("number")), kind=kind, stem=stem, options=opts,
                passage_key=q.get("passage_key") or None, has_figure=bool(q.get("has_figure")), topic=_int(q.get("topic")),
            )
        )
    key: dict[int, str] = {}
    raw_key = data.get("answer_key")
    if isinstance(raw_key, dict):
        for k, v in raw_key.items():
            n = _int(k)
            if n is not None and v is not None and str(v).strip():
                key[n] = str(v).strip()
    return PageExtraction(passages, questions, key)


def answer_from_key(kind: str, raw: str, option_count: int) -> dict[str, Any] | None:
    """Convert a printed key entry ('B', 'A,C', '12.5') into a response; None if unparsable."""
    text = raw.strip()
    if kind in ("single_choice", "multi_choice"):
        letters = [t.lower() for t in re.findall(r"[A-Za-z]", text)]
        letters = [t for t in dict.fromkeys(letters) if t in _LETTERS[:option_count]]
        if kind == "single_choice":
            return {"choice": letters[0]} if len(letters) == 1 else None
        return {"choices": letters} if letters else None
    if kind == "numeric":
        t = text.replace(",", ".").replace(" ", "")
        try:
            float(t)
        except ValueError:
            return None
        return {"value": t}
    return {"text": text} if text else None


def placeholder_answer(kind: str, options: list[dict[str, str]]) -> dict[str, Any]:
    """Valid-but-unreviewed answer for drafts without an official key (never verified as-is)."""
    match kind:
        case "single_choice":
            return {"choice": options[0]["id"]}
        case "multi_choice":
            return {"choices": [options[0]["id"]]}
        case "numeric":
            return {"value": 0}
        case _:
            return {"text": "-"}


def pick_topic(hint: int | None, topic_ids: list[Any], default: Any) -> Any:
    """Resolve a 1-based model topic hint against the ordered topic list; fall back to `default`."""
    if hint is not None and 1 <= hint <= len(topic_ids):
        return topic_ids[hint - 1]
    return default


def parse_classification(data: dict[str, Any], count: int) -> dict[int, int]:
    """{question position (0-based) -> 1-based topic index} from a classify reply; invalid entries dropped."""
    out: dict[int, int] = {}
    raw = data.get("topics")
    if isinstance(raw, dict):
        for k, v in raw.items():
            n, t = _int(k), _int(v)
            if n is not None and t is not None and 1 <= n <= count:
                out[n - 1] = t
    return out
