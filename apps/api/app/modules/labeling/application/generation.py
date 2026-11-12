import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.domain.routing import Task
from app.modules.bank import facade as bank
from app.modules.labeling.application import prompts
from app.modules.labeling.application.solve import SolveService
from app.modules.labeling.domain.answers import SOLVABLE_KINDS
from app.modules.labeling.infrastructure import catalog_adapter
from app.modules.labeling.infrastructure.orm import GenerationRunRow
from app.shared.errors import DomainError, NotFound, ValidationFailed
from app.shared.ids import new_id

log = logging.getLogger(__name__)

EXAMPLES = 5  # few-shot examples per model call
BATCH = 5  # questions requested per model call


class GenerationService:
    def __init__(self, session: AsyncSession, gateway: AIGateway) -> None:
        self._s = session
        self._gw = gateway

    async def create_run(
        self,
        *,
        subject_id: UUID,
        topic_id: UUID,
        type_id: UUID,
        language: str,
        count: int,
        difficulty: float | None,
        prompt_template: str | None,
        created_by: UUID | None,
    ) -> GenerationRunRow:
        qt = await catalog_adapter.get_question_type(self._s, type_id)
        if qt is None:
            raise NotFound("Question type not found")
        if qt.kind not in SOLVABLE_KINDS:
            raise ValidationFailed(
                f"kind '{qt.kind}' cannot be generated", code="kind_not_generatable"
            )
        row = GenerationRunRow(
            id=new_id(),
            subject_id=subject_id,
            topic_id=topic_id,
            type_id=type_id,
            kind=qt.kind,
            language=language,
            requested=count,
            difficulty=difficulty,
            prompt_template=prompt_template,
            status="pending",
            created_by=created_by,
        )
        self._s.add(row)
        await self._s.flush()
        return row

    async def execute(self, run_id: UUID) -> None:
        run = await self._s.get(GenerationRunRow, run_id)
        if run is None:
            raise NotFound("Generation run not found")
        run.status = "running"
        await self._s.commit()
        qt = await catalog_adapter.get_question_type(self._s, run.type_id)
        subject = await self._subject_label(run.subject_id)
        route = (await self._gw.routes(Task.GENERATE))[0]
        template = run.prompt_template or (qt.prompt_template if qt else None)
        examples = await self._examples(run)
        remaining = run.requested
        created_ids: list[UUID] = []
        try:
            while remaining > 0:
                n = min(BATCH, remaining)
                data, _ = await self._gw.complete_json(
                    route,
                    prompts.generate_messages(
                        template,
                        kind=run.kind,
                        subject=subject,
                        topic=await _topic(self._s, run.topic_id),
                        language=run.language,
                        count=n,
                        difficulty=_difficulty_word(run.difficulty),
                        type_config=qt.config if qt else {},
                        examples=examples,
                    ),
                    purpose="labeling.generate",
                    ref=str(run.id),
                )
                items = data.get("questions")
                items = items if isinstance(items, list) else []
                for it in items[:n]:
                    try:
                        async with self._s.begin_nested():
                            qid = await self._create(run, it)
                        created_ids.append(qid)
                        run.created_count += 1
                    except (DomainError, KeyError, TypeError) as e:
                        log.warning("generated item rejected: %s", e)
                        run.failed_count += 1
                remaining -= n
                await self._s.commit()
            run.status = "done"
        except DomainError as e:
            run.status = "failed"
            run.error = e.detail
        run.finished_at = datetime.now(UTC)
        await self._s.commit()
        await self.solve_created(created_ids)

    async def _examples(self, run: GenerationRunRow) -> list[dict[str, Any]]:
        picked: list[bank.QuestionDTO] = []
        for statuses in (("verified",), ("auto_agreed", "draft")):
            if len(picked) >= EXAMPLES:
                break
            picked += await bank.pick_questions(
                self._s,
                subject_id=run.subject_id,
                topic_ids=[run.topic_id],
                type_ids=[run.type_id],
                language=run.language,
                n=EXAMPLES - len(picked),
                exclude_ids=[q.id for q in picked],
                statuses=statuses,
            )
        return [
            {"stem": q.stem, "payload": q.payload, "answer": await bank.get_answer(self._s, q.id)}
            for q in picked
        ]

    async def solve_created(self, ids: list[UUID]) -> None:
        solver = SolveService(self._s, self._gw)
        for qid in ids:
            try:
                await solver.solve_question(qid, trigger="generation")
                await self._s.commit()
            except DomainError as e:
                await self._s.rollback()
                log.warning("auto-solve failed for %s: %s", qid, e.detail)

    async def _create(self, run: GenerationRunRow, it: dict[str, Any]) -> UUID:
        if not isinstance(it, dict) or not it.get("stem") or not isinstance(it.get("answer"), dict):
            raise ValidationFailed("malformed generated question")
        payload = it.get("payload") if isinstance(it.get("payload"), dict) else {}
        cmd = bank.CreateQuestionCmd(
            subject_id=run.subject_id,
            topic_id=run.topic_id,
            type_id=run.type_id,
            kind=run.kind,
            language=run.language,
            stem=str(it["stem"]),
            payload=payload,
            answer=it["answer"],
            difficulty=run.difficulty or 1000.0,
            source_ref={"generation_run": str(run.id)},
            status="draft",
            created_by="labeling:generate",
        )
        return await bank.create_question(self._s, cmd)

    async def _subject_label(self, subject_id: UUID) -> str:
        for s in await catalog_adapter.list_subjects(self._s):
            if s.id == subject_id:
                return s.names.get("en") or s.code or str(subject_id)
        return str(subject_id)


async def _topic(session: AsyncSession, topic_id: UUID | None) -> str:
    if topic_id is None:
        return "any"
    try:
        return await catalog_adapter.topic_label(session, topic_id)
    except DomainError:
        return str(topic_id)


def _difficulty_word(elo: float | None) -> str:
    if elo is None or 900 <= elo <= 1100:
        return "medium"
    return "easy" if elo < 900 else "hard"
