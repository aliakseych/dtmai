"""DB test: two AttemptGraded events for one user+topic delivered in ONE outbox batch must both
land in mastery (no lost update from a stale identity-map read).

Runs against DATABASE_URL inside a rolled-back transaction; skipped when no DB is reachable.
"""

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.modules.learning import wiring as learning_wiring
from app.modules.learning.infrastructure.orm import MasteryRow
from app.modules.learning.ports import Item
from app.shared import events
from app.shared.events import Event, publish

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="needs Postgres")


class _StubContent:
    """Replaces the bank/catalog facade: resolves question ids to fixed items."""

    items_by_id: dict[UUID, Item] = {}

    def __init__(self, _session: AsyncSession) -> None: ...

    async def items(self, ids):  # noqa: ANN001, ANN202
        return [self.items_by_id[i] for i in ids if i in self.items_by_id]


def _item(qid: UUID, subject: UUID, topic: UUID, type_id: UUID) -> Item:
    return Item(qid, subject, topic, type_id, "single", "uz", 0.0, "q", [], {}, None, False)


def _graded(user: UUID, qid: UUID, topic: UUID, type_id: UUID, subject: UUID, ok: bool, at):  # noqa: ANN001, ANN202
    return Event(
        "AttemptGraded",
        {
            "user_id": str(user),
            "question_id": str(qid),
            "question_type_id": str(type_id),
            "topic_id": str(topic),
            "subject_id": str(subject),
            "correct": ok,
            "mode": "mock",
            "session_id": str(uuid4()),
        },
        occurred_at=at,
    )


async def test_two_answers_same_topic_in_one_batch_both_count(monkeypatch):
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            for schema, table in (("learning", "mastery"), ("shared", "outbox")):
                if not await conn.run_sync(
                    lambda c, s=schema, t=table: c.dialect.has_table(c, t, schema=s)
                ):
                    pytest.skip(f"{schema}.{table} not migrated")

            user, subject, topic, type_id = uuid4(), uuid4(), uuid4(), uuid4()
            q1, q2 = uuid4(), uuid4()
            _StubContent.items_by_id = {
                q1: _item(q1, subject, topic, type_id),
                q2: _item(q2, subject, topic, type_id),
            }
            # Route the dispatcher's own session through the test transaction (savepoints), and
            # run only the learning handler so unrelated modules stay out of this test.
            maker = async_sessionmaker(
                bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
            )
            monkeypatch.setattr(events, "get_sessionmaker", lambda: maker)
            monkeypatch.setattr(
                events, "_handlers", {"AttemptGraded": [learning_wiring._on_attempt_graded]}
            )
            monkeypatch.setattr(learning_wiring, "FacadeContent", _StubContent)

            # Ancient timestamps so these rows sort first in the batch (dispatch is oldest-first).
            t0 = datetime(2000, 1, 1, tzinfo=UTC)
            t1 = datetime(2000, 1, 1, 0, 0, 1, tzinfo=UTC)
            async with maker() as s:
                await publish(s, _graded(user, q1, topic, type_id, subject, True, t0))
                await publish(s, _graded(user, q2, topic, type_id, subject, False, t1))
                await s.commit()

            await events.dispatch_pending()

            async with maker() as s:
                row = (
                    await s.execute(
                        select(MasteryRow).where(
                            MasteryRow.user_id == user,
                            MasteryRow.topic_id == topic,
                            MasteryRow.type_id == type_id,
                        )
                    )
                ).scalar_one_or_none()
            assert row is not None, "no mastery row written for the batch"
            assert row.attempts == 2, f"lost update: attempts={row.attempts}, expected 2"
            assert row.correct == 1, f"lost update: correct={row.correct}, expected 1"
            # EMA: 0.5 -> +0.5*(1-0.5)=0.75 -> +(1/3)*(0-0.75)=0.5
            assert row.score == pytest.approx(0.5), f"score={row.score}, expected 0.5"
            await tx.rollback()
    finally:
        await engine.dispose()
