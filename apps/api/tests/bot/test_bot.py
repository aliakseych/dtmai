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


class _FakeRedis:
    def __init__(self) -> None:
        self.kv: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.kv[key] = value

    async def eval(self, _script: str, _n: int, key: str, arg: str) -> int:
        if self.kv.get(key) == arg:
            del self.kv[key]
            return 1
        return 0


def test_issued_question_is_consumed_once_and_only_for_that_chat() -> None:
    import asyncio

    from app.interfaces.bot.issued import RedisIssuedStore

    store = RedisIssuedStore(_FakeRedis())  # type: ignore[arg-type]
    qid, other = uuid4(), uuid4()

    async def run() -> list[bool]:
        await store.issue(1, qid)
        return [
            await store.consume(1, other),
            await store.consume(2, qid),
            await store.consume(1, qid),
            await store.consume(1, qid),
        ]

    assert asyncio.run(run()) == [False, False, True, False]
