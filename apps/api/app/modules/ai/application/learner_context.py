"""Learner profile block for Temur's system prompt (track, subjects, weak topics, dream lyceum)."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog import facade as catalog
from app.modules.exam_info import facade as exam_info
from app.modules.identity.wiring import build_identity_service
from app.modules.learning import facade as learning
from app.modules.lyceums import facade as lyceums

MAX_WEAK_TOPICS = 5
WEAK_PER_SUBJECT = 2


@dataclass(frozen=True, slots=True)
class LearnerProfile:
    locale: str
    track: str | None
    subjects: tuple[str, ...]
    weak_topics: tuple[str, ...]
    dream_lyceums: tuple[str, ...]


def render_learner_context(p: LearnerProfile) -> str:
    """Prompt block; empty when nothing is known beyond the locale."""
    if not (p.track or p.subjects or p.weak_topics or p.dream_lyceums):
        return ""
    return (
        "Learner profile (authoritative; use it, never ask the student for what is listed here).\n"
        f"Interface locale: {p.locale}.\n"
        f"Track: {p.track or 'not chosen'}.\n"
        f"Track subjects: {', '.join(p.subjects) or 'n/a'}.\n"
        f"Weak topics (lowest mastery first): {', '.join(p.weak_topics) or 'no data yet'}.\n"
        f"Dream lyceum: {', '.join(p.dream_lyceums) or 'not set'}.\n"
        "Tailor advice to this track and these weak topics; do not suggest subjects outside the track."
    )


def _name(names: dict[str, str], locale: str) -> str:
    for key in (locale, "uz-Latn", "ru", "en", "uz-Cyrl"):
        if names.get(key):
            return names[key]
    return ""


async def load_learner_profile(session: AsyncSession, user_id: UUID, locale: str) -> LearnerProfile:
    user = await build_identity_service(session).get_me(user_id)
    all_subjects = await catalog.list_subjects(session)
    wanted = set(user.subject_ids)
    track_subjects = [s for s in all_subjects if s.id in wanted] if wanted else []

    track: str | None = None
    if user.field_code:
        track = user.field_code
        for p in await exam_info.list_profiles(session):
            if p.direction_code == user.field_code and _name(p.names, locale):
                track = _name(p.names, locale)
                break

    weak: list[str] = []
    for s in track_subjects or all_subjects:
        for area in await learning.weak_areas(session, user_id, s.id, WEAK_PER_SUBJECT):
            if area.topic_id is None:
                continue
            label = _name((await catalog.get_topic(session, area.topic_id)).names, locale)
            if label and label not in weak:
                weak.append(label)
    return LearnerProfile(
        locale=locale,
        track=track,
        subjects=tuple(n for n in (_name(s.names, locale) for s in track_subjects) if n),
        weak_topics=tuple(weak[:MAX_WEAK_TOPICS]),
        dream_lyceums=tuple(await lyceums.lyceum_names(session, list(user.dream_lyceum_ids))),
    )


async def learner_context(session: AsyncSession, user_id: UUID, locale: str) -> str:
    return render_learner_context(await load_learner_profile(session, user_id, locale))
