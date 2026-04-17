from src.interfaces.mongodb.client import MongoClient


class QuestionRepository:
    """Questions repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.questions()

    async def create(self, data: dict) -> str:
        """Insert a new question document, return its id."""
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_category(self, category_id: str) -> list[dict]:
        """Fetch all questions belonging to a category. Used in question bank browsing."""
        docs = await self.collection.find({"category_id": category_id}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_id(self, question_id: str) -> dict | None:
        """Fetch a single question by id. Used to load solution steps on demand."""
        doc = await self.collection.find_one({"_id": question_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def exists_by_text_hash(self, text_hash: str) -> bool:
        """Dedup check during the ingestion pipeline — avoids inserting duplicate questions."""
        doc = await self.collection.find_one({"text_hash": text_hash})
        return doc is not None

    async def get_random(
        self,
        subject: str,
        count: int,
        level: str | None = None,
        exclude_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Returns up to `count` random questions for a subject via MongoDB $sample.
        - level: if provided, restricts to that difficulty level; None = any level (mixed)
        - exclude_ids: question ids to skip — used when user enables "exclude answered" in the test selector
        Note: $sample may return fewer than `count` docs if the pool is smaller.
        """
        match: dict = {"subject": subject}
        if level:
            match["level"] = level
        if exclude_ids:
            match["_id"] = {"$nin": exclude_ids}
        pipeline = [{"$match": match}, {"$sample": {"size": count}}]
        docs = await self.collection.aggregate(pipeline).to_list(length=count)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def count_available(
        self,
        subject: str,
        level: str | None = None,
        exclude_ids: list[str] | None = None,
    ) -> int:
        """
        Returns how many questions are available matching the given filters.
        Called by the test selector to warn the user when fewer questions exist
        than the requested count (e.g. only 3 new Math questions left out of 10 requested).
        """
        query: dict = {"subject": subject}
        if level:
            query["level"] = level
        if exclude_ids:
            query["_id"] = {"$nin": exclude_ids}
        return await self.collection.count_documents(query)