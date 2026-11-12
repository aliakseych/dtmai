from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.interfaces.http.v1 import catalog as route


@pytest.mark.asyncio
async def test_subjects_carry_verified_question_count(monkeypatch: pytest.MonkeyPatch) -> None:
    full, empty = uuid4(), uuid4()

    async def count(_s, subject_id):  # noqa: ANN001, ANN202
        return {full: 12, empty: 0}[subject_id]

    monkeypatch.setattr(route.bank, "count_verified_for_subject", count)
    subs = [
        SimpleNamespace(id=i, code=c, names={"en": c}, weight=1.0, active=True, position=n)
        for n, (i, c) in enumerate([(full, "math"), (empty, "history")])
    ]
    out = await route.subjects_with_counts(None, subs)  # type: ignore[arg-type]
    assert [(o.code, o.question_count) for o in out] == [("math", 12), ("history", 0)]
