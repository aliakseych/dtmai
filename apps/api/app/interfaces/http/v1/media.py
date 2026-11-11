import mimetypes
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from app.shared.audit import audit_admin
from app.shared.deps import require_role
from app.shared.errors import ProblemDetails, ValidationFailed
from app.shared.media import MediaSettings, build_media_store
from app.shared.security import Principal

admin_router = APIRouter(tags=["media-admin"])
Admin = Annotated[Principal, Depends(require_role("admin"))]

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}
ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/svg+xml", "audio/mpeg", "application/pdf"}


class MediaOut(BaseModel):
    key: str


@admin_router.post("", operation_id="media_admin_upload", responses=ERR)
async def upload(file: UploadFile, who: Admin) -> MediaOut:
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in ALLOWED:
        raise ValidationFailed(f"unsupported media type: {mime or 'unknown'}", code="unsupported_media")
    limit = MediaSettings().media_max_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise ValidationFailed("file too large", code="file_too_large")
    ext = mimetypes.guess_extension(mime) or ""
    key = f"media/{uuid4().hex}{ext}"
    await build_media_store().put(key, data, mime)
    audit_admin(who, "media.upload", key=key, size=len(data), mime=mime)
    return MediaOut(key=key)
