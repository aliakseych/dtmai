from typing import Any, Literal

from pydantic import BaseModel

_KINDS = {"image": "image", "image_url": "image", "audio": "audio"}


class MediaOut(BaseModel):
    kind: Literal["image", "audio"]
    url: str
    alt: str | None = None


def to_media(raw: list[Any] | None) -> list[MediaOut]:
    """Normalise stored media entries ({kind|type, url|key, alt}) to the public shape; skip unknown ones."""
    out: list[MediaOut] = []
    for m in raw or []:
        if not isinstance(m, dict):
            continue
        kind = _KINDS.get(str(m.get("kind") or m.get("type") or ""))
        url = m.get("url") or m.get("key")
        if kind is None and isinstance(m.get("image_url"), dict):
            kind, url = "image", m["image_url"].get("url")
        if kind and isinstance(url, str) and url:
            alt = m.get("alt")
            out.append(MediaOut(kind=kind, url=url, alt=alt if isinstance(alt, str) else None))  # type: ignore[arg-type]
    return out
