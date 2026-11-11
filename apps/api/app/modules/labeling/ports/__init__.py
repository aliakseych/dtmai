from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Page:
    """One extractable unit: a rendered image and/or text (docx paragraphs)."""

    number: int
    image: bytes | None
    mime: str = "image/png"
    text: str | None = None


class FileStore(Protocol):
    """Where import material lives (local directory or S3 prefix)."""

    async def list(self, root: str) -> list[str]: ...
    async def read(self, path: str) -> bytes: ...
    async def put_public(self, key: str, data: bytes, mime: str) -> str | None:
        """Store derived media (page figures); returns the stored key or None when unsupported."""
        ...


class PageRenderer(Protocol):
    def pages(self, filename: str, data: bytes) -> list[Page]: ...
