import asyncio
from collections import defaultdict
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.ai.application import tutor as tutor_mod
from app.modules.ai.application.errors import TutorLimitReached
from app.modules.ai.application.tutor import ChatTurn, NoActiveMock, TutorService


class FakeLedger:
    def __init__(self) -> None:
        self.calls: dict[object, int] = defaultdict(int)

    async def user_calls_today(self, user_id, purpose):  # noqa: ANN001, ANN201
        return self.calls[user_id]


class FakeGateway:
    def __init__(self) -> None:
        self.in_flight = 0
        self.max_in_flight = 0

    async def routes(self, task):  # noqa: ANN001, ANN201
        return [SimpleNamespace(model="m")]

    async def complete(self, route, messages, *, purpose, user_id):  # noqa: ANN001, ANN201
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        await asyncio.sleep(0.01)
        self.in_flight -= 1
        return SimpleNamespace(text="ok")


class FakeSlots:
    """Reserve is atomic and short; nothing is held during the LLM call."""

    def __init__(self, ledger: FakeLedger) -> None:
        self._ledger = ledger
        self.released: list[object] = []

    async def reserve(self, user_id, limit):  # noqa: ANN001, ANN201
        if limit >= 0 and self._ledger.calls[user_id] >= limit:
            return None
        self._ledger.calls[user_id] += 1
        return uuid4()

    async def release(self, reservation_id):  # noqa: ANN001, ANN201
        self.released.append(reservation_id)


@pytest.mark.asyncio
async def test_concurrent_chats_cannot_exceed_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ents(_uid):  # noqa: ANN001, ANN202
        return SimpleNamespace(limit=lambda _k, _d: 1)

    monkeypatch.setattr(tutor_mod, "entitlements_for", ents)
    monkeypatch.setattr(
        tutor_mod, "get_ai_settings", lambda: SimpleNamespace(ai_temur_daily_quota=1)
    )

    async def no_catalog(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        return "catalog"

    monkeypatch.setattr(tutor_mod, "_catalog_context", no_catalog)
    ledger = FakeLedger()
    gw = FakeGateway()
    svc = TutorService(gw, ledger, NoActiveMock(), FakeSlots(ledger))  # type: ignore[arg-type]
    uid = uuid4()

    async def go():  # noqa: ANN202
        return await svc.chat(None, uid, [ChatTurn("user", "hi")], question_id=None, locale="en")  # type: ignore[arg-type]

    results = await asyncio.gather(go(), go(), go(), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert sum(isinstance(r, TutorLimitReached) for r in results) == 2
    assert ledger.calls[uid] == 1
    assert gw.max_in_flight == 1


@pytest.mark.asyncio
async def test_failed_llm_call_releases_reservation(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ents(_uid):  # noqa: ANN001, ANN202
        return SimpleNamespace(limit=lambda _k, _d: 5)

    monkeypatch.setattr(tutor_mod, "entitlements_for", ents)
    monkeypatch.setattr(
        tutor_mod, "get_ai_settings", lambda: SimpleNamespace(ai_temur_daily_quota=5)
    )

    async def no_catalog(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        return "catalog"

    monkeypatch.setattr(tutor_mod, "_catalog_context", no_catalog)
    ledger = FakeLedger()
    gw = FakeGateway()

    async def boom(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        raise RuntimeError("llm down")

    gw.complete = boom  # type: ignore[method-assign]
    slots = FakeSlots(ledger)
    svc = TutorService(gw, ledger, NoActiveMock(), slots)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        await svc.chat(None, uuid4(), [ChatTurn("user", "hi")], question_id=None, locale="en")  # type: ignore[arg-type]
    assert len(slots.released) == 1
