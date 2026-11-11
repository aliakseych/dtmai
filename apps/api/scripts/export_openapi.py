"""Write the FastAPI OpenAPI schema to apps/api/openapi/openapi.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bootstrap.http import create_app  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "openapi" / "openapi.json"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    schema = create_app().openapi()
    OUT.write_text(json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {OUT}")
