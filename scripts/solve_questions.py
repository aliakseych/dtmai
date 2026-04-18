"""
Main pipeline: extract questions from images and insert into MongoDB.

Usage:
    # Single mock folder:
    python -m scripts.solve_questions data/math/mock1

    # All mocks for one subject:
    python -m scripts.solve_questions data/math

    # All subjects at once:
    python -m scripts.solve_questions data

    # Multiple explicit paths:
    python -m scripts.solve_questions data/math/mock1 data/english/mock5

    # Flags (work with any of the above):
    python -m scripts.solve_questions data --dry-run
    python -m scripts.solve_questions data --concurrency 8
"""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.questions import QuestionRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.services.ai_service import AIService
from src.services.category_service import CategoryService
from src.services.question_service import DEFAULT_CONCURRENCY, FOLDER_SUBJECT_MAP, QuestionService
from src.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _collect_mock_folders(target: Path) -> list[Path]:
    """
    Resolves a target path to a flat list of mock folders (folders containing images).

    data/math/mock1   → [data/math/mock1]          (direct mock folder)
    data/math         → [data/math/mock1, ...]      (subject folder)
    data              → [data/math/mock1, ...,      (root data folder)
                         data/english/mock5, ...]
    """
    if not target.exists():
        logger.error("Path does not exist: %s", target)
        sys.exit(1)

    # Mock folder: contains images directly
    if any(p.suffix.lower() in IMAGE_EXTS for p in target.iterdir()):
        return [target]

    subdirs = sorted(p for p in target.iterdir() if p.is_dir())
    if not subdirs:
        logger.error("No subfolders found in %s", target)
        sys.exit(1)

    # Root data folder: subdirs are known subject names (math, english, ...)
    if all(d.name.lower() in FOLDER_SUBJECT_MAP for d in subdirs):
        mock_folders = []
        for subject_dir in subdirs:
            mock_folders.extend(_collect_mock_folders(subject_dir))
        return mock_folders

    # Subject folder: subdirs are mock folders
    return subdirs


async def main(targets: list[Path], dry_run: bool, concurrency: int) -> None:
    mongo = MongoClient(settings.MONGO_URI, settings.MONGO_DB_NAME)

    question_service = QuestionService(
        ai_service=AIService(),
        category_service=CategoryService(CategoryRepository(mongo)),
        question_repo=QuestionRepository(mongo),
        source_repo=SourceRepository(mongo),
    )

    mock_folders: list[Path] = []
    for target in targets:
        mock_folders.extend(_collect_mock_folders(target))

    if not mock_folders:
        logger.error("No mock folders resolved from provided paths.")
        sys.exit(1)

    subjects = {f.parent.name.lower() for f in mock_folders}
    logger.info(
        "Found %d mock folder(s) across subject(s): %s",
        len(mock_folders), ", ".join(sorted(subjects)),
    )

    total = {"added": 0, "skipped_dupe": 0, "skipped_error": 0, "new_categories": 0}

    for folder in mock_folders:
        logger.info("── %s ──", folder)
        stats = await question_service.process_folder(folder, dry_run=dry_run, concurrency=concurrency)
        logger.info(
            "   added=%d  dupes=%d  errors=%d  new_categories=%d",
            stats["added"], stats["skipped_dupe"], stats["skipped_error"], stats["new_categories"],
        )
        for k in total:
            total[k] += stats[k]

    print("\n" + "=" * 50)
    print(f"{'[DRY RUN] ' if dry_run else ''}TOTAL SUMMARY")
    print(f"  Questions added:      {total['added']}")
    print(f"  Duplicates skipped:   {total['skipped_dupe']}")
    print(f"  Errors skipped:       {total['skipped_error']}")
    print(f"  New categories added: {total['new_categories']}")
    print("=" * 50)


if __name__ == "__main__":
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    path_args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not path_args:
        print("Usage: python -m scripts.solve_questions <path> [<path> ...] [--dry-run] [--concurrency N]")
        print(f"  Subjects: {list(FOLDER_SUBJECT_MAP.keys())}")
        sys.exit(1)

    dry_run = "--dry-run" in flags

    concurrency = DEFAULT_CONCURRENCY
    for i, flag in enumerate(flags):
        if flag.startswith("--concurrency="):
            concurrency = int(flag.split("=", 1)[1])
        elif flag == "--concurrency" and i + 1 < len(flags):
            concurrency = int(flags[i + 1])

    asyncio.run(main([Path(p) for p in path_args], dry_run=dry_run, concurrency=concurrency))
