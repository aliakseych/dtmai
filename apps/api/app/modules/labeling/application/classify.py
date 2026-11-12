"""Topic (re)classification of existing bank questions by one cheap text-only AI call per chunk."""

import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.domain.routing import Task
from app.modules.bank import facade as bank
from app.modules.labeling.application.prompts import classify_messages
from app.modules.labeling.domain.extraction import parse_classification, pick_topic
from app.modules.labeling.infrastructure import catalog_adapter

log = logging.getLogger(__name__)
CHUNK = 25


async def classify_topics(
    session: AsyncSession, gw: AIGateway, *, subject_id: UUID, question_ids: list[UUID]
) -> dict[UUID, UUID]:
    """Assign each question its best-matching topic; returns {question_id: topic_id} for changed rows."""
    topics = await catalog_adapter.ordered_topics(session, subject_id)
    if not topics:
        return {}
    labels, topic_ids = [t[1] for t in topics], [t[0] for t in topics]
    route = (await gw.routes(Task.EXTRACT))[0]
    changed: dict[UUID, UUID] = {}
    for i in range(0, len(question_ids), CHUNK):
        qs = await bank.get_questions(session, question_ids[i : i + CHUNK])
        data, _ = await gw.complete_json(
            route,
            classify_messages(labels, [q.stem for q in qs]),
            purpose="labeling.classify",
            ref=str(qs[0].id),
        )
        picks = parse_classification(data, len(qs))
        for pos, q in enumerate(qs):
            tid = pick_topic(picks.get(pos), topic_ids, None)
            if tid is None or tid == q.topic_id:
                continue
            await session.execute(
                text("UPDATE bank.questions SET topic_id=:t WHERE id=:q"), {"t": tid, "q": q.id}
            )
            await session.execute(
                text("UPDATE labeling.queue_items SET topic_id=:t WHERE question_id=:q"),
                {"t": tid, "q": q.id},
            )
            changed[q.id] = tid
        await session.commit()
    return changed
