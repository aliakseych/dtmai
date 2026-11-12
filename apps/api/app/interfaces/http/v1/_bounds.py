"""Request-size guards for free-form JSON responses."""

import json
from typing import Any

MAX_RESPONSE_BYTES = 4096


def check_response_size(value: dict[str, Any]) -> dict[str, Any]:
    """Pydantic validator body: reject responses whose serialized form exceeds the cap."""
    size = len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())
    if size > MAX_RESPONSE_BYTES:
        raise ValueError(f"response exceeds {MAX_RESPONSE_BYTES} bytes")
    return value
