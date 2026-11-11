from uuid import uuid4

from app.interfaces.bot.i18n import LOCALES, STRINGS, locale_from_telegram, t
from app.interfaces.bot.keyboards import parse_question_data, question_data
from app.interfaces.bot.webhook import secret_matches


def test_string_parity_across_locales() -> None:
    keys = set(STRINGS["en"])
    for loc in LOCALES:
        assert set(STRINGS[loc]) == keys, loc


def test_welcome_formats_name_and_unknown_locale_falls_back() -> None:
    assert "Ali" in t("ru", "welcome", name="Ali")
    assert t("xx", "daily") == t("uz-Latn", "daily")


def test_locale_from_telegram() -> None:
    assert locale_from_telegram("ru-RU") == "ru"
    assert locale_from_telegram("en") == "en"
    assert locale_from_telegram(None) == "uz-Latn"


def test_question_callback_roundtrip_and_size() -> None:
    qid = uuid4()
    data = question_data(qid, 3)
    assert len(data.encode()) <= 64
    assert parse_question_data(data) == (qid, 3)
    assert parse_question_data("dq:zz:1") is None
    assert parse_question_data("lang:en") is None


def test_secret_check() -> None:
    assert secret_matches("s3cret", "s3cret")
    assert not secret_matches("s3cret", "other")
    assert not secret_matches("s3cret", None)
    assert not secret_matches("", "")
