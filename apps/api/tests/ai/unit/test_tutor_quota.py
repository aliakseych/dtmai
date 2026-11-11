import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
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
    def __init__(self, ledger: FakeLedger) -> None:
        self._ledger = ledger

    async def routes(self, task):  # noqa: ANN001, ANN201
        return [SimpleNamespace(model="m")]

    async def complete(self, route, messages, *, purpose, user_id):  # noqa: ANN001, ANN201
        await asyncio.sleep(0.01)  # slow LLM: both requests would pass a naive check meanwhile
        self._ledger.calls[user_id] += 1
        return SimpleNamespace(text="ok")


class FakeSlots:
    def __init__(self) -> None:
        self._locks: dict[object, asyncio.Lock] = defaultdict(asyncio.Lock)

    @asynccontextmanager
    async def hold(self, user_id):  # noqa: ANN001, ANN201
        async with self._locks[user_id]:
            yield


@pytest.mark.asyncio
async def test_concurrent_chats_cannot_exceed_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ents(_uid):  # noqa: ANN001, ANN202
        return SimpleNamespace(limit=lambda _k, _d: 1)

    monkeypatch.setattr(tutor_mod, "entitlements_for", ents)
    monkeypatch.setattr(
        tutor_mod, "get_ai_settings", lambda: SimpleNamespace(ai_temur_daily_quota=1)
    )
    ledger = FakeLedger()
    svc = TutorService(FakeGateway(ledger), ledger, NoActiveMock(), FakeSlots())  # type: ignore[arg-type]
    uid = uuid4()

    async def go():  # noqa: ANN202
        return await svc.chat(None, uid, [ChatTurn("user", "hi")], question_id=None, locale="en")  # type: ignore[arg-type]

    results = await asyncio.gather(go(), go(), go(), return_exceptions=True)
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert sum(isinstance(r, TutorLimitReached) for r in results) == 2
    assert ledger.calls[uid] == 1
