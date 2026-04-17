from src.interfaces.mongodb.client import MongoClient


class SourceRepository:
    """Question sources repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.sources()

    async def get_all(self) -> list[dict]:
        """Fetch all sources. Used to build id→name lookup caches."""
        docs = await self.collection.find({}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_or_create(self, name: str, source_id: str) -> str:
        """Returns existing source id or creates a new one."""
        doc = await self.collection.find_one({"name": name})
        if doc:
            return str(doc["_id"])
        await self.collection.insert_one({"_id": source_id, "name": name})
        return source_id
