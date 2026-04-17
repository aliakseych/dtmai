"""
Dry-run: detect what categories Gemini would assign to images, without writing to DB.
Prints a table of image → proposed category → match/new.

Usage:
    python -m scripts.detect_categories data/math/mock1
    python -m scripts.detect_categories data/english/mock5
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces.ai.subjects import get_config
from src.services.question_service import FOLDER_SUBJECT_MAP
from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.services.ai_service import AIService
from src.settings import settings

logging.basicConfig(level=logging.WARNING, format="%(message)s")


async def main(folder: Path):
    subject_name = folder.parent.name.lower()
    subject = FOLDER_SUBJECT_MAP.get(subject_name)
    if subject is None:
        print(f"Unknown subject folder: '{subject_name}'. Known: {list(FOLDER_SUBJECT_MAP.keys())}")
        sys.exit(1)

    config = get_config(subject)

    client = MongoClient(settings.MONGO_URI, settings.DB_NAME)
    repo = CategoryRepository(client)
    ai = AIService()

    existing = await repo.get_by_subject(subject.value)
    existing_names = {c["name"].strip().lower(): c["name"] for c in existing}

    images = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    )

    print(f"\n{'Image':<35} {'Proposed category':<40} {'Status'}")
    print("-" * 85)

    for image_path in images:
        result = await ai.extract_question(image_path, config, list(existing_names.values()))
        if result is None:
            print(f"{image_path.name:<35} {'[AI ERROR]':<40} ERROR")
            continue

        normalized = result.category.strip().lower()
        status = "MATCH" if normalized in existing_names else "NEW"
        print(f"{image_path.name:<35} {result.category:<40} {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.detect_categories <folder>")
        sys.exit(1)
    asyncio.run(main(Path(sys.argv[1])))
