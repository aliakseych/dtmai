from src.interfaces.mongodb.client import MongoClient


class AttemptRepository:
    """Question attempt history repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.attempts()

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_by_user(self, user_id: str) -> list[dict]:
        docs = await self.collection.find({"user_id": user_id}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_user_and_set(self, user_id: str, set_id: str) -> list[dict]:
        docs = await self.collection.find(
            {"user_id": user_id, "set_id": set_id}
        ).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_answered_question_ids(self, user_id: str) -> list[str]:
        """Returns all unique question_ids the user has ever answered."""
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$question_id"}},
        ]
        docs = await self.collection.aggregate(pipeline).to_list(length=None)
        return [doc["_id"] for doc in docs]
