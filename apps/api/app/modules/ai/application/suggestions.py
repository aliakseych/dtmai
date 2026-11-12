from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.domain.suggestions import build_suggestions
from app.modules.catalog import facade as catalog
from app.modules.learning import facade as learning

MAX_SUBJECTS = 5
WEAK_PER_SUBJECT = 2


def _name(names: dict[str, str], locale: str) -> str:
    return names.get(locale) or names.get("en") or next(iter(names.values()), "")


async def suggest_for(session: AsyncSession, user_id: UUID, locale: str) -> list[str]:
    """Prompts built from the learner's weakest topics across active subjects."""
    topics: list[str] = []
    for subject in (await catalog.list_subjects(session))[:MAX_SUBJECTS]:
        for area in await learning.weak_areas(session, user_id, subject.id, WEAK_PER_SUBJECT):
            if area.topic_id is not None:
                topics.append(
                    _name((await catalog.get_topic(session, area.topic_id)).names, locale)
                )
    return build_suggestions(locale, topics)
