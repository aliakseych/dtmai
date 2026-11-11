import json
import re
from typing import Any

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
# Backslash tokens, scanned left to right so escaped pairs stay intact. LaTeX commands that
# collide with JSON escapes (\frac, \beta, \neq, \times, \right…) are re-escaped.
_LATEX_NRT = r"(?:eq|eg|u|abla|ot|ot|i|ightarrow|ight|ho|heta|imes|au|ext|ri|ilde|op)\b"
_ESCAPES = re.compile(
    r"\\\\|\\u[0-9a-fA-F]{4}|\\[\"/]|\\[bf](?![A-Za-z])|\\[nrt](?!" + _LATEX_NRT + r")|\\"
)


def _repair_escapes(text: str) -> str:
    return _ESCAPES.sub(lambda m: m.group(0) if len(m.group(0)) > 1 else "\\\\", text)


def _loads(text: str) -> Any:
    return json.loads(_repair_escapes(text))


def parse_json_object(raw: str) -> dict[str, Any]:
    """Parse an LLM JSON reply tolerating code fences, surrounding prose and raw LaTeX."""
    text = raw.strip()
    m = _FENCE.match(text)
    if m:
        text = m.group(1)
    try:
        value = _loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("no JSON object in LLM reply") from None
        try:
            value = _loads(text[start : end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(str(e)) from None
    if not isinstance(value, dict):
        raise ValueError("LLM reply is not a JSON object")
    return value
