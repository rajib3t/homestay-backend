from decimal import Decimal
from typing import Any, Union

from pydantic import BaseModel as PydanticBaseModel
from pydantic.v1 import BaseModel as PydanticV1BaseModel

from app.application.dto.property import PropertyQuery
from app.core.exceptions import AppException
from app.models.property_model import Property
from app.repositories.property_repository import PropertyRepository
from app.serializers.property_serializer import PropertySerializer
from app.services.base_service import BaseService


class PropertyService(BaseService):

    def __init__(self, repository: PropertyRepository):
        super().__init__(repository.db)
        self.repository = repository

    @staticmethod
    def _normalize_payload(data: Any):
        if isinstance(data, dict):
            return {key: PropertyService._normalize_payload(value) for key, value in data.items()}
        if isinstance(data, list):
            return [PropertyService._normalize_payload(item) for item in data]
        if isinstance(data, Decimal):
            return float(data)
        return data

    async def create(
        self,
        property_data: Union[dict, PydanticBaseModel, PydanticV1BaseModel],
        session=None,
    ):
        self.timestamps(property_data, is_new=True)

        if isinstance(property_data, (PydanticBaseModel, PydanticV1BaseModel)):
            payload = property_data.model_dump() if hasattr(property_data, "model_dump") else property_data.dict()
        else:
            payload = property_data

        payload = self._normalize_payload(payload)

        result = await self.repository.insert_one(payload, session=session)
        return str(result.inserted_id)
    

    async def get(
        self,
        property_id: str,       
        session=None
    ):
        property_data = await self.repository.get_property_by_id(property_id, session=session)

        if not property_data:
            raise AppException(status_code=404, message="Property not found", error_code="PROPERTY_NOT_FOUND", field="property_id")

        serialized = PropertySerializer.serialize(property_data)
        serialized = await self._resolve_bed_types(serialized, session)
        return serialized

    async def list(
        self,
        query: PropertyQuery,
        session=None
    ):
        await self.validate_pagination(query.page, query.size)

        result = await self.repository.list_properties(query, session=session)

        items = []
        for item in result["items"]:
            serialized = PropertySerializer.serialize(item)
            # Resolve bed types in rooms
            serialized = await self._resolve_bed_types(serialized, session)
            items.append(serialized)

        return {
            "total": result["total"],
            "page": result["page"],
            "size": result["size"],
            "items": items
        }

    async def _resolve_bed_types(self, item: dict, session=None):
        # Resolve bed types in rooms
        if item.get("rooms"):
            bed_type_ids = [r["type"] for r in item["rooms"]]
            bed_types_cursor = self.db.bed_types.find({"_id": {"$in": [self.to_object_id(bid) for bid in bed_type_ids]}}, session=session)
            bed_type_map = {str(doc["_id"]): doc["name"] async for doc in bed_types_cursor}
            for room in item["rooms"]:
                room["type"] = bed_type_map.get(room["type"], room["type"])

        return item
    
    async def update(
        self,
        property_id: str,
        property_data: Union[dict, PydanticBaseModel, PydanticV1BaseModel],
        session=None,
    ):
        self.timestamps(property_data, is_new=False)

        if isinstance(property_data, (PydanticBaseModel, PydanticV1BaseModel)):
            payload = property_data.model_dump() if hasattr(property_data, "model_dump") else property_data.dict()
        else:
            payload = property_data

        payload = self._normalize_payload(payload)

        try:
            existing_property = await self.repository.get_property_by_id(property_id, session=session)
        except Exception as e:
            raise AppException(status_code=500, message="Error fetching property", error_code="PROPERTY_FETCH_ERROR", field="property_id") from e

        if not existing_property:
            raise AppException(status_code=404, message="Property not found", error_code="PROPERTY_NOT_FOUND", field="property_id")

        try:
            result = await self.repository.update_property(property_id, payload, session=session)
            return result
        except Exception as e:
            raise AppException(status_code=500, message="Error updating property", error_code="PROPERTY_UPDATE_ERROR", field="property_id") from e
        

        
