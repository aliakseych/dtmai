"""DB test: a failing passage group imports no rows. Rolled back; skipped without Postgres."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.bank.application.service import BankService
from app.modules.bank.infrastructure.orm import QuestionRow
from app.modules.bank.infrastructure.repositories import SqlQuestionRepository

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="needs Postgres")


def _child(ids: tuple[str, str, str]) -> dict:
    return {
        "subject_id": ids[0],
        "topic_id": ids[1],
        "type_id": ids[2],
        "kind": "single_choice",
        "language": "uz",
        "stem": "Qaysi biri to'g'ri?",
        "payload": {"options": [{"id": "a", "text": "bir"}, {"id": "b", "text": "ikki"}]},
        "answer": {"option_id": "a"},
    }


async def test_failed_group_leaves_no_rows() -> None:
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            trans = await conn.begin()
            session = AsyncSession(conn, join_transaction_mode="create_savepoint")
            ids = (str(uuid4()), str(uuid4()), str(uuid4()))
            before = await session.scalar(select(func.count()).select_from(QuestionRow))
            group = {
                **_child(ids),
                "kind": "passage_group",
                "stem": "bad \\u0041 escape",
                "payload": {},
                "answer": {},
                "children": [_child(ids), _child(ids)],
            }
            res = await BankService(SqlQuestionRepository(session)).import_items([group], None)
            assert res.created == [] and len(res.errors) == 1
            after = await session.scalar(select(func.count()).select_from(QuestionRow))
            assert after == before
            await trans.rollback()
    finally:
        await engine.dispose()
