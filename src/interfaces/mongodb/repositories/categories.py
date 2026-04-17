from src.interfaces.mongodb.client import MongoClient


class CategoryRepository:
    """Question categories repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.categories()

    async def get_all(self) -> list[dict]:
        docs = await self.collection.find({}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_subject(self, subject: str) -> list[dict]:
        docs = await self.collection.find({"subject": subject}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_name(self, name: str) -> dict | None:
        doc = await self.collection.find_one({"name": name})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def get_by_ids(self, ids: list[str]) -> list[dict]:
        docs = await self.collection.find({"_id": {"$in": ids}}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)
