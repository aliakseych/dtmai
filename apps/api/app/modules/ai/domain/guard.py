"""Prompt-injection heuristics for the learner-facing tutor (defence in depth, not a guarantee)."""

import re
import unicodedata

_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts?|rules)",
    r"disregard (all |any |the )?(previous|prior|above|earlier)",
    r"forget (all |your |the )?(previous|prior|instructions|rules)",
    r"(reveal|show|print|repeat|leak) (me )?(your|the) (system|hidden|initial) (prompt|instructions|message)",
    r"you are (now )?(dan|developer mode|jailbroken)",
    r"\bsystem prompt\b",
    r"</?\s*(system|assistant|instructions?)\s*>",
    r"\[/?(system|inst)\]",
    r"игнорируй (все |любые )?(предыдущие|прошлые|прежние) (инструкции|указания|правила)",
    r"забудь (все )?(инструкции|правила)",
    r"(покажи|выведи|раскрой) (свой |системный )?(системный )?(промпт|prompt)",
    r"oldingi (barcha )?(ko['‘’`]?rsatma|buyruq)lar(ni)? (e['‘’`]?tiborsiz|unut)",
    r"tizim (prompt|ko['‘’`]?rsatma)",
]
_RE = re.compile("|".join(f"(?:{p})" for p in _PATTERNS), re.IGNORECASE)


def looks_like_injection(text: str) -> bool:
    norm = unicodedata.normalize("NFKC", text)
    return _RE.search(norm) is not None


def sanitize_user_text(text: str, max_len: int) -> str:
    """Strip control chars and cap length; role markers are neutralised so they cannot close our delimiters."""
    cleaned = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    cleaned = cleaned.replace("<<<", "«").replace(">>>", "»")
    return cleaned[:max_len].strip()
