from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile
from pydantic import BaseModel

from app.shared.audit import audit_admin
from app.shared.deps import require_role
from app.shared.errors import ProblemDetails, ValidationFailed
from app.shared.media import MediaSettings, build_media_store, sniff_media
from app.shared.security import Principal

admin_router = APIRouter(tags=["media-admin"])
Admin = Annotated[Principal, Depends(require_role("admin"))]

ERR: dict[int | str, dict[str, Any]] = {
    401: {"model": ProblemDetails, "description": "Unauthorized"},
    403: {"model": ProblemDetails, "description": "Forbidden"},
    422: {"model": ProblemDetails, "description": "Validation failed"},
}


class MediaOut(BaseModel):
    key: str


@admin_router.post("", operation_id="media_admin_upload", responses=ERR)
async def upload(file: UploadFile, who: Admin) -> MediaOut:
    limit = MediaSettings().media_max_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise ValidationFailed("file too large", code="file_too_large")
    sniffed = sniff_media(data)
    if sniffed is None:
        raise ValidationFailed("unsupported media type", code="unsupported_media")
    mime, ext = sniffed
    declared = file.content_type or ""
    if declared and declared != "application/octet-stream" and declared != mime:
        raise ValidationFailed(
            f"declared type {declared} does not match file content ({mime})",
            code="media_type_mismatch",
        )
    key = f"media/{uuid4().hex}{ext}"
    await build_media_store().put(key, data, mime)
    audit_admin(who, "media.upload", key=key, size=len(data), mime=mime)
    return MediaOut(key=key)
