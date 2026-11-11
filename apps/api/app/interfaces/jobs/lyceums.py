from uuid import UUID

from app.bootstrap.tasks import broker
from app.modules.lyceums.application.importer import LyceumImporter
from app.modules.lyceums.infrastructure.eduuz import EduUzSource
from app.modules.lyceums.infrastructure.repositories import SqlImportRuns, SqlImportSink
from app.modules.lyceums.settings import get_lyceums_settings
from app.shared.db import get_sessionmaker


@broker.task(task_name="lyceums.import_year")
async def import_year(run_id: str) -> None:
    cfg = get_lyceums_settings()
    source = EduUzSource(base_url=cfg.edu_api_base_url)
    try:
        async with get_sessionmaker()() as session:
            importer = LyceumImporter(
                source, SqlImportSink(session), SqlImportRuns(session),
                concurrency=cfg.lyceums_import_concurrency, checkpoint=session.commit,
            )
            await importer.run(UUID(run_id))
    finally:
        await source.aclose()
