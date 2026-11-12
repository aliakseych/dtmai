import pytest

from app.shared import events


class _Session:
    def __init__(self) -> None:
        self.order: list[str] = []

    async def commit(self) -> None:
        self.order.append("commit")


async def test_commit_and_dispatch_commits_then_delivers(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _Session()

    async def fake_dispatch(limit: int = 200) -> int:
        s.order.append("dispatch")
        return 1

    monkeypatch.setattr(events, "dispatch_pending", fake_dispatch)
    await events.commit_and_dispatch(s)  # type: ignore[arg-type]
    assert s.order == ["commit", "dispatch"]


async def test_dispatch_failure_does_not_fail_the_request(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _Session()

    async def boom(limit: int = 200) -> int:
        raise RuntimeError("down")

    monkeypatch.setattr(events, "dispatch_pending", boom)
    await events.commit_and_dispatch(s)  # type: ignore[arg-type]
    assert s.order == ["commit"]


async def test_finish_endpoint_credits_without_scheduler(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /finish commits and dispatches the outbox itself (no scheduler tick needed)."""
    from types import SimpleNamespace
    from uuid import uuid4

    from app.interfaces.http.v1 import learning as http

    called: list[object] = []

    async def fake_commit_and_dispatch(session: object) -> None:
        called.append(session)

    class _Svc:
        async def finish(self, user_id, session_id):  # noqa: ANN001, ANN202
            return object()

    monkeypatch.setattr(http, "commit_and_dispatch", fake_commit_and_dispatch)
    monkeypatch.setattr(http.FinishOut, "of", staticmethod(lambda r: r))
    db = object()
    await http.finish(uuid4(), SimpleNamespace(user_id=uuid4()), _Svc(), db)  # type: ignore[arg-type]
    assert called == [db]


async def test_session_completed_xp_feeds_xp_earned_quest(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace
    from uuid import uuid4

    from app.modules.gamification.application import service as svc_mod
    from app.modules.gamification.application.service import GamificationService

    monkeypatch.setattr(svc_mod, "clamp_session_xp", lambda xp, total, caps: xp)
    monkeypatch.setattr(svc_mod, "tashkent_day", lambda now: now)

    advanced: list[tuple[str, int]] = []
    s = GamificationService.__new__(GamificationService)
    stats = SimpleNamespace(lessons_completed=0, hearts=None)
    cfg = SimpleNamespace(xp_caps=SimpleNamespace(daily_cap=600, session_cap=150, per_item_cap=10))

    async def load(_u):  # noqa: ANN001, ANN202
        return stats, cfg, 5, False, __import__("datetime").datetime(2026, 1, 5, 9)

    async def mark(*_):  # noqa: ANN002, ANN202
        return True

    async def noop(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        return None

    async def award(*_a, **_k):  # noqa: ANN002, ANN003, ANN202
        return 6

    async def adv(_stats, _cfg, _day, metric, amount):  # noqa: ANN001, ANN202
        advanced.append((metric, amount))

    s._load = load  # type: ignore[method-assign]
    s._stats = SimpleNamespace(mark_event=mark, save=noop)  # type: ignore[assignment]
    s._sync_profile = noop  # type: ignore[method-assign]
    s._award_xp = award  # type: ignore[method-assign]
    s._touch_streak = noop  # type: ignore[method-assign]
    s._advance = adv  # type: ignore[method-assign]
    s._achievements = noop  # type: ignore[method-assign]
    await s.on_session_completed(uuid4(), uuid4(), "s1", "drill", 6, 3, 4)
    assert ("xp_earned", 6) in advanced
