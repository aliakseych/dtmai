import base64
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.application.gateway import AIGateway
from app.modules.ai.domain.routing import Task
from app.modules.ai.ports import LLMMessage
from app.modules.bank import facade as bank
from app.modules.labeling.application.prompts import extract_system
from app.modules.labeling.domain.extraction import (
    ExtractedQuestion,
    PageExtraction,
    answer_from_key,
    parse_page,
    pick_topic,
    placeholder_answer,
    resolve_keys,
)
from app.modules.labeling.domain.stale import ACTIVE_STATUSES, STALE_AFTER, is_abandoned
from app.modules.labeling.infrastructure import catalog_adapter
from app.modules.labeling.infrastructure.files import DefaultRenderer, crop_png, store_for
from app.modules.labeling.infrastructure.orm import ImportBatchRow, ImportFileRow
from app.modules.labeling.ports import FileStore, Page, PageRenderer
from app.shared.errors import Conflict, DomainError, NotFound, ValidationFailed
from app.shared.ids import new_id

log = logging.getLogger(__name__)

ACTOR = "labeling:ingest"


class IngestService:
    def __init__(
        self,
        session: AsyncSession,
        gateway: AIGateway,
        *,
        renderer: PageRenderer | None = None,
        store: FileStore | None = None,
    ) -> None:
        self._s = session
        self._gw = gateway
        self._renderer = renderer or DefaultRenderer()
        self._store = store

    # ---- batch lifecycle ---------------------------------------------------------------------
    async def create_batch(
        self,
        *,
        root: str,
        source_code: str,
        source_name: str | None,
        source_year: int | None,
        subject_id: UUID,
        language: str,
        base: str | None,
        has_answer_key: bool,
        topic_id: UUID | None,
        type_ids: dict[str, UUID] | None,
        created_by: UUID | None,
    ) -> ImportBatchRow:
        store = self._store or store_for(root)
        paths = await store.list(root)
        if not paths:
            raise ValidationFailed(f"no importable files under {root}", code="no_files")
        topic = topic_id or await catalog_adapter.first_topic(self._s, subject_id)
        if topic is None:
            raise ValidationFailed(
                "topic_id required (no topics found for subject)", code="topic_required"
            )
        types = {
            **{k: str(v) for k, v in (await catalog_adapter.find_type_ids(self._s)).items()},
            **{k: str(v) for k, v in (type_ids or {}).items()},
        }
        batch = ImportBatchRow(
            id=new_id(),
            source_code=source_code,
            source_name=source_name,
            source_year=source_year,
            subject_id=subject_id,
            language=language,
            base=base,
            has_answer_key=has_answer_key,
            root=root,
            topic_id=topic,
            type_ids=types,
            status="pending",
            files_total=len(paths),
            created_by=created_by,
        )
        self._s.add(batch)
        await self._s.flush()
        for p in paths:
            self._s.add(
                ImportFileRow(
                    id=new_id(), batch_id=batch.id, path=p, status="pending", question_ids=[]
                )
            )
        await self._s.flush()
        return batch

    async def fail_abandoned(self) -> None:
        """Fail pending/running batches whose worker was lost so they never look live."""
        await self._s.execute(
            update(ImportBatchRow)
            .where(
                ImportBatchRow.status.in_(ACTIVE_STATUSES),
                ImportBatchRow.created_at < datetime.now(UTC) - STALE_AFTER,
            )
            .values(status="failed", error="abandoned (worker lost)", finished_at=datetime.now(UTC))
        )
        await self._s.flush()

    async def reset_for_rerun(self, batch_id: UUID, *, all_files: bool) -> ImportBatchRow:
        batch = await self._require(batch_id)
        if batch.status == "running" and is_abandoned(
            batch.status, batch.created_at, datetime.now(UTC)
        ):
            batch.status = "failed"
        if batch.status == "running":
            raise Conflict("Batch is already running", code="batch_running")
        files = (
            await self._s.execute(select(ImportFileRow).where(ImportFileRow.batch_id == batch_id))
        ).scalars()
        for f in files:
            if f.status == "failed" or (all_files and not f.question_ids):
                f.status = "pending"
                f.error = None
        batch.status = "pending"
        batch.error = None
        batch.created_at = datetime.now(UTC)  # restart the abandonment clock
        await self._s.flush()
        return batch

    async def _require(self, batch_id: UUID) -> ImportBatchRow:
        batch = await self._s.get(ImportBatchRow, batch_id)
        if batch is None:
            raise NotFound("Import batch not found")
        return batch

    # ---- execution ----------------------------------------------------------------------------
    async def run(self, batch_id: UUID) -> list[UUID]:
        """Phase 1 extract every pending file; phase 2 create drafts. Returns new question ids."""
        batch = await self._require(batch_id)
        batch.status = "running"
        await self._s.commit()
        store = self._store or store_for(batch.root)
        files = list(
            (
                await self._s.execute(
                    select(ImportFileRow)
                    .where(ImportFileRow.batch_id == batch_id)
                    .order_by(ImportFileRow.path)
                )
            ).scalars()
        )
        route = (await self._gw.routes(Task.EXTRACT))[0]
        system = extract_system(
            [label for _, label in await catalog_adapter.ordered_topics(self._s, batch.subject_id)]
        )
        for f in files:
            if f.status == "pending":
                await self._extract_file(batch, f, store, route, system)
                await self._s.commit()
        created = await self._assemble(batch, files, store)
        failed = [f for f in files if f.status == "failed"]
        batch.files_done = sum(1 for f in files if f.status == "done")
        batch.questions_created += len(created)
        batch.status = "failed" if failed and not batch.files_done else "done"
        if failed:
            batch.error = f"{len(failed)} file(s) failed; re-run to retry"
        batch.finished_at = datetime.now(UTC)
        await self._s.commit()
        return created

    async def _extract_file(
        self, batch: ImportBatchRow, f: ImportFileRow, store: FileStore, route: Any, system: str
    ) -> None:
        try:
            data = await store.read(f.path)
            pages = self._renderer.pages(Path(f.path).name, data)
            out: list[dict[str, Any]] = []
            for pg in pages:
                parsed, _ = await self._gw.complete_json(
                    route,
                    [LLMMessage("system", system), LLMMessage("user", _content(pg))],
                    purpose="ingestion.extract",
                    ref=f"{f.id}:{pg.number}",
                )
                out.append({"page": pg.number, "data": parsed})
            f.extracted = {"pages": out}
            f.status = "extracted"
        except DomainError as e:
            if e.code in ("ai_budget_exhausted", "ai_unavailable"):
                raise
            f.status, f.error = "failed", e.detail[:500]
        except Exception as e:  # noqa: BLE001 - bad file must not abort the batch
            log.exception("extract failed for %s", f.path)
            f.status, f.error = "failed", f"{type(e).__name__}: {e}"[:500]

    async def _assemble(
        self, batch: ImportBatchRow, files: list[ImportFileRow], store: FileStore
    ) -> list[UUID]:
        ready = [f for f in files if f.status == "extracted"]
        if not ready:
            return []
        parsed: dict[UUID, list[tuple[int, PageExtraction]]] = {
            f.id: [(p["page"], parse_page(p["data"])) for p in (f.extracted or {}).get("pages", [])]
            for f in ready
        }
        source_id = await catalog_adapter.get_or_create_source(
            self._s,
            code=batch.source_code,
            name=batch.source_name or batch.source_code,
            year=batch.source_year,
        )
        topic_ids = [
            tid for tid, _ in await catalog_adapter.ordered_topics(self._s, batch.subject_id)
        ]
        created: list[UUID] = []
        for f in ready:
            ids: list[UUID] = []
            passage_ids: dict[str, UUID] = {}
            # answer keys are scoped to the file and its sections (numbering restarts per chapter)
            keys = resolve_keys([ex for _, ex in parsed[f.id]]) if batch.has_answer_key else {}
            try:
                async with self._s.begin_nested():
                    for pi, (page_no, ex) in enumerate(parsed[f.id]):
                        for p in ex.passages:
                            passage_ids[p.key] = await bank.create_passage(
                                self._s,
                                language=batch.language,
                                text=p.text,
                                title=p.title,
                                source_id=source_id,
                            )
                        for qi, q in enumerate(ex.questions):
                            qid = await self._create_question(
                                batch,
                                f,
                                source_id,
                                page_no,
                                qi,
                                q,
                                keys.get((pi, qi)),
                                passage_ids,
                                store,
                                topic_ids,
                            )
                            if qid is not None:
                                ids.append(qid)
                f.question_ids = [str(i) for i in ids]
                f.status = "done"
                f.processed_at = datetime.now(UTC)
                created.extend(ids)
            except DomainError as e:
                f.status, f.error = "failed", e.detail[:500]
        await self._s.flush()
        return created

    async def _create_question(
        self,
        batch: ImportBatchRow,
        f: ImportFileRow,
        source_id: UUID,
        page_no: int,
        idx: int,
        q: ExtractedQuestion,
        key_raw: str | None,
        passage_ids: dict[str, UUID],
        store: FileStore,
        topic_ids: list[UUID],
    ) -> UUID | None:
        type_id = (batch.type_ids or {}).get(q.kind)
        if type_id is None or batch.topic_id is None:
            log.warning("no question type for kind %s in batch %s; skipping", q.kind, batch.id)
            return None
        official: dict[str, Any] | None = None
        answer_source: str | None = None
        if q.answer_raw:
            official = answer_from_key(q.kind, q.answer_raw, len(q.options))
            answer_source = "inline" if official else None
        if official is None and key_raw is not None:
            official = answer_from_key(q.kind, key_raw, len(q.options))
            answer_source = "key" if official else None
        answer = official or placeholder_answer(q.kind, q.options)
        media: list[Any] = []
        if q.has_figure:
            image = await self._page_image(f, page_no, store)
            media_key = await store.put_public(
                f"ingest/{batch.id}/{f.id}-p{page_no}-q{idx}.png",
                crop_png(image, q.bbox) or image,
                "image/png",
            )
            if media_key:
                media.append({"type": "image", "key": media_key})
        cmd = bank.CreateQuestionCmd(
            subject_id=batch.subject_id,
            topic_id=pick_topic(q.topic, topic_ids, batch.topic_id),
            type_id=UUID(type_id),
            kind=q.kind,
            language=batch.language,
            stem=q.stem,
            payload={"options": q.options} if q.options else {},
            answer=answer,
            media=media,
            passage_id=passage_ids.get(q.passage_key) if q.passage_key else None,
            source_id=source_id,
            source_ref={
                "batch": str(batch.id),
                "file": f.path,
                "page": page_no,
                "number": q.number,
                "base": batch.base,
                "has_figure": q.has_figure,
                "answer_placeholder": official is None,
                "answer_source": answer_source,
                "options_generated": q.options_generated,
            },
            status="draft",
            answer_official=official is not None,
            created_by=ACTOR,
        )
        return await bank.create_question(self._s, cmd)

    async def _page_image(self, f: ImportFileRow, page_no: int, store: FileStore) -> bytes:
        pages = self._renderer.pages(Path(f.path).name, await store.read(f.path))
        pg = next((p for p in pages if p.number == page_no and p.image), None)
        if pg is None or pg.image is None:
            raise ValidationFailed("page image unavailable")
        return pg.image


def _content(pg: Page) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = [
        {"type": "text", "text": "Extract all questions from this page."}
    ]
    if pg.text:
        parts.append({"type": "text", "text": f"TEXT LAYER:\n{pg.text}"})
    if pg.image:
        b64 = base64.b64encode(pg.image).decode()
        parts.append({"type": "image_url", "image_url": {"url": f"data:{pg.mime};base64,{b64}"}})
    return parts
