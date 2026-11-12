from uuid import uuid4

import pytest

from app.interfaces.http.v1 import catalog as route


@pytest.mark.asyncio
async def test_bases_without_verified_questions_are_hidden(monkeypatch: pytest.MonkeyPatch) -> None:
    full, empty, off = uuid4(), uuid4(), uuid4()

    async def count(_s, source_id):  # noqa: ANN001, ANN202
        return {full: 3, empty: 0, off: 9}[source_id]

    monkeypatch.setattr(route.bank, "count_verified_by_source", count)
    bases = [
        {"id": full, "active": True},
        {"id": empty, "active": True},
        {"id": off, "active": False},
    ]
    out = await route.servable_bases(None, bases)  # type: ignore[arg-type]
    assert [b["id"] for b in out] == [full]
