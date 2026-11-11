"""Accept-Language -> one of the supported UI locales."""

SUPPORTED = ("uz-Latn", "uz-Cyrl", "ru", "en")
DEFAULT = "uz-Latn"


def pick_locale(header: str | None) -> str:
    """First supported tag of an Accept-Language header (q-values ignored, order respected)."""
    for part in (header or "").split(","):
        tag = part.split(";")[0].strip().lower()
        if not tag:
            continue
        if tag.startswith("uz"):
            return "uz-Cyrl" if "cyrl" in tag else "uz-Latn"
        if tag.startswith("ru"):
            return "ru"
        if tag.startswith("en"):
            return "en"
    return DEFAULT
