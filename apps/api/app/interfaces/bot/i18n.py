LOCALES = ("uz-Latn", "uz-Cyrl", "ru", "en")
DEFAULT_LOCALE = "uz-Latn"

LOCALE_LABELS = {"uz-Latn": "O‘zbekcha", "uz-Cyrl": "Ўзбекча", "ru": "Русский", "en": "English"}

# Question content language per UI locale (content language is separate from UI locale).
CONTENT_LANGUAGE = {"uz-Latn": "uz", "uz-Cyrl": "uz", "ru": "ru", "en": "en"}

STRINGS: dict[str, dict[str, str]] = {
    "uz-Latn": {
        "welcome": "Salom, {name}! Men Temur — DTM AI yordamchisiman. Litseyga kirish imtihoniga birga tayyorlanamiz.",
        "open_app": "📱 Ilovani ochish",
        "daily": "🎯 Kunlik savol",
        "reminders_on": "🔔 Eslatmalar: yoqilgan",
        "reminders_off": "🔕 Eslatmalar: o‘chiq",
        "language": "🌐 Til",
        "help": "❓ Yordam",
        "help_text": "Ilovani oching, kunlik savolga javob bering va eslatmalarni yoqing. Muammo bo‘lsa: support@dtm-ai.uz",
        "pick_language": "Tilni tanlang:",
        "language_saved": "Til saqlandi ✅",
        "link_ok": "Hisobingiz ulandi ✅ Endi eslatmalar shu yerga keladi.",
        "link_bad": "Ulash kodi yaroqsiz yoki muddati o‘tgan. Ilovadan yangi kod oling.",
        "need_link": "Eslatmalarni yoqish uchun avval hisobingizni ilovada ulang.",
        "no_question": "Hozircha savol yo‘q. Keyinroq urinib ko‘ring.",
        "correct": "✅ To‘g‘ri!",
        "wrong": "❌ Noto‘g‘ri.",
        "expired": "Bu savol endi mavjud emas.",
        "reminders_enabled": "Eslatmalar yoqildi 🔔",
        "reminders_disabled": "Eslatmalar o‘chirildi 🔕",
    },
    "uz-Cyrl": {
        "welcome": "Салом, {name}! Мен Темур — DTM AI ёрдамчисиман. Лицейга кириш имтиҳонига бирга тайёрланамиз.",
        "open_app": "📱 Иловани очиш",
        "daily": "🎯 Кунлик савол",
        "reminders_on": "🔔 Эслатмалар: ёқилган",
        "reminders_off": "🔕 Эслатмалар: ўчиқ",
        "language": "🌐 Тил",
        "help": "❓ Ёрдам",
        "help_text": "Иловани очинг, кунлик саволга жавоб беринг ва эслатмаларни ёқинг. Муаммо бўлса: support@dtm-ai.uz",
        "pick_language": "Тилни танланг:",
        "language_saved": "Тил сақланди ✅",
        "link_ok": "Ҳисобингиз уланди ✅ Энди эслатмалар шу ерга келади.",
        "link_bad": "Улаш коди яроқсиз ёки муддати ўтган. Иловадан янги код олинг.",
        "need_link": "Эслатмаларни ёқиш учун аввал ҳисобингизни иловада уланг.",
        "no_question": "Ҳозирча савол йўқ. Кейинроқ уриниб кўринг.",
        "correct": "✅ Тўғри!",
        "wrong": "❌ Нотўғри.",
        "expired": "Бу савол энди мавжуд эмас.",
        "reminders_enabled": "Эслатмалар ёқилди 🔔",
        "reminders_disabled": "Эслатмалар ўчирилди 🔕",
    },
    "ru": {
        "welcome": "Привет, {name}! Я Темур, помощник DTM AI. Вместе подготовимся к вступительным экзаменам в лицей.",
        "open_app": "📱 Открыть приложение",
        "daily": "🎯 Вопрос дня",
        "reminders_on": "🔔 Напоминания: вкл",
        "reminders_off": "🔕 Напоминания: выкл",
        "language": "🌐 Язык",
        "help": "❓ Помощь",
        "help_text": "Откройте приложение, отвечайте на вопрос дня и включите напоминания. Проблемы: support@dtm-ai.uz",
        "pick_language": "Выберите язык:",
        "language_saved": "Язык сохранён ✅",
        "link_ok": "Аккаунт привязан ✅ Теперь напоминания приходят сюда.",
        "link_bad": "Код привязки недействителен или истёк. Получите новый в приложении.",
        "need_link": "Чтобы включить напоминания, сначала привяжите аккаунт в приложении.",
        "no_question": "Пока нет вопросов. Попробуйте позже.",
        "correct": "✅ Верно!",
        "wrong": "❌ Неверно.",
        "expired": "Этот вопрос больше недоступен.",
        "reminders_enabled": "Напоминания включены 🔔",
        "reminders_disabled": "Напоминания выключены 🔕",
    },
    "en": {
        "welcome": "Hi, {name}! I'm Temur, your DTM AI buddy. Let's prepare for the lyceum entrance exam together.",
        "open_app": "📱 Open the app",
        "daily": "🎯 Daily question",
        "reminders_on": "🔔 Reminders: on",
        "reminders_off": "🔕 Reminders: off",
        "language": "🌐 Language",
        "help": "❓ Help",
        "help_text": "Open the app, answer the daily question and enable reminders. Issues: support@dtm-ai.uz",
        "pick_language": "Choose a language:",
        "language_saved": "Language saved ✅",
        "link_ok": "Account linked ✅ Reminders will arrive here.",
        "link_bad": "The link code is invalid or expired. Get a new one in the app.",
        "need_link": "Link your account in the app first to enable reminders.",
        "no_question": "No question available right now. Try again later.",
        "correct": "✅ Correct!",
        "wrong": "❌ Wrong.",
        "expired": "This question is no longer available.",
        "reminders_enabled": "Reminders enabled 🔔",
        "reminders_disabled": "Reminders disabled 🔕",
    },
}


def t(locale: str, key: str, **params: object) -> str:
    table = STRINGS.get(locale) or STRINGS[DEFAULT_LOCALE]
    return table[key].format(**params) if params else table[key]


def locale_from_telegram(language_code: str | None) -> str:
    code = (language_code or "").lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    if code.startswith("uz") and "cyr" in code:
        return "uz-Cyrl"
    return DEFAULT_LOCALE
