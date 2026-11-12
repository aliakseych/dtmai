"""Match lyceum names from external documents (PDF orders, call-centre sheets) to DB lyceums.

Names differ in script (Cyrillic vs Latin), apostrophes, x/h spelling, typos and noise words
("akademik litseyi", "davlat"), so both sides are normalised to token lists and compared with a
fuzzy Dice score. Matching is one-to-one and refuses ambiguous ties.
"""

import re
from collections.abc import Hashable, Mapping
from dataclasses import dataclass, field
from difflib import SequenceMatcher

_CYR = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "j",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sh",
    "ъ": "",
    "ы": "i",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
    "ў": "o",
    "қ": "q",
    "ғ": "g",
    "ҳ": "h",
}
_APOSTROPHES = "ʻʼ'`’‘´ʹ"
_NOISE = frozenset(
    {
        "akademik",
        "academic",
        "litsey",
        "litseyi",
        "litseyining",
        "licey",
        "davlat",
        "nomidagi",
        "nomli",
        "nomi",
        "huzuridagi",
        "qoshidagi",
        "ixtisoslashgan",
        "ixtisoslashtirilgan",
        "respublika",
        "ga",
        "va",
        "and",
        "of",
        "the",
        "mtu",
    }
)
# Tokens are normalised (x -> h) before filtering, so the noise words must be too.
_NOISE = frozenset(w.replace("x", "h") for w in _NOISE)
_STEM = 6
_TOKEN_MATCH = 0.8
THRESHOLD = 0.7
_TIE_GAP = 0.02


def transliterate(text: str) -> str:
    return "".join(_CYR.get(ch, ch) for ch in text.lower())


def name_tokens(name: str) -> list[str]:
    """Normalised distinctive tokens; numbers like `2-son` become `2son`."""
    s = transliterate(name)
    for ch in _APOSTROPHES:
        s = s.replace(ch, "")
    s = s.replace("x", "h")
    s = re.sub(r"(\d+)\s*-?\s*son\b", r"\1son", s)
    tokens = re.findall(r"[a-z]+|\d+son|\d+", s)
    return [t for t in tokens if t not in _NOISE and len(t) > 1 or t.isdigit()]


def _stem(token: str) -> str:
    return token if token[0].isdigit() else token[:_STEM]


def _tokens_equal(a: str, b: str) -> bool:
    if a[0].isdigit() or b[0].isdigit():
        return a == b
    return SequenceMatcher(None, _stem(a), _stem(b)).ratio() >= _TOKEN_MATCH


def similarity(a: str, b: str) -> float:
    """Dice score of fuzzy token overlap, 0 when the numeric tokens (`2-son`) differ."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    if {t for t in ta if t[0].isdigit()} != {t for t in tb if t[0].isdigit()}:
        return 0.0
    free = list(tb)
    hits = 0
    for token in ta:
        for i, other in enumerate(free):
            if _tokens_equal(token, other):
                hits += 1
                del free[i]
                break
    return 2 * hits / (len(ta) + len(tb))


@dataclass(frozen=True, slots=True)
class MatchResult:
    matched: dict[Hashable, Hashable] = field(default_factory=dict)
    unmatched: list[Hashable] = field(default_factory=list)
    ambiguous: list[Hashable] = field(default_factory=list)


def match_names(sources: Mapping[Hashable, str], candidates: Mapping[Hashable, str]) -> MatchResult:
    """One-to-one assignment source key -> candidate key, best scores first.

    A source whose best two candidates are nearly tied is `ambiguous` and left unmatched.
    """
    scored: dict[Hashable, list[tuple[float, Hashable]]] = {}
    for sk, sname in sources.items():
        scores = sorted(
            ((similarity(sname, cname), ck) for ck, cname in candidates.items()),
            key=lambda x: -x[0],
        )
        scored[sk] = [x for x in scores if x[0] >= THRESHOLD]
    ambiguous = [sk for sk, s in scored.items() if len(s) > 1 and s[0][0] - s[1][0] < _TIE_GAP]
    pairs = sorted(
        ((score, sk, ck) for sk, s in scored.items() if sk not in ambiguous for score, ck in s),
        key=lambda x: -x[0],
    )
    matched: dict[Hashable, Hashable] = {}
    taken: set[Hashable] = set()
    for _score, sk, ck in pairs:
        if ck in taken or sk in matched:
            continue
        matched[sk] = ck
        taken.add(ck)
    unmatched = [sk for sk in sources if sk not in matched and sk not in ambiguous]
    return MatchResult(matched=matched, unmatched=unmatched, ambiguous=ambiguous)
