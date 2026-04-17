import logging

from uuid6 import uuid7

from src.interfaces.mongodb.repositories.categories import CategoryRepository

logger = logging.getLogger(__name__)


class CategoryService:
    """Handles category lookup and upsert logic."""

    def __init__(self, repo: CategoryRepository):
        self._repo = repo

    async def get_names_for_subject(self, subject: str) -> list[dict]:
        """Returns all categories for a subject as {id, name} dicts."""
        return await self._repo.get_by_subject(subject)

    async def resolve(
        self,
        proposed_name: str,
        subject: str,
        existing: list[dict],
    ) -> tuple[str, list[dict]]:
        """
        Finds a matching category by name (case-insensitive).
        If none found, creates a new one and appends it to `existing`.
        Returns (category_id, updated_existing).
        """
        normalized = proposed_name.strip().lower()
        for cat in existing:
            if cat["name"].strip().lower() == normalized:
                return cat["id"], existing

        # No match — create new category
        new_id = str(uuid7())
        await self._repo.create({
            "_id": new_id,
            "subject": subject,
            "name": proposed_name.strip(),
        })
        new_entry = {"id": new_id, "name": proposed_name.strip()}
        existing = existing + [new_entry]
        logger.info("New category created: '%s' (subject=%s)", proposed_name, subject)
        return new_id, existing
