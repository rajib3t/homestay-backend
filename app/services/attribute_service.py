from uuid import uuid4
from warnings import filters

from jmespath import search

from app.application.dto.bed_type import BedTypeQuery
from app.application.dto.facility import FacilityQuery
from app.serializers.facility_serializer import FacilitySerializer
from app.serializers.room_type_serializer import RoomTypeSerializer
from app.services.base_service import BaseService
from app.core.exceptions import AppException
import logging
from typing import Dict, Optional
from pymongo.errors import DuplicateKeyError
from app.services.storage_service import StorageService
from bson import ObjectId
from app.repositories.attribute_repository import AttributeRepository
from app.schemas.attribute_schema import Amenity, Facility, RoomType
from app.utils.api_utils import decode_data_url
logger = logging.getLogger(__name__)
from app.application.dto.attribute import Amenity as AmenityDTO, AmenityQuery
from app.serializers.amenity_serializer import AmenitySerializer
class AttributeService(BaseService):
    """Service for managing attributes like amenities, facilities, etc.

    This is a placeholder implementation. Actual logic for creating and listing attributes
    should be implemented here, interacting with the database as needed.
    """

    def __init__(self, repository: AttributeRepository):
        super().__init__(repository.db)
        self.repository = repository

    async def create_amenity(
        self,
        data: AmenityDTO,
        session=None
    ):
        try:
            self.timestamps(data, is_new=True)

            result = await self.repository.insert_one(
                "amenities",
                data,
                session=session
            )

            created = await self.repository.find_by_id(
                "amenities",
                result.inserted_id,
                session=session
            )

            return AmenitySerializer.serialize(created)

        except DuplicateKeyError as e:

            error_msg = str(e)

            if "name" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Amenity with this name already exists",
                    error_code="AMENITY_NAME_EXISTS",
                    field="name"
                )

            raise AppException(
                status_code=500,
                message="Failed to create amenity due to a database error",
                error_code="AMENITY_CREATION_FAILED",
                field="name"
            )

        except Exception as e:
            logger.exception("Unexpected error while creating amenity")

            raise AppException(
                status_code=500,
                message=f"An unexpected error occurred: {str(e)}",
                error_code="AMENITY_CREATION_ERROR",
                field="name"
            )
    
    async def get_amenity(self, amenity_id: str, session=None) -> Amenity:
        # validate ObjectId format first
        if not ObjectId.is_valid(amenity_id):
            raise AppException(status_code=400, message="Invalid amenity id", error_code="INVALID_AMENITY_ID", field="amenity")
        
        amenity = await self.repository.find_by_id("amenities", amenity_id, session=session)
        if not amenity:
            raise AppException(status_code=404, message="Amenity not found", error_code="AMENITY_NOT_FOUND", field="amenity")
        # convert ObjectId to string for API responses
        
        return AmenitySerializer.serialize(amenity)

    async def list_amenities(
                
            self,
            query: AmenityQuery,
            
            session=None
        ) -> Dict[str, object]:
        
            await self.validate_pagination(query.page, query.size)
            filters = await self.build_query_filters(query.filters)
            
            skip = (query.page - 1) * query.size
            sort_direction = 1 if query.sort_order.lower() == "asc" else -1

            cursor = (
                    self.repository
                    .find_many("amenities", filters, session=session)
                    .sort(query.sort_by, sort_direction)
                    .skip(skip)
                    .limit(query.size)
                )
            

            
            total = await self.repository.count_documents("amenities", filters, session=session)
            items = []

            async for doc in cursor:

                serialized = AmenitySerializer.serialize(doc)

                items.append(serialized)
            return {
                "total": total,
                "page": query.page,
                "size": query.size,
                "items": items
            }
    
    
    async def update_amenity(
        self,
        amenity_id: str,
        data: dict,
        session=None
    ) -> dict:

        if not ObjectId.is_valid(amenity_id):
            raise AppException(
                status_code=400,
                message="Invalid amenity ID",
                error_code="INVALID_AMENITY_ID",
                field="amenity_id"
            )

        try:
            result = await self.repository.update_by_id(
                "amenities", amenity_id, data, session=session
            )
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="Amenity with this name already exists",
                error_code="AMENITY_NAME_EXISTS",
                field="name"
            )

        if result.matched_count == 0:
            raise AppException(
                status_code=404,
                message="Amenity not found after update",
                error_code="AMENITY_NOT_FOUND",
                field="amenity_id"
            )

        return await self.get_amenity(amenity_id, session) 

    
    
    # Similar methods for facilities can be implemented here following the same pattern as amenities
    async def create_facility(
        self,
        data: Dict[str, str],
        session=None,
        
    ) :
        # Here you would typically insert into the database and return the created object
        try:
            self.timestamps(data, is_new=True)

            result = await self.repository.insert_one(
                "facilities",
                data,
                session=session
            )

            created = await self.repository.find_by_id(
                "facilities",
                result.inserted_id,
                session=session
            )
            return FacilitySerializer.serialize(created)
        except DuplicateKeyError as e:

            error_msg = str(e)

            if "name" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Facility with this name already exists",
                    error_code="FACILITY_NAME_EXISTS",
                    field="name"
                )

            raise AppException(
                status_code=500,
                message="Failed to create facility due to a database error",
                error_code="FACILITY_CREATION_FAILED",
                field="name"
            )
        except Exception as e:
            logger.exception("Unexpected error while creating facility")
            raise AppException(
                status_code=500,
                message=f"An unexpected error occurred: {str(e)}",
                error_code="FACILITY_CREATION_ERROR",
                field="name"

                )
            
    async def get_facility(self, facility_id: str, session=None) -> Facility:    
        # validate ObjectId format first
        if not ObjectId.is_valid(facility_id):
            raise AppException(status_code=400, message="Invalid facility id", error_code="INVALID_FACILITY_ID", field="facility")
        
        facility = await self.repository.find_by_id("facilities", facility_id, session=session)
        if not facility:
            raise AppException(status_code=404, message="Facility not found", error_code="FACILITY_NOT_FOUND", field="facility")
        
        return FacilitySerializer.serialize(facility)


    async def list_facilities(
        self,
       
        query: FacilityQuery,
            
        session=None
    ) -> Dict[str, object]:
            await self.validate_pagination(query.page, query.size)
            filters = await self.build_query_filters(query.filters)
            
            skip = (query.page - 1) * query.size
            sort_direction = 1 if query.sort_order.lower() == "asc" else -1

            cursor = (
                    self.repository
                    .find_many("facilities", filters, session=session)
                    .sort(query.sort_by, sort_direction)
                    .skip(skip)
                    .limit(query.size)
                )
            

            
            total = await self.repository.count_documents("facilities", filters, session=session)
            items = []

            async for doc in cursor:

                serialized = FacilitySerializer.serialize(doc)

                items.append(serialized)
            return {
                "total": total,
                "page": query.page,
                "size": query.size,
                "items": items
            }
       
        
    
    # attribute_service.py

    async def update_facility(
        self,
        facility_id: str,
        data: Dict[str, str],
        session=None
    ) -> Dict[str, str]:

        if not ObjectId.is_valid(facility_id):
            raise AppException(status_code=400, message="Invalid facility id", error_code="INVALID_FACILITY_ID", field="facility")

        if not data:
            raise AppException(status_code=400, message="No fields to update", error_code="NO_UPDATE_FIELDS", field="facility")

        self.timestamps(data, is_new=False)

        try:
            result = await self.repository.update_by_id("facilities", facility_id, data, session=session)
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="Facility with this name already exists",
                error_code="FACILITY_NAME_EXISTS",
                field="name"
            )

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Facility not found", error_code="FACILITY_NOT_FOUND", field="facility")

        return await self.get_facility(facility_id, session)
    

    
    

    async def create_room_type(
            self, 
            data: Dict[str, str],
            session=None
        ) -> dict:
        # Here you would typically insert into the database and return the created object
        try:
            
            self.timestamps(data, is_new=True)
            result = await self.repository.insert_one("room_types", data, session=session)
            created = await self.repository.find_by_id("room_types", result.inserted_id, session=session)
            return RoomTypeSerializer.serialize(created)
        except DuplicateKeyError as e:

            error_msg = str(e)

            if "name" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Room type with this name already exists",
                    error_code="ROOM_TYPE_NAME_EXISTS",
                    field="name"
                )

            raise AppException(
                status_code=500,
                message="Failed to create room type due to a database error",
                error_code="ROOM_TYPE_CREATION_FAILED",
                field="name"
            )
        except Exception as e:
            logger.exception("Unexpected error while creating room type")
            raise AppException(
                status_code=500,
                message=f"An unexpected error occurred: {str(e)}",
                error_code="ROOM_TYPE_CREATION_ERROR",
                field="name"

                )
        
    async def get_room_type(self, room_type_id: str, session=None) -> RoomType:    
        # validate ObjectId format first
        if not ObjectId.is_valid(room_type_id):
            raise AppException(status_code=400, message="Invalid room type id", error_code="INVALID_ROOM_TYPE_ID", field="room_type")
        
        room_type = await self.repository.find_by_id("room_types", room_type_id, session=session)
        if not room_type:
            raise AppException(status_code=404, message="Room type not found", error_code="ROOM_TYPE_NOT_FOUND", field="room_type")
       
        return RoomTypeSerializer.serialize(room_type)
    

    async def list_room_types(
        self,
        query: BedTypeQuery,
        session=None
    ) -> Dict[str, object]:
        
            await self.validate_pagination(query.page, query.size)
            filters = await self.build_query_filters(query.filters)
            skip = (query.page - 1) * query.size
            sort_direction = 1 if query.sort_order.lower() == "asc" else -1



    
            cursor = (
                    self.repository
                    .find_many("room_types", filters, session=session)
                    .sort(query.sort_by, sort_direction)
                    .skip(skip)
                    .limit(query.size)
                )
            total = await self.repository.count_documents("room_types", filters, session=session)
            items = []
            async for doc in cursor:
                items.append(RoomTypeSerializer.serialize(doc))
            return {
                "items": items,
                "total": total,
                "page": query.page,
                "size": query.size
            }
    
    async def update_room_type(
            self, 
            room_type_id: str, 
            data: Dict[str, str],
            session=None
        ) -> dict:
        if not ObjectId.is_valid(room_type_id):
            raise AppException(status_code=400, message="Invalid room type id", error_code="INVALID_ROOM_TYPE_ID", field="room_type")

        if not data:
            raise AppException(status_code=400, message="No fields to update", error_code="NO_UPDATE_FIELDS", field="room_type")

        self.timestamps(data, is_new=False)
        try:
            result = await self.repository.update_by_id("room_types", room_type_id, data, session=session)
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="Room type with this name already exists",
                error_code="ROOM_TYPE_NAME_EXISTS",
                field="name"
            )

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Room type not found", error_code="ROOM_TYPE_NOT_FOUND", field="room_type")

        updated = await self.get_room_type(room_type_id, session=session)
        return updated

    
    


    def _build_query_filters(self, search: dict | None) -> dict:

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