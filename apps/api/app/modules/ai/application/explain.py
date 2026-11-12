import hashlib
import json
from datetime import date
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.errors import (
    AIUpstreamFailed,
    ExplanationLimitReached,
    ensure_registered,
)
from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.domain.budget import within_quota
from app.modules.ai.domain.locale import language_name
from app.modules.ai.domain.routing import Task
from app.modules.ai.infrastructure.clock import tashkent_today
from app.modules.ai.infrastructure.config import get_ai_settings
from app.modules.ai.infrastructure.orm import ExplainUsageRow
from app.modules.ai.ports import ActiveMockChecker, LLMMessage
from app.modules.bank import facade as bank
from app.shared.entitlements import entitlements_for
from app.shared.errors import Forbidden, NotFound

SYSTEM = (
    "You are a patient exam tutor for the Uzbekistan lyceum entrance exam. Explain why the given "
    "correct answer is right and, briefly, why common wrong choices fail. Use Markdown with KaTeX "
    '($...$) for math. Be concise (under 180 words). Reply ONLY with JSON: {"explanation": "..."}.'
)


class ExplainService:
    def __init__(self, gateway: AIGateway, mock_checker: ActiveMockChecker) -> None:
        self._gw = gateway
        self._mocks = mock_checker

    async def explain(
        self,
        session: AsyncSession,
        user_id: UUID,
        roles: frozenset[str],
        question_id: UUID,
        locale: str,
    ) -> tuple[str, bool, str | None]:
        """Returns (text, cached, model). Registered users only, and never during a mock."""
        ensure_registered(roles)
        if await self._mocks.has_active_mock(user_id):
            raise Forbidden(
                "AI explanations are unavailable during a mock exam",
                code="explain_locked_during_mock",
            )
        ent = await entitlements_for(user_id)
        unlimited = (
            ent.has("ai_unlimited_explanations") or ent.limit("ai_explanations_per_day", 0) < 0
        )
        today = tashkent_today()

        if not unlimited:
            # Serialize this user's quota check + insert for the day (released at commit).
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext('explain:' || :uid || ':' || :day))"),
                {"uid": str(user_id), "day": today.isoformat()},
            )
            limit = ent.limit(
                "ai_explanations_per_day", get_ai_settings().ai_explanations_per_day_default
            )
            inserted = await session.execute(
                insert(ExplainUsageRow)
                .values(user_id=user_id, day=today, question_id=question_id)
                .on_conflict_do_nothing()
                .returning(ExplainUsageRow.question_id)
            )
            if inserted.first() is not None:
                used = await _count_usage(session, user_id, today)
                if not within_quota(limit, used - 1):
                    raise ExplanationLimitReached("Daily AI explanation limit reached")

        cached = await bank.get_explanation(session, question_id, locale)
        if cached:
            return cached, True, None

        # One generation per (question, locale) even under concurrent requests.
        key = int.from_bytes(
            hashlib.sha256(f"{question_id}:{locale}".encode()).digest()[:8], "big", signed=True
        )
        await session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": key})
        cached = await bank.get_explanation(session, question_id, locale)
        if cached:
            return cached, True, None

        questions = await bank.get_questions(session, [question_id])
        if not questions:
            raise NotFound("question not found")
        q = questions[0]
        graded = await bank.grade(session, question_id, {})
        route = (await self._gw.routes(Task.EXPLAIN))[0]
        user_msg = (
            f"Answer in {language_name(locale)}.\n"
            f"Question (language: {q.language}):\n{q.stem}\n\n"
            f"Choices/payload:\n{json.dumps(q.payload, ensure_ascii=False)}\n\n"
            f"Correct answer:\n{json.dumps(graded.correct_response, ensure_ascii=False)}"
        )
        data, _ = await self._gw.complete_json(
            route,
            [LLMMessage("system", SYSTEM), LLMMessage("user", user_msg)],
            purpose="explain",
            user_id=user_id,
            ref=str(question_id),
        )
        explanation = str(data.get("explanation", "")).strip()
        if not explanation:
            raise AIUpstreamFailed("model returned an empty explanation")
        await bank.upsert_explanation(session, question_id, locale, explanation, route.model)
        return explanation, False, route.model


async def _count_usage(session: AsyncSession, user_id: UUID, day: date) -> int:
    return int(
        await session.scalar(
            select(func.count())
            .select_from(ExplainUsageRow)
            .where(ExplainUsageRow.user_id == user_id, ExplainUsageRow.day == day)
        )
        or 0
    )
