from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.ai.application import explain as explain_mod
from app.modules.ai.application.errors import GuestNotAllowed
from app.modules.ai.application.explain import ExplainService
from app.shared.errors import Forbidden


class _Mocks:
    def __init__(self, active: bool) -> None:
        self.active = active

    async def has_active_mock(self, user_id):  # noqa: ANN001, ANN201
        return self.active


class _Session:
    def __init__(self) -> None:
        self.sql: list[str] = []

    async def execute(self, stmt, params=None):  # noqa: ANN001, ANN201
        self.sql.append(str(stmt))
        raise _Stop


class _Stop(Exception):
    pass


@pytest.mark.asyncio
async def test_guest_is_refused() -> None:
    svc = ExplainService(None, _Mocks(False))  # type: ignore[arg-type]
    with pytest.raises(GuestNotAllowed):
        await svc.explain(None, uuid4(), frozenset({"guest"}), uuid4(), "en")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_active_mock_is_refused() -> None:
    svc = ExplainService(None, _Mocks(True))  # type: ignore[arg-type]
    with pytest.raises(Forbidden) as e:
        await svc.explain(None, uuid4(), frozenset({"student"}), uuid4(), "en")  # type: ignore[arg-type]
    assert e.value.code == "explain_locked_during_mock"


@pytest.mark.asyncio
async def test_quota_path_takes_advisory_lock_first(monkeypatch: pytest.MonkeyPatch) -> None:
    async def ents(_uid):  # noqa: ANN001, ANN202
        return SimpleNamespace(has=lambda _f: False, limit=lambda _k, _d: 3)

    monkeypatch.setattr(explain_mod, "entitlements_for", ents)
    monkeypatch.setattr(
        explain_mod, "get_ai_settings", lambda: SimpleNamespace(ai_explanations_per_day_default=3)
    )
    s = _Session()
    svc = ExplainService(None, _Mocks(False))  # type: ignore[arg-type]
    with pytest.raises(_Stop):
        await svc.explain(s, uuid4(), frozenset({"student"}), uuid4(), "en")  # type: ignore[arg-type]
    assert "pg_advisory_xact_lock(hashtext('explain:'" in s.sql[0]


@pytest.mark.asyncio
async def test_slow_model_call_times_out_as_upstream_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import asyncio

    from app.modules.ai.application.errors import AIUpstreamFailed

    async def ents(_uid):  # noqa: ANN001, ANN202
        return SimpleNamespace(has=lambda _f: True, limit=lambda _k, _d: -1)

    async def none(*_a):  # noqa: ANN002, ANN202
        return None

    async def questions(*_a):  # noqa: ANN002, ANN202
        return [SimpleNamespace(language="uz", stem="s", payload={})]

    async def grade(*_a):  # noqa: ANN002, ANN202
        return SimpleNamespace(correct_response={})

    class _Gw:
        async def routes(self, _t):  # noqa: ANN001, ANN201
            return [SimpleNamespace(model="m")]

        async def complete_json(self, *_a, **_k):  # noqa: ANN002, ANN003, ANN201
            await asyncio.sleep(5)

    class _Sess:
        async def execute(self, *_a, **_k):  # noqa: ANN002, ANN003, ANN201
            return None

    monkeypatch.setattr(explain_mod, "entitlements_for", ents)
    monkeypatch.setattr(
        explain_mod, "get_ai_settings", lambda: SimpleNamespace(ai_explain_timeout_seconds=0.05)
    )
    monkeypatch.setattr(explain_mod.bank, "get_explanation", none)
    monkeypatch.setattr(explain_mod.bank, "get_questions", questions)
    monkeypatch.setattr(explain_mod.bank, "grade", grade)
    svc = ExplainService(_Gw(), _Mocks(False))  # type: ignore[arg-type]
    with pytest.raises(AIUpstreamFailed):
        await svc.explain(_Sess(), uuid4(), frozenset({"student"}), uuid4(), "en")  # type: ignore[arg-type]
