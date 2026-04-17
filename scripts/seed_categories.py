"""
Seed initial categories into MongoDB from data/categories.json.
Safe to run multiple times — skips already-existing categories.

Usage:
    python -m scripts.seed_categories
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

from uuid6 import uuid7

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.settings import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent.parent / "data" / "categories.json"


async def main():
    client = MongoClient(settings.MONGO_URI, settings.DB_NAME)
    repo = CategoryRepository(client)

    seed_data = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    added = 0
    skipped = 0

    for entry in seed_data:
        existing = await repo.get_by_name(entry["name"])
        if existing:
            skipped += 1
            continue

        await repo.create({
            "_id": str(uuid7()),
            "subject": entry["subject"],
            "name": entry["name"],
        })
        added += 1
        logger.info("  + %s (%s)", entry["name"], entry["subject"])

    logger.info("\nDone. Added: %d, Skipped (already exist): %d", added, skipped)


if __name__ == "__main__":
    asyncio.run(main())
