from dataclasses import dataclass

from app.modules.notify.domain.policy import LOCALES, Kind


@dataclass(frozen=True, slots=True)
class Message:
    title: str
    body: str


_CATALOG: dict[Kind, dict[str, Message]] = {
    Kind.STREAK_REMINDER: {
        "uz-Latn": Message(
            "Seriyangizni saqlang! 🔥",
            "Bugun {streak} kunlik seriya xavf ostida. 5 daqiqa mashq qiling.",
        ),
        "uz-Cyrl": Message(
            "Серияингизни сақланг! 🔥",
            "Бугун {streak} кунлик серия хавф остида. 5 дақиқа машқ қилинг.",
        ),
        "ru": Message(
            "Сохраните серию! 🔥", "Серия в {streak} дн. под угрозой. Позанимайтесь 5 минут."
        ),
        "en": Message(
            "Save your streak! 🔥", "Your {streak}-day streak is at risk. Practise for 5 minutes."
        ),
    },
    Kind.LEAGUE_ENDING: {
        "uz-Latn": Message(
            "Liga tugashiga oz qoldi ⏳",
            "Haftalik liga tez orada yakunlanadi. O‘rningizni mustahkamlang!",
        ),
        "uz-Cyrl": Message(
            "Лига тугашига оз қолди ⏳",
            "Ҳафталик лига тез орада якунланади. Ўрнингизни мустаҳкамланг!",
        ),
        "ru": Message(
            "Лига скоро закончится ⏳", "Недельная лига скоро завершится. Закрепите своё место!"
        ),
        "en": Message("League ends soon ⏳", "The weekly league ends soon. Secure your spot!"),
    },
    Kind.DAILY_QUESTION: {
        "uz-Latn": Message("Kunlik savol 🎯", "Bugungi savolga javob bering."),
        "uz-Cyrl": Message("Кунлик савол 🎯", "Бугунги саволга жавоб беринг."),
        "ru": Message("Вопрос дня 🎯", "Ответьте на вопрос дня."),
        "en": Message("Daily question 🎯", "Answer today's question."),
    },
}


def render(kind: Kind, locale: str, **params: object) -> Message:
    by_locale = _CATALOG[kind]
    msg = by_locale.get(locale) or by_locale["en"]
    return Message(msg.title.format(**params), msg.body.format(**params))


def catalog_locales(kind: Kind) -> set[str]:
    return set(_CATALOG[kind])


__all__ = ["LOCALES", "Message", "catalog_locales", "render"]
