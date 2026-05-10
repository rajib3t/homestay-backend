from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession


class BaseRepository:
    def __init__(self, db):
        self.db = db

    # -------------------------
    # TIMESTAMPS
    # -------------------------
    def timestamps(self, data: dict, is_new: bool = False):
        now = datetime.now(timezone.utc)

        if is_new:
            data["created_at"] = now

        data["updated_at"] = now
        return data

    # -------------------------
    # OBJECT ID HELPERS
    # -------------------------
    def to_object_id(self, value):
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        return value

    # -------------------------
    # TRANSACTION SUPPORT
    # -------------------------
    async def start_session(self) -> AsyncIOMotorClientSession:
        return await self.db.client.start_session()