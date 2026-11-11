import re
from pathlib import PurePosixPath
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.labeling.infrastructure.files import store_for, upload_root
from app.modules.labeling.infrastructure.orm import ImportBatchRow, ImportFileRow
from app.modules.labeling.wiring import IngestDep
from app.shared.db import get_session
from app.shared.deps import require_role
from app.shared.errors import NotFound, ProblemDetails, ValidationFailed
from app.shared.security import Principal

admin_router = APIRouter(tags=["ingestion-admin"])

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    404: {"model": ProblemDetails, "description": "Not found"},
    409: {"model": ProblemDetails, "description": "Conflict"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}
SessionDep = Annotated[AsyncSession, Depends(get_session)]
Admin = Annotated[Principal, Depends(require_role("admin"))]


class BatchIn(BaseModel):
    root: str = Field(max_length=500, description="Server-side path or s3://bucket/prefix")
    source_code: str = Field(max_length=80)
    source_name: str | None = None
    source_year: int | None = None
    subject_id: UUID
    language: str = Field(max_length=10)
    base: str | None = None
    has_answer_key: bool = False
    topic_id: UUID | None = None
    type_ids: dict[str, UUID] | None = Field(None, description="question kind -> question type id")


class FileOut(BaseModel):
    id: UUID
    path: str
    status: str
    questions: int
    error: str | None


class BatchOut(BaseModel):
    id: UUID
    source_code: str
    subject_id: UUID
    language: str
    status: str
    files_total: int
    files_done: int
    questions_created: int
    error: str | None


class BatchDetail(BatchOut):
    files: list[FileOut]


class RerunIn(BaseModel):
    include_unfinished: bool = Field(False, description="Also retry files that produced no questions")


def _batch(b: ImportBatchRow) -> BatchOut:
    return BatchOut(
        id=b.id, source_code=b.source_code, subject_id=b.subject_id, language=b.language, status=b.status,
        files_total=b.files_total, files_done=b.files_done, questions_created=b.questions_created, error=b.error,
    )


@admin_router.post("/batches", operation_id="ingestion_create_batch", response_model=BatchOut, status_code=202,
                   responses=ERR)
async def create_batch(body: BatchIn, svc: IngestDep, session: SessionDep, who: Admin) -> BatchOut:
    from app.modules.labeling.tasks import run_import

    batch = await svc.create_batch(
        root=body.root, source_code=body.source_code, source_name=body.source_name, source_year=body.source_year,
        subject_id=body.subject_id, language=body.language, base=body.base, has_answer_key=body.has_answer_key,
        topic_id=body.topic_id, type_ids=body.type_ids, created_by=who.user_id,
    )
    await session.commit()
    await run_import.kiq(str(batch.id))
    return _batch(batch)


UPLOAD_MIME = {
    "application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
UPLOAD_MAX_FILES = 50
UPLOAD_MAX_BYTES = 100 * 1024 * 1024


@admin_router.post("/batches/upload", operation_id="ingestion_upload_batch", response_model=BatchOut,
                   status_code=202, responses=ERR)
async def upload_batch(
    svc: IngestDep, session: SessionDep, who: Admin,
    files: Annotated[list[UploadFile], File(description="PDF/PNG/JPEG/WebP, max 50 files, 25 MB each")],
    source_code: Annotated[str, Form(max_length=80)],
    subject_id: Annotated[UUID, Form()],
    language: Annotated[Literal["uz", "ru"], Form()],
    source_name: Annotated[str | None, Form()] = None,
    source_year: Annotated[int | None, Form()] = None,
    base: Annotated[str | None, Form()] = None,
    has_answer_key: Annotated[bool, Form()] = False,
    topic_id: Annotated[UUID | None, Form()] = None,
) -> BatchOut:
    from app.modules.labeling.tasks import run_import

    if not files:
        raise ValidationFailed("No files uploaded")
    if len(files) > UPLOAD_MAX_FILES:
        raise ValidationFailed(f"At most {UPLOAD_MAX_FILES} files per upload")
    blobs: list[tuple[str, bytes, str]] = []
    for i, f in enumerate(files, 1):
        mime = (f.content_type or "").split(";")[0].strip().lower()
        if mime not in UPLOAD_MIME:
            raise ValidationFailed(f"Unsupported file type for {f.filename!r}: {mime or 'unknown'}")
        data = await f.read(UPLOAD_MAX_BYTES + 1)
        if len(data) > UPLOAD_MAX_BYTES:
            raise ValidationFailed(f"{f.filename!r} exceeds 25 MB")
        stem = re.sub(r"[^\w.-]+", "_", PurePosixPath((f.filename or "file").replace("\\", "/")).stem)[:80] or "file"
        blobs.append((f"{i:03d}_{stem}{UPLOAD_MIME[mime]}", data, mime))

    batch_uuid = uuid4().hex
    root = upload_root(batch_uuid)
    store = store_for(root)
    for name, data, mime in blobs:
        await store.put(root, name, data, mime)
    batch = await svc.create_batch(
        root=root, source_code=source_code, source_name=source_name, source_year=source_year,
        subject_id=subject_id, language=language, base=base, has_answer_key=has_answer_key,
        topic_id=topic_id, type_ids=None, created_by=who.user_id,
    )
    await session.commit()
    await run_import.kiq(str(batch.id))
    return _batch(batch)


@admin_router.get("/batches", operation_id="ingestion_list_batches", response_model=list[BatchOut], responses=ERR)
async def list_batches(session: SessionDep, _: Admin, limit: int = Query(50, ge=1, le=200)) -> list[BatchOut]:
    rows = (
        await session.execute(select(ImportBatchRow).order_by(ImportBatchRow.created_at.desc()).limit(limit))
    ).scalars()
    return [_batch(b) for b in rows]


@admin_router.get("/batches/{batch_id}", operation_id="ingestion_get_batch", response_model=BatchDetail, responses=ERR)
async def get_batch(batch_id: UUID, session: SessionDep, _: Admin) -> BatchDetail:
    b = await session.get(ImportBatchRow, batch_id)
    if b is None:
        raise NotFound("Import batch not found")
    files = (
        await session.execute(select(ImportFileRow).where(ImportFileRow.batch_id == batch_id).order_by(ImportFileRow.path))
    ).scalars()
    return BatchDetail(
        **_batch(b).model_dump(),
        files=[FileOut(id=f.id, path=f.path, status=f.status, questions=len(f.question_ids or []), error=f.error) for f in files],
    )


@admin_router.post("/batches/{batch_id}/rerun", operation_id="ingestion_rerun_batch", response_model=BatchOut,
                   status_code=202, responses=ERR)
async def rerun_batch(batch_id: UUID, body: RerunIn, svc: IngestDep, session: SessionDep, _: Admin) -> BatchOut:
    from app.modules.labeling.tasks import run_import

    batch = await svc.reset_for_rerun(batch_id, all_files=body.include_unfinished)
    await session.commit()
    await run_import.kiq(str(batch.id))
    return _batch(batch)
