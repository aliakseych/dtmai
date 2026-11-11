from typing import Protocol
from uuid import UUID

from app.modules.lyceums.domain.models import (
    ImportRun,
    SourceLanguage,
    SourceLyceum,
    SourceSpeciality,
)


class LyceumStatsSource(Protocol):
    """Where admission overview data comes from (swappable adapter)."""

    async def lyceums(self) -> list[SourceLyceum]: ...
    async def languages(self) -> list[SourceLanguage]: ...
    async def specialities(
        self, lyceum_external_id: int, language_external_id: int
    ) -> list[SourceSpeciality]: ...


class ImportSink(Protocol):
    """Write side used by the importer."""

    async def upsert_lyceum(self, item: SourceLyceum) -> UUID: ...
    async def upsert_language(self, item: SourceLanguage) -> UUID: ...
    async def upsert_stat(
        self, *, lyceum_id: UUID, language_id: UUID, year: int, item: SourceSpeciality
    ) -> None: ...


class ImportRunRepository(Protocol):
    async def create(self, year: int, requested_by: UUID | None) -> ImportRun: ...
    async def get(self, run_id: UUID) -> ImportRun | None: ...
    async def save(self, run: ImportRun) -> None: ...
    async def list(self, limit: int) -> list[ImportRun]: ...
