"""Pure parsing of vision-extraction output into question drafts."""

import re
from dataclasses import dataclass, field
from typing import Any

EXTRACTABLE_KINDS = frozenset({"single_choice", "multi_choice", "numeric", "short_text"})
_LEADING_INT = re.compile(r"^\s*(\d+)")
_CYR_TO_LATIN = str.maketrans("АВСДЕавсде", "ABCDEabcde")
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
    answer_raw: str | None = None  # answer printed next to the question (Q&A tables), as printed
    options_generated: bool = False  # options synthesised by the model around the printed answer
    bbox: list[int] | None = None  # [x0,y0,x1,y1] 0..1000 normalized to the page


@dataclass(slots=True)
class PageExtraction:
    passages: list[ExtractedPassage]
    questions: list[ExtractedQuestion]
    answer_key: dict[int, str]


def _int(v: Any) -> int | None:
    """Leading integer of a number-like value ('16(1/2-62).' -> 16); bools and non-numbers -> None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        m = _LEADING_INT.match(v)
        if m:
            return int(m.group(1))
    return None


def _option_label(o: dict[str, Any], index: int) -> str:
    for raw in (o.get("label"), o.get("id")):
        s = str(raw or "").strip().strip(".)()")
        if len(s) == 1 and s.isalnum():
            return s.upper()
    return _LETTERS[index].upper()


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
        has_figure = bool(q.get("has_figure"))
        opts: list[dict[str, str]] = []
        for i, o in enumerate(q.get("options") or []):
            if not isinstance(o, dict) or i >= len(_LETTERS):
                continue
            text = str(o.get("text") or "").strip()
            if not text and has_figure and kind in ("single_choice", "multi_choice"):
                text = _option_label(o, i)  # picture option: the drawing itself is in the page image
            if text:
                opts.append({"id": _LETTERS[i], "text": text})
        if kind in ("single_choice", "multi_choice") and len(opts) < 2:
            continue
        raw_answer = q.get("answer")
        answer_raw = str(raw_answer).strip() if isinstance(raw_answer, (str, int, float)) and not isinstance(raw_answer, bool) else ""
        bbox = q.get("bbox")
        questions.append(
            ExtractedQuestion(
                number=_int(q.get("number")), kind=kind, stem=stem, options=opts,
                passage_key=q.get("passage_key") or None, has_figure=has_figure, topic=_int(q.get("topic")),
                answer_raw=answer_raw or None, options_generated=bool(q.get("options_generated")),
                bbox=[int(x) for x in bbox] if bbox is not None and _is_bbox(bbox) else None,
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


def _is_bbox(v: Any) -> bool:
    return isinstance(v, (list, tuple)) and len(v) == 4 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)


def crop_box(bbox: list[int] | None, width: int, height: int, pad: float = 0.02) -> tuple[int, int, int, int] | None:
    """Pixel crop (x0, y0, x1, y1) from a 0..1000 normalized bbox, padded and clamped; None if invalid/degenerate."""
    if not _is_bbox(bbox) or width <= 0 or height <= 0:
        return None
    assert bbox is not None
    x0, y0, x1, y1 = (float(v) for v in bbox)
    if not (0 <= x0 <= 1000 and 0 <= y0 <= 1000 and 0 <= x1 <= 1000 and 0 <= y1 <= 1000):
        return None
    if x1 <= x0 or y1 <= y0 or (x1 - x0) < 20 or (y1 - y0) < 20:
        return None
    px, py = pad * 1000, pad * 1000
    nx0, ny0 = max(0.0, x0 - px), max(0.0, y0 - py)
    nx1, ny1 = min(1000.0, x1 + px), min(1000.0, y1 + py)
    return (
        int(nx0 * width / 1000), int(ny0 * height / 1000),
        min(width, int(round(nx1 * width / 1000))), min(height, int(round(ny1 * height / 1000))),
    )


def resolve_keys(pages: list[PageExtraction]) -> dict[tuple[int, int], str]:
    """Map (page index, question index) -> printed key for ONE file, honouring restarted numbering."""
    out: dict[tuple[int, int], str] = {}
    pending: dict[int, tuple[int, int]] = {}
    counts: dict[int, int] = {}
    last_key: dict[int, str] = {}
    for pi, page in enumerate(pages):
        for qi, q in enumerate(page.questions):
            if q.number is not None:
                pending[q.number] = (pi, qi)
                counts[q.number] = counts.get(q.number, 0) + 1
        for n, raw in page.answer_key.items():
            last_key[n] = raw
            pos = pending.pop(n, None)
            if pos is not None:
                out[pos] = raw
    for pi, page in enumerate(pages):
        for qi, q in enumerate(page.questions):
            if q.number is not None and (pi, qi) not in out and counts[q.number] == 1 and q.number in last_key:
                out[(pi, qi)] = last_key[q.number]
    return out


def answer_from_key(kind: str, raw: str, option_count: int) -> dict[str, Any] | None:
    """Convert a printed key entry ('B', 'A,C', '12.5') into a response; None if unparsable."""
    text = raw.strip()
    if kind in ("single_choice", "multi_choice"):
        latin = text.translate(_CYR_TO_LATIN)
        letters = [t.lower() for t in re.findall(r"[A-Za-z]", latin)]
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
