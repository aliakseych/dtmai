import logging
from uuid import UUID

from app.bootstrap.tasks import broker
from app.modules.bank import facade as bank
from app.modules.ai.wiring import get_gateway
from app.modules.labeling.application.generation import GenerationService
from app.modules.labeling.application.ingest import IngestService
from app.modules.labeling.application.solve import SolveService
from app.modules.labeling.domain.autogen import plan_autogen
from app.modules.labeling.infrastructure.config import get_labeling_settings
from app.shared.db import get_sessionmaker
from app.shared.errors import NotFound, ValidationFailed

log = logging.getLogger(__name__)
CHUNK = 50


def _solver(session) -> SolveService:  # noqa: ANN001
    s = get_labeling_settings()
    return SolveService(session, get_gateway(), min_models=s.labeling_min_models, min_confidence=s.labeling_min_confidence)


@broker.task(task_name="labeling.solve_questions")
async def solve_questions(question_ids: list[str], trigger: str = "manual") -> int:
    done = 0
    async with get_sessionmaker()() as session:
        svc = _solver(session)
        for qid in question_ids:
            try:
                await svc.solve_question(UUID(qid), trigger=trigger)
                await session.commit()
                done += 1
            except Exception:  # noqa: BLE001 - keep going; the failure is logged
                await session.rollback()
                log.exception("solve failed for %s", qid)
    return done


@broker.task(task_name="labeling.run_generation")
async def run_generation(run_id: str) -> None:
    async with get_sessionmaker()() as session:
        svc = GenerationService(session, get_gateway())
        await svc.execute(UUID(run_id))
        await session.commit()


@broker.task(task_name="labeling.run_import")
async def run_import(batch_id: str) -> int:
    async with get_sessionmaker()() as session:
        created = await IngestService(session, get_gateway()).run(UUID(batch_id))
        run_ids = await _plan_followup_runs(session, created)
    for i in range(0, len(created), CHUNK):
        await solve_questions.kiq([str(q) for q in created[i : i + CHUNK]], "ingestion")
    for rid in run_ids:
        await run_generation.kiq(rid)
    return len(created)


async def _plan_followup_runs(session, created: list[UUID]) -> list[str]:  # noqa: ANN001
    """Create generation runs (per subject/topic/type/language) for freshly imported questions."""
    s = get_labeling_settings()
    if not created or s.labeling_autogen_per_question <= 0 or s.labeling_autogen_max_per_batch <= 0:
        return []
    groups: dict[tuple[UUID, UUID, UUID, str], int] = {}
    for i in range(0, len(created), CHUNK):
        for q in await bank.get_questions(session, created[i : i + CHUNK]):
            if q.topic_id is None:
                continue
            key = (q.subject_id, q.topic_id, q.type_id, q.language)
            groups[key] = groups.get(key, 0) + 1
    svc = GenerationService(session, get_gateway())
    run_ids: list[str] = []
    for (subject_id, topic_id, type_id, language), count in plan_autogen(
        groups, s.labeling_autogen_per_question, s.labeling_autogen_max_per_batch
    ):
        try:
            run = await svc.create_run(
                subject_id=subject_id, topic_id=topic_id, type_id=type_id, language=language, count=count,
                difficulty=None, prompt_template=None, created_by=None,
            )
        except (ValidationFailed, NotFound):
            continue  # non-generatable kind: nothing to follow up
        run_ids.append(str(run.id))
    await session.commit()
    return run_ids
