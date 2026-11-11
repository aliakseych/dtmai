"""Inline quiz: Temur may end a reply with one fenced ```quiz JSON block the client renders."""

import json
import re
from dataclasses import dataclass

_BLOCK = re.compile(r"```quiz\s*(.*?)```", re.DOTALL | re.IGNORECASE)
MIN_OPTIONS = 2
MAX_OPTIONS = 6


@dataclass(frozen=True, slots=True)
class InlineQuiz:
    stem: str
    options: list[str]
    correct_index: int
    explanation: str


def _parse(raw: str) -> InlineQuiz | None:
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    stem, options = data.get("stem"), data.get("options")
    idx, expl = data.get("correct_index"), data.get("explanation", "")
    if not isinstance(stem, str) or not stem.strip() or not isinstance(options, list):
        return None
    if not MIN_OPTIONS <= len(options) <= MAX_OPTIONS or not all(
        isinstance(o, str) and o.strip() for o in options
    ):
        return None
    if isinstance(idx, bool) or not isinstance(idx, int) or not 0 <= idx < len(options):
        return None
    return InlineQuiz(
        stem.strip(),
        [o.strip() for o in options],
        idx,
        expl.strip() if isinstance(expl, str) else "",
    )


def extract_quiz(text: str) -> tuple[str, InlineQuiz | None]:
    """Strip every quiz block from the reply; return the first valid one (malformed blocks are dropped)."""
    quiz: InlineQuiz | None = None
    for m in _BLOCK.finditer(text):
        quiz = quiz or _parse(m.group(1).strip())
    return _BLOCK.sub("", text).strip(), quiz
