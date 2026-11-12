import asyncio
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from app.modules.bank.application.service import BankService
from app.modules.bank.domain.models import Passage, Question
from app.shared.errors import ValidationFailed


def _q(kind: str = "single_choice", payload: dict[str, Any] | None = None) -> Question:
    return Question(
        id=uuid4(),
        subject_id=uuid4(),
        topic_id=uuid4(),
        type_id=uuid4(),
        kind=kind,
        language="uz",
        stem="2+2?",
        payload=payload if payload is not None else {"options": [{"id": "a", "text": "4"}]},
        answer={},
    )


class Repo:
    def __init__(self, q: Question | None = None, p: Passage | None = None) -> None:
        self.q, self.p = q, p

    async def get_many(self, ids: Any) -> list[Question]:
        return [self.q] if self.q else []

    async def get_passage(self, pid: Any) -> Passage | None:
        return self.p

    async def save(self, q: Any) -> None: ...
    async def save_passage(self, p: Any) -> None: ...
    async def add_audit(self, *a: Any, **k: Any) -> None: ...


@pytest.mark.parametrize("key", ["stem", "language", "payload", "answer", "topic_id", "difficulty"])
def test_null_patch_is_422(key: str) -> None:
    repo = Repo(_q())
    svc = BankService(repo)  # type: ignore[arg-type]
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.update(repo.q.id, {key: None}, None))  # type: ignore[union-attr]


def test_group_payload_patch_keeps_child_ids() -> None:
    q = _q("passage_group", {"child_ids": ["c1"]})
    svc = BankService(Repo(q))  # type: ignore[arg-type]
    out = asyncio.run(svc.update(q.id, {"payload": {}}, None))
    assert out.payload["child_ids"] == ["c1"]


@pytest.mark.parametrize(
    "patch", [{"text": "  "}, {"language": "!!"}, {"text": None}, {"language": None}]
)
def test_update_passage_validates_like_create(patch: dict[str, Any]) -> None:
    p = Passage(uuid4(), "uz", "text", None, [], None)
    svc = BankService(Repo(p=p))  # type: ignore[arg-type]
    with pytest.raises(ValidationFailed):
        asyncio.run(svc.update_passage(p.id, patch))


def test_update_passage_valid_patch_applies() -> None:
    p = Passage(uuid4(), "uz", "text", "t", [], None)
    svc = BankService(Repo(p=p))  # type: ignore[arg-type]
    ok = asyncio.run(svc.update_passage(p.id, {"title": None, "text": "new"}))
    assert (ok.text, ok.title) == ("new", None)


_ = SimpleNamespace
