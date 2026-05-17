from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClientSession

from app.core.exceptions import AppException


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
    

    @staticmethod
    def validate_pagination(page: int, size: int):
        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION",
                field="pagination",
            )
        if page < 1 or size < 1:
            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION",
                field="pagination",
            )
        
    
    