from src.interfaces.mongodb.client import MongoClient


class ProgramRepository:
    """Programs repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.programs()

    async def get_all(self) -> list[dict]:
        docs = await self.collection.find({}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_id(self, program_id: str) -> dict | None:
        doc = await self.collection.find_one({"_id": program_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc