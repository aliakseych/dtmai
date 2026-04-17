from src.interfaces.mongodb.client import MongoClient


class UserRepository:
    """User (students) database repository."""

    def __init__(self, client: MongoClient):
        if not client:
            raise ValueError("MongoDB client is required")
        self.collection = client.users()

    async def get_all(self) -> list[dict]:
        docs = await self.collection.find({}).to_list(length=None)
        for doc in docs:
            doc["id"] = str(doc.pop("_id"))
        return docs

    async def get_by_telegram_id(self, telegram_id: int) -> dict | None:
        doc = await self.collection.find_one({"telegram_id": telegram_id})
        if doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    async def update_by_vault_creds_uuid(self, vault_creds_uuid: str, data: dict) -> bool:
        result = await self.collection.update_one(
            {"vault_creds_uuid": vault_creds_uuid}, {"$set": data}
        )
        return result.modified_count > 0

    async def delete_by_telegram_id(self, telegram_id: int) -> bool:
        result = await self.collection.delete_one({"telegram_id": telegram_id})
        return result.deleted_count > 0

    async def create(self, data: dict) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)
