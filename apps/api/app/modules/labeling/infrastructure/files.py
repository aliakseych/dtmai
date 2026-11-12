import asyncio
import io
import mimetypes
import re
from pathlib import Path
from typing import Any

from app.modules.labeling.ports import Page
from app.settings import get_settings

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_EXT = IMAGE_EXT | {".pdf", ".docx"}


def natural_key(s: str) -> list[Any]:
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def crop_png(image: bytes, bbox: list[int] | None) -> bytes | None:
    """Crop a PNG to a 0..1000-normalized bbox (padded); None when bbox is unusable or cropping fails."""
    from app.modules.labeling.domain.extraction import crop_box

    try:
        import pymupdf

        src = pymupdf.Pixmap(image)
        box = crop_box(bbox, src.width, src.height)
        if box is None:
            return None
        rect = pymupdf.IRect(*box)
        dst = pymupdf.Pixmap(src.colorspace, rect, src.alpha)
        dst.copy(src, rect)
        return bytes(dst.tobytes("png"))
    except Exception:  # noqa: BLE001 - fall back to the whole page
        return None


class LocalFileStore:
    """Reads sources from disk; figure media goes to the public S3 bucket when one is configured."""

    def __init__(self, public: "S3FileStore | None" = None) -> None:
        self._public = public

    async def list(self, root: str) -> list[str]:
        p = Path(root)
        if p.is_file():
            return [str(p)]
        files = [str(f) for f in p.rglob("*") if f.is_file() and f.suffix.lower() in SUPPORTED_EXT]
        return sorted(files, key=natural_key)

    async def read(self, path: str) -> bytes:
        return await asyncio.to_thread(Path(path).read_bytes)

    async def put_public(self, key: str, data: bytes, mime: str) -> str | None:
        return await self._public.put_public(key, data, mime) if self._public else None

    async def put(self, root: str, name: str, data: bytes, mime: str) -> None:
        base = Path(root).resolve()
        path = (base / name).resolve()
        if base not in path.parents:
            raise ValueError("invalid upload name")

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

        await asyncio.to_thread(write)


class S3FileStore:
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

    @staticmethod
    def split(uri: str) -> tuple[str, str]:
        rest = uri.removeprefix("s3://")
        bucket, _, prefix = rest.partition("/")
        return bucket, prefix

    async def list(self, root: str) -> list[str]:
        bucket, prefix = self.split(root)

        def run() -> list[str]:
            out: list[str] = []
            for page in self._c.get_paginator("list_objects_v2").paginate(
                Bucket=bucket, Prefix=prefix
            ):
                for o in page.get("Contents", []):
                    if Path(o["Key"]).suffix.lower() in SUPPORTED_EXT:
                        out.append(f"s3://{bucket}/{o['Key']}")
            return out

        return sorted(await asyncio.to_thread(run), key=natural_key)

    async def read(self, path: str) -> bytes:
        bucket, key = self.split(path)
        obj = await asyncio.to_thread(self._c.get_object, Bucket=bucket, Key=key)
        return await asyncio.to_thread(obj["Body"].read)

    async def put_public(self, key: str, data: bytes, mime: str) -> str | None:
        await asyncio.to_thread(
            self._c.put_object, Bucket=self._bucket, Key=key, Body=data, ContentType=mime
        )
        return key

    async def put(self, root: str, name: str, data: bytes, mime: str) -> None:
        bucket, prefix = self.split(root)
        key = f"{prefix.rstrip('/')}/{name}"
        await asyncio.to_thread(
            self._c.put_object, Bucket=bucket, Key=key, Body=data, ContentType=mime
        )


def store_for(root: str) -> LocalFileStore | S3FileStore:
    if root.startswith("s3://"):
        return S3FileStore()
    return LocalFileStore(S3FileStore() if get_settings().s3_access_key else None)


def upload_root(batch_uuid: str) -> str:
    """Root for uploaded files: s3://bucket/uploads/<uuid> when S3 is configured, else a local dir."""
    s = get_settings()
    if s.s3_access_key:
        return f"s3://{s.s3_bucket}/uploads/{batch_uuid}"
    from app.modules.labeling.infrastructure.config import get_labeling_settings

    return str(
        (Path(get_labeling_settings().labeling_upload_dir) / "uploads" / batch_uuid).resolve()
    )


class DefaultRenderer:
    """Images pass through; PDFs render per page (PyMuPDF); docx yields text + embedded images."""

    def pages(self, filename: str, data: bytes) -> list[Page]:
        ext = Path(filename).suffix.lower()
        if ext in IMAGE_EXT:
            return [Page(1, data, mimetypes.guess_type(filename)[0] or "image/png")]
        if ext == ".pdf":
            return self._pdf(data)
        if ext == ".docx":
            return self._docx(data)
        raise ValueError(f"unsupported file type: {ext}")

    @staticmethod
    def _pdf(data: bytes) -> list[Page]:
        try:
            import pymupdf
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("PDF ingestion needs the 'pymupdf' package") from e
        doc = pymupdf.open(stream=data, filetype="pdf")
        out = []
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=150)
            out.append(Page(i, pix.tobytes("png"), "image/png", page.get_text() or None))
        return out

    @staticmethod
    def _docx(data: bytes) -> list[Page]:
        try:
            import docx
        except ImportError as e:  # pragma: no cover
            raise RuntimeError("docx ingestion needs the 'python-docx' package") from e
        d = docx.Document(io.BytesIO(data))
        text = "\n".join(p.text for p in d.paragraphs if p.text.strip())
        pages = [Page(1, None, "image/png", text)] if text else []
        for i, rel in enumerate(
            (r for r in d.part.rels.values() if "image" in r.reltype), start=len(pages) + 1
        ):
            pages.append(Page(i, rel.target_part.blob, rel.target_part.content_type))
        return pages
