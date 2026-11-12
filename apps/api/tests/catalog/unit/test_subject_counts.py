from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.interfaces.http.v1 import catalog as route


@pytest.mark.asyncio
async def test_subjects_carry_verified_question_count(monkeypatch: pytest.MonkeyPatch) -> None:
    full, empty = uuid4(), uuid4()

    async def counts(_s, language=None):  # noqa: ANN001, ANN202
        return {full: 12}

    monkeypatch.setattr(route.bank, "verified_counts_by_subject", counts)
    subs = [
        SimpleNamespace(id=i, code=c, names={"en": c}, weight=1.0, active=True, position=n)
        for n, (i, c) in enumerate([(full, "math"), (empty, "history")])
    ]
    out = await route.subjects_with_counts(None, subs)  # type: ignore[arg-type]
    assert [(o.code, o.question_count) for o in out] == [("math", 12), ("history", 0)]


@pytest.mark.asyncio
async def test_subject_counts_are_per_language(monkeypatch: pytest.MonkeyPatch) -> None:
    sid = uuid4()
    per_language = {"uz": 77, "ru": 5, "en": 0}

    async def counts(_s, language=None):  # noqa: ANN001, ANN202
        return {sid: per_language[language]}

    monkeypatch.setattr(route.bank, "verified_counts_by_subject", counts)
    subs = [
        SimpleNamespace(
            id=sid, code="math", names={"en": "Math"}, weight=1.0, active=True, position=0
        )
    ]
    got = {
        lang: (await route.subjects_with_counts(None, subs, lang))[0].question_count  # type: ignore[arg-type]
        for lang in per_language
    }
    assert got == per_language
