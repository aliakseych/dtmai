import logging
from uuid import UUID

from app.bootstrap.tasks import broker
from app.modules.ai.wiring import get_gateway
from app.modules.labeling.application.generation import GenerationService
from app.modules.labeling.application.ingest import IngestService
from app.modules.labeling.application.solve import SolveService
from app.modules.labeling.infrastructure.config import get_labeling_settings
from app.shared.db import get_sessionmaker

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
    for i in range(0, len(created), CHUNK):
        await solve_questions.kiq([str(q) for q in created[i : i + CHUNK]], "ingestion")
    return len(created)
