from datetime import datetime, timezone
from typing import Optional, Union
from bson import ObjectId

from pydantic import BaseModel as PydanticBaseModel
from pydantic.v1 import BaseModel as PydanticV1BaseModel

from app.core.exceptions import AppException


class BaseService:
    def __init__(self, db):
        self.db = db

    def timestamps(self, data: Union[dict, PydanticBaseModel, PydanticV1BaseModel], is_new: bool = False):
        now = datetime.now(timezone.utc)

        if isinstance(data, (PydanticBaseModel, PydanticV1BaseModel)):
            if is_new:
                data.created_at = now
            data.updated_at = now
            return data

        if is_new:
            data["created_at"] = now

        data["updated_at"] = now
        return data

    def to_object_id(self, value):
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        return value


    async def validate_pagination(self, page: int, size: int):
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
        
    
    async def build_query_filters(self, search: Optional[dict]) -> dict:

        query = {}

        if not search:
            return query

        for key, value in search.items():

            if isinstance(value, dict):
                query[key] = value

            elif isinstance(value, str):

                lv = value.strip().lower()

                if lv in ("true", "false"):
                    query[key] = lv == "true"
                else:
                    query[key] = {
                        "$regex": value,
                        "$options": "i"
                    }

            else:
                query[key] = value

        return query