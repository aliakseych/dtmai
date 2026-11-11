LOCALE_LANGUAGE = {
    "uz-Latn": "Uzbek (Latin script)",
    "uz-Cyrl": "Uzbek (Cyrillic script)",
    "ru": "Russian",
    "en": "English",
}


def language_name(locale: str) -> str:
    return LOCALE_LANGUAGE.get(locale, "Uzbek (Latin script)")
