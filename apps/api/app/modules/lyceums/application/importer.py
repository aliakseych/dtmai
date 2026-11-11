import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import UUID

import structlog

from app.modules.lyceums.domain.models import ImportRun, ImportStatus, validate_year
from app.modules.lyceums.ports import ImportRunRepository, ImportSink, LyceumStatsSource
from app.shared.errors import NotFound

log = structlog.get_logger()


class LyceumImporter:
    """Pulls the admission overview and stamps every row with the requested year.

    The upstream API has no year field, so the year is the admin's input.
    Re-running a year upserts and keeps manually entered passing scores.
    """

    def __init__(
        self,
        source: LyceumStatsSource,
        sink: ImportSink,
        runs: ImportRunRepository,
        *,
        concurrency: int = 8,
        checkpoint: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        self._checkpoint = checkpoint
        self._source = source
        self._sink = sink
        self._runs = runs
        self._concurrency = max(1, concurrency)

    async def start(self, year: int, requested_by: UUID | None) -> ImportRun:
        return await self._runs.create(validate_year(year), requested_by)

    async def run(self, run_id: UUID) -> ImportRun:
        run = await self._runs.get(run_id)
        if run is None:
            raise NotFound("import run not found", code="import_run_not_found")
        run.status = ImportStatus.RUNNING
        await self._runs.save(run)
        await self._commit()
        try:
            await self._import(run)
            run.status = ImportStatus.SUCCEEDED
        except Exception as e:  # noqa: BLE001 - the run records any failure
            log.exception("lyceums.import_failed", run_id=str(run.id))
            run.status, run.error = ImportStatus.FAILED, f"{type(e).__name__}: {e}"[:500]
        run.finished_at = datetime.now(UTC)
        await self._runs.save(run)
        await self._commit()
        return run

    async def _commit(self) -> None:
        if self._checkpoint is not None:
            await self._checkpoint()

    async def _import(self, run: ImportRun) -> None:
        languages = await self._source.languages()
        lyceums = await self._source.lyceums()
        language_ids = {lang.external_id: await self._sink.upsert_language(lang) for lang in languages}
        sem = asyncio.Semaphore(self._concurrency)

        async def fetch(lyc_ext: int, lang_ext: int):  # type: ignore[no-untyped-def]
            async with sem:
                try:
                    return await self._source.specialities(lyc_ext, lang_ext)
                except Exception:  # noqa: BLE001 - one failing pair must not abort the run
                    run.errors += 1
                    log.warning("lyceums.fetch_failed", lyceum=lyc_ext, language=lang_ext)
                    return []

        for lyceum in lyceums:
            lyceum_id = await self._sink.upsert_lyceum(lyceum)
            run.lyceums += 1
            results = await asyncio.gather(*(fetch(lyceum.external_id, ext) for ext in language_ids))
            for lang_ext, specialities in zip(language_ids, results, strict=True):
                for item in specialities:
                    await self._sink.upsert_stat(
                        lyceum_id=lyceum_id, language_id=language_ids[lang_ext],
                        year=run.year, item=item,
                    )
                    run.stats += 1
            await self._runs.save(run)
            await self._commit()
        if run.errors and run.stats == 0:
            raise RuntimeError("every speciality request failed")
