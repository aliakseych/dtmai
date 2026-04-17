from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class MongoClient:
    """MongoDB client wrapping Motor."""

    def __init__(self, uri: str, db_name: str):
        if not all([uri, db_name]):
            raise ValueError("uri and db_name are required")
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]

    def users(self) -> AsyncIOMotorCollection:
        return self.db["users"]

    def questions(self) -> AsyncIOMotorCollection:
        return self.db["questions"]

    def categories(self) -> AsyncIOMotorCollection:
        return self.db["categories"]

    def sources(self) -> AsyncIOMotorCollection:
        return self.db["sources"]

    def attempts(self) -> AsyncIOMotorCollection:
        return self.db["attempts"]

    def programs(self) -> AsyncIOMotorCollection:
        return self.db["programs"]
