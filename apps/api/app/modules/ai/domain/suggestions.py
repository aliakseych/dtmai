"""Prompt suggestions for Ask Temur: weak-topic prompts first, then generic study starters."""

from collections.abc import Sequence

MAX_SUGGESTIONS = 4

_TOPIC = {
    "uz-Latn": (
        "«{t}» mavzusini oddiy qilib tushuntir",
        "«{t}» bo‘yicha menga qiziqarli savol ber",
    ),
    "uz-Cyrl": ("«{t}» мавзусини оддий қилиб тушунтир", "«{t}» бўйича менга қизиқарли савол бер"),
    "ru": ("Объясни тему «{t}» простыми словами", "Задай мне вопрос по теме «{t}»"),
    "en": ("Explain “{t}” in simple words", "Quiz me on “{t}”"),
}

_GENERIC = {
    "uz-Latn": (
        "Bugun nimani takrorlashim kerak?",
        "Menga bitta qiyin savol ber",
        "Imtihonga qanday tayyorlanay?",
    ),
    "uz-Cyrl": (
        "Бугун нимани такрорлашим керак?",
        "Менга битта қийин савол бер",
        "Имтиҳонга қандай тайёрлансам?",
    ),
    "ru": (
        "Что мне повторить сегодня?",
        "Задай мне один сложный вопрос",
        "Как лучше готовиться к экзамену?",
    ),
    "en": (
        "What should I review today?",
        "Give me one hard question",
        "How should I prepare for the exam?",
    ),
}


def build_suggestions(locale: str, weak_topics: Sequence[str]) -> list[str]:
    """Up to MAX_SUGGESTIONS prompts in `locale`; unknown locales fall back to English."""
    topic_tpl = _TOPIC.get(locale, _TOPIC["en"])
    generic = _GENERIC.get(locale, _GENERIC["en"])
    out: list[str] = []
    for i, name in enumerate(dict.fromkeys(t for t in weak_topics if t)):
        if len(out) >= MAX_SUGGESTIONS - 1:  # always leave room for a generic starter
            break
        out.append(topic_tpl[i % len(topic_tpl)].format(t=name))
    for g in generic:
        if len(out) >= MAX_SUGGESTIONS:
            break
        out.append(g)
    return out
