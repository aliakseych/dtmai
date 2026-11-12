"""DB test: re-importing edu.uz languages must not blank curated English names.

Runs against DATABASE_URL inside a rolled-back transaction; skipped when no DB is reachable.
"""

import os

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.modules.lyceums.domain.models import SourceLanguage
from app.modules.lyceums.infrastructure.orm import EducationLanguageRow
from app.modules.lyceums.infrastructure.repositories import SqlImportSink

URL = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not URL.startswith("postgresql"), reason="needs Postgres")


async def test_reimport_keeps_curated_english_name():
    engine = create_async_engine(URL)
    try:
        async with engine.connect() as conn:
            tx = await conn.begin()
            if not await conn.run_sync(
                lambda c: c.dialect.has_table(c, "education_languages", schema="lyceums")
            ):
                pytest.skip("lyceums schema not migrated")

            s = AsyncSession(bind=conn)
            sink = SqlImportSink(s)
            ext = 987_654_321
            lang_id = await sink.upsert_language(SourceLanguage(ext, "xx", "Uz", "English", "Ру"))
            again = await sink.upsert_language(SourceLanguage(ext, "xx", "Uz2", "", "Ру2"))
            row = (
                await s.execute(
                    select(EducationLanguageRow).where(EducationLanguageRow.id == again)
                )
            ).scalar_one()
            assert again == lang_id
            assert (row.name_en, row.name_uz, row.name_ru) == ("English", "Uz2", "Ру2")
            changed = await sink.upsert_language(SourceLanguage(ext, "xx", "Uz2", "Eng2", "Ру2"))
            await s.refresh(row)
            assert changed == lang_id and row.name_en == "Eng2"
            await tx.rollback()
    finally:
        await engine.dispose()
