from app.interfaces.jobs import assessment as job


class _Session:
    async def commit(self) -> None: ...


class _Svc:
    async def auto_submit_expired(self) -> int:
        return 0


def _patch(monkeypatch, calls: list) -> None:
    class _Ctx:
        async def __aenter__(self):
            return _Session()

        async def __aexit__(self, *a):
            return False

    monkeypatch.setattr(job, "get_sessionmaker", lambda: lambda: _Ctx())
    monkeypatch.setattr(job, "build_assessment_service", lambda s: _Svc())

    async def fake_dispatch(limit: int = 200) -> int:
        calls.append(1)
        return 0

    monkeypatch.setattr(job, "dispatch_pending", fake_dispatch)


async def test_dispatch_runs_even_when_nothing_was_auto_submitted(monkeypatch):
    calls: list = []
    _patch(monkeypatch, calls)
    assert await job.auto_submit_expired() == 0
    assert calls == [1]


async def test_dedicated_dispatch_task_drains_the_outbox(monkeypatch):
    calls: list = []
    _patch(monkeypatch, calls)
    await job.dispatch_outbox()
    assert calls == [1]
