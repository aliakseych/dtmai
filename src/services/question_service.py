import asyncio
import hashlib
import logging
from pathlib import Path

from uuid6 import uuid7

from src.interfaces.ai.subjects import get_config
from src.interfaces.mongodb.repositories.questions import QuestionRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.models.questions.subject import Subject
from src.services.ai_service import AIService
from src.services.category_service import CategoryService

logger = logging.getLogger(__name__)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# Maps data folder names to Subject enum values.
# Add new subjects here when new data folders are introduced.
FOLDER_SUBJECT_MAP: dict[str, Subject] = {
    "math": Subject.MATH,
    "english": Subject.ENGLISH,
}

DEFAULT_CONCURRENCY = 5


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class QuestionService:
    """Orchestrates the full image → DB pipeline for a batch of images."""

    def __init__(
        self,
        ai_service: AIService,
        category_service: CategoryService,
        question_repo: QuestionRepository,
        source_repo: SourceRepository,
    ):
        self._ai = ai_service
        self._categories = category_service
        self._questions = question_repo
        self._sources = source_repo

    async def process_folder(
        self,
        folder: Path,
        dry_run: bool = False,
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> dict:
        """
        Processes all images concurrently. Each image is extracted and inserted
        to DB as soon as its AI response arrives — no waiting for the whole batch.

        A semaphore caps concurrent AI calls; a lock serialises category-resolve
        and DB writes to prevent duplicate category creation.
        """
        subject_name = folder.parent.name.lower()
        subject = FOLDER_SUBJECT_MAP.get(subject_name)
        if subject is None:
            raise ValueError(
                f"Unknown subject folder '{subject_name}'. "
                f"Known: {list(FOLDER_SUBJECT_MAP.keys())}"
            )

        config = get_config(subject)
        source_name = folder.name

        source_id = str(uuid7())
        if not dry_run:
            source_id = await self._sources.get_or_create(source_name, source_id)

        existing_cats = await self._categories.get_names_for_subject(subject.value)
        cats_before = len(existing_cats)

        images = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        if not images:
            logger.warning("No images found in %s", folder)
            return {"added": 0, "skipped_dupe": 0, "skipped_error": 0, "new_categories": 0}

        logger.info("Processing %d images with concurrency=%d ...", len(images), concurrency)

        semaphore = asyncio.Semaphore(concurrency)
        db_lock = asyncio.Lock()  # serialises category resolve + DB write
        stats = {"added": 0, "skipped_dupe": 0, "skipped_error": 0, "new_categories": 0}

        async def _handle_one(image_path: Path) -> None:
            nonlocal existing_cats

            # AI call runs concurrently (semaphore-gated)
            result = await self._ai.extract_question(
                image_path, config, [c["name"] for c in existing_cats], semaphore
            )

            if result is None:
                stats["skipped_error"] += 1
                return

            # DB work is serialised to keep category state consistent
            async with db_lock:

                text_hash = _text_hash(result.question_text)
                if not dry_run and await self._questions.exists_by_text_hash(text_hash):
                    stats["skipped_dupe"] += 1
                    logger.info("Skipped (duplicate): %s", image_path.name)
                    return

                category_id, existing_cats = await self._categories.resolve(
                    result.category, subject.value, existing_cats
                )

                if dry_run:
                    logger.info(
                        "[DRY RUN] %s → category='%s' level=%s",
                        image_path.name, result.category, result.level,
                    )
                    stats["added"] += 1
                    return

                question_doc = {
                    "_id": str(uuid7()),
                    "subject": subject.value,  # denormalized for fast bot queries
                    "category_id": category_id,
                    "source_id": source_id,
                    "level": result.level.value,
                    "question": result.question_text,
                    "text_hash": text_hash,
                    "answers": result.answers,
                    "correct_answer": result.correct_answer,
                    "solution_steps": (
                        [s.model_dump() for s in result.solution_steps]
                        if result.solution_steps else None
                    ),
                }
                await self._questions.create(question_doc)
                stats["added"] += 1
                logger.info("Saved:         %s", image_path.name)

        await asyncio.gather(*[_handle_one(img) for img in images])

        stats["new_categories"] = len(existing_cats) - cats_before
        return stats
