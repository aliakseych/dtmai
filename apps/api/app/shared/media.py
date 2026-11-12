import asyncio
from pathlib import Path
from typing import Protocol

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.settings import get_settings


class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    media_local_dir: str = "./.media"
    media_max_bytes: int = 10 * 1024 * 1024


_SIGNATURES: tuple[tuple[bytes, str, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"GIF87a", "image/gif", ".gif"),
    (b"GIF89a", "image/gif", ".gif"),
    (b"%PDF-", "application/pdf", ".pdf"),
)


def sniff_media(data: bytes) -> tuple[str, str] | None:
    """(content type, extension) from the file's magic bytes; None when not an allowed type.

    The client-declared type is never trusted: stored objects are served with the sniffed one.
    """
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", ".webp"
    for magic, mime, ext in _SIGNATURES:
        if data.startswith(magic):
            return mime, ext
    return None


class MediaStore(Protocol):
    async def put(self, key: str, data: bytes, mime: str) -> None: ...


class LocalMediaStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    async def put(self, key: str, data: bytes, mime: str) -> None:
        path = (self._root / key).resolve()
        if self._root.resolve() not in path.parents:
            raise ValueError("invalid media key")

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(write)


class S3MediaStore:
    def __init__(self) -> None:
        import boto3

        s = get_settings()
        self._bucket = s.s3_bucket
        self._c = boto3.client(
            "s3",
            endpoint_url=s.s3_endpoint,
            aws_access_key_id=s.s3_access_key,
            aws_secret_access_key=s.s3_secret_key,
        )

    async def put(self, key: str, data: bytes, mime: str) -> None:
        extra = {"ContentDisposition": "attachment"} if mime == "application/pdf" else {}
        await asyncio.to_thread(
            self._c.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=mime,
            **extra,
        )


def build_media_store() -> MediaStore:
    """S3 when credentials are configured, otherwise a local directory (dev)."""
    if get_settings().s3_access_key:
        return S3MediaStore()
    return LocalMediaStore(Path(MediaSettings().media_local_dir))
