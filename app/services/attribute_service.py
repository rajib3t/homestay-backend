from uuid import uuid4

from app.models.attribute_model import CreateFacility
from app.services.base_service import BaseService
from app.core.exceptions import AppException
from starlette.exceptions import HTTPException
import logging
from typing import List, Dict, Optional
from pymongo.errors import DuplicateKeyError
from app.services.storage_service import StorageService
from bson import ObjectId
from app.repositories.attribute_repository import AttributeRepository
from app.schemas.attribute_schema import Amenity, Facility, RoomType
from app.utils.api_utils import decode_data_url
logger = logging.getLogger(__name__)


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
            data: Dict[str, str], 
            storage: Optional[StorageService] = None
        ) -> str:
        
       
        name = data.get("name")
        icon = data.get("icon")
        status = data.get("status", True)
        # Here you would typically insert into the database and return the created object
        try:
            # Placeholder for actual creation logic
            new_amenity = {
                "name": name,
                "icon": icon,
                "status": status
            }
            

            self.timestamps(new_amenity, is_new=True)
            result = await self.repository.insert_one("amenities", new_amenity)
            return str(result.inserted_id)
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
    
    async def get_amenity(self, amenity_id: str, storage: Optional[StorageService] = None) -> Amenity:
        # validate ObjectId format first
        if not ObjectId.is_valid(amenity_id):
            raise AppException(status_code=400, message="Invalid amenity id", error_code="INVALID_AMENITY_ID", field="amenity")
        
        amenity = await self.repository.find_by_id("amenities", amenity_id)
        if not amenity:
            raise AppException(status_code=404, message="Amenity not found", error_code="AMENITY_NOT_FOUND", field="amenity")
        # convert ObjectId to string for API responses
        amenity["_id"] = str(amenity["_id"])
        if storage and amenity.get("icon"):
            try:
                amenity["icon"] = storage.generate_presigned_url(amenity["icon"])
            except Exception:
                pass
        return amenity

    async def list_amenities(
                
            self,
            page: int = 1,
            size: int = 10,
            sort_by: str = "name",
            sort_order: str = "asc",
            search: dict = None,
            storage: Optional[StorageService] = None
        ) -> Dict[str, object]:
        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION_PARAMETERS",
                field="pagination"
            )
        if page < 1 or size < 1:
            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION_VALUES",
                field="pagination"
            )

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        query = {}

        if search:
            for k, v in search.items():

                if isinstance(v, dict):
                    query[k] = v

                elif isinstance(v, str):
                    lv = v.strip().lower()

                    if lv in ("true", "false"):
                        query[k] = lv == "true"
                    else:
                        query[k] = {"$regex": v, "$options": "i"}

                else:
                    query[k] = v

    
        cursor = self.repository.find_many("amenities", query).sort(sort_by, sort_direction).skip(skip).limit(size)
        total = await self.repository.count_documents("amenities", query)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if storage and "icon" in doc:
                try:
                    doc["icon"] = storage.generate_presigned_url(doc["icon"])
                except Exception:
                    pass
            items.append(doc)
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
    
    
    async def update_amenity(self, amenity_id: str, data: Dict[str, str], storage: Optional[StorageService] = None) -> Amenity:
        if not ObjectId.is_valid(amenity_id):
            raise AppException(status_code=400, message="Invalid amenity id", error_code="INVALID_AMENITY_ID", field="amenity")

        if not data:
            raise AppException(status_code=400, message="No fields to update", error_code="NO_UPDATE_FIELDS", field="amenity")

        self.timestamps(data, is_new=False)

        result = await self.repository.update_by_id("amenities", amenity_id, data)

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Amenity not found", error_code="AMENITY_NOT_FOUND", field="amenity")

        updated = await self.get_amenity(amenity_id, storage)
        return updated
    
    async def toggle_amenity_status(self, amenity_id: str) -> Amenity:
        if not ObjectId.is_valid(amenity_id):
            raise AppException(status_code=400, message="Invalid amenity id", error_code="INVALID_AMENITY_ID", field="amenity")

        amenity = await self.repository.find_by_id("amenities", amenity_id)
        if not amenity:
            raise AppException(status_code=404, message="Amenity not found", error_code="AMENITY_NOT_FOUND", field="amenity")

        new_status = not amenity.get("status", True)
        self.timestamps(amenity, is_new=False)
        result = await self.repository.update_by_id("amenities", amenity_id, {"status": new_status})

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Amenity not found during status toggle", error_code="AMENITY_NOT_FOUND_TOGGLE", field="amenity")

        updated = await self.get_amenity(amenity_id)
        return updated
    
    # Similar methods for facilities can be implemented here following the same pattern as amenities
    async def create_facility(
        self,
        data: Dict[str, str],
        storage: Optional[StorageService] = None) -> str:
        
        # Here you would typically insert into the database and return the created object
        try:
            name = data.get("name")
            icon = data.get("icon")
            status = data.get("status", True)
            # Placeholder for actual creation logic
            new_facility = {
                "name": name,
                "icon": icon,
                "status": status
            }
            if storage and icon and isinstance(icon, str) and icon.startswith("data:"):
                raw, mime, ext = decode_data_url(icon)
                key_name = name.lower().replace(" ", "_") if name else uuid4().hex
                key = f"facilities/{key_name}_{uuid4().hex}{ext}"

                await storage.upload_bytes(key, raw, content_type=mime)

                new_facility["icon"] = key
            self.timestamps(new_facility, is_new=True)
            result = await self.repository.insert_one("facilities", new_facility)
            return str(result.inserted_id)
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
            
    async def get_facility(self, facility_id: str, storage: Optional[StorageService] = None) -> Facility:    
        # validate ObjectId format first
        if not ObjectId.is_valid(facility_id):
            raise AppException(status_code=400, message="Invalid facility id", error_code="INVALID_FACILITY_ID", field="facility")
        
        facility = await self.repository.find_by_id("facilities", facility_id)
        if not facility:
            raise AppException(status_code=404, message="Facility not found", error_code="FACILITY_NOT_FOUND", field="facility")
        # convert ObjectId to string for API responses
        facility["_id"] = str(facility["_id"])
        if storage and "icon" in facility:
            try:
                facility["icon"] = storage.generate_presigned_url(facility["icon"])
            except Exception:
                pass
        return facility


    async def list_facilities(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "name",
        sort_order: str = "asc",
        search: dict = None,
        storage: Optional[StorageService] = None
    ) -> Dict[str, object]:
        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION_PARAMETERS",
                field="pagination"
            )
        if page < 1 or size < 1:
            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION_VALUES",
                field="pagination"
            )

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        query = {}

        if search:
            for k, v in search.items():

                if isinstance(v, dict):
                    query[k] = v

                elif isinstance(v, str):
                    lv = v.strip().lower()

                    if lv in ("true", "false"):
                        query[k] = lv == "true"
                    else:
                        query[k] = {"$regex": v, "$options": "i"}

                else:
                    query[k] = v

    
        cursor = self.repository.find_many("facilities", query).sort(sort_by, sort_direction).skip(skip).limit(size)
        total = await self.repository.count_documents("facilities", query)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if storage and "icon" in doc:
                try:
                    doc["icon"] = storage.generate_presigned_url(doc["icon"])
                except Exception:
                    pass
            items.append(doc)
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
       
        
    
    async def update_facility(self, facility_id: str, data: Dict[str, str], storage: Optional[StorageService] = None) -> Facility:
        if not ObjectId.is_valid(facility_id):
            raise AppException(status_code=400, message="Invalid facility id", error_code="INVALID_FACILITY_ID", field="facility")

        if not data:
            raise AppException(status_code=400, message="No fields to update", error_code="NO_UPDATE_FIELDS", field="facility")

        self.timestamps(data, is_new=False)

        result = await self.repository.update_by_id("facilities", facility_id, data)

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Facility not found", error_code="FACILITY_NOT_FOUND", field="facility")

        updated = await self.get_facility(facility_id, storage)
        return updated
    

    async def toggle_facility_status(self, facility_id: str) -> Facility:
        if not ObjectId.is_valid(facility_id):
            raise AppException(status_code=400, message="Invalid facility id", error_code="INVALID_FACILITY_ID", field="facility")

        facility = await self.repository.find_by_id("facilities", facility_id)
        if not facility:
            raise AppException(status_code=404, message="Facility not found", error_code="FACILITY_NOT_FOUND", field="facility")

        new_status = not facility.get("status", True)
        self.timestamps(facility, is_new=False)
        result = await self.repository.update_by_id("facilities", facility_id, {"status": new_status})

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Facility not found during status toggle", error_code="FACILITY_NOT_FOUND_TOGGLE", field="facility")

        updated = await self.get_facility(facility_id)
        return updated
    

    async def create_room_type(self, data: Dict[str, str]) -> str:
        # Here you would typically insert into the database and return the created object
        try:
            name = data.get("name")
            capacity = data.get("capacity")
            status = data.get("status", True)
            # Placeholder for actual creation logic
            new_room_type = {
                "name": name,
                "capacity": capacity,
                "status": status
            }
            self.timestamps(new_room_type, is_new=True)
            result = await self.repository.insert_one("room_types", new_room_type)
            return str(result.inserted_id)
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
        
    async def get_room_type(self, room_type_id: str) -> RoomType:    
        # validate ObjectId format first
        if not ObjectId.is_valid(room_type_id):
            raise AppException(status_code=400, message="Invalid room type id", error_code="INVALID_ROOM_TYPE_ID", field="room_type")
        
        room_type = await self.repository.find_by_id("room_types", room_type_id)
        if not room_type:
            raise AppException(status_code=404, message="Room type not found", error_code="ROOM_TYPE_NOT_FOUND", field="room_type")
        # convert ObjectId to string for API responses
        room_type["_id"] = str(room_type["_id"])
        return room_type
    

    async def list_room_types(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "name",
        sort_order: str = "asc",
        search: dict = None
    ) -> Dict[str, object]:
        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION_PARAMETERS",
                field="pagination"
            )
        if page < 1 or size < 1:
            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION_VALUES",
                field="pagination"
            )

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        query = {}

        if search:
            for k, v in search.items():

                if isinstance(v, dict):
                    query[k] = v

                elif isinstance(v, str):
                    lv = v.strip().lower()

                    if lv in ("true", "false"):
                        query[k] = lv == "true"
                    else:
                        query[k] = {"$regex": v, "$options": "i"}

                else:
                    query[k] = v

    
        cursor = self.repository.find_many("room_types", query).sort(sort_by, sort_direction).skip(skip).limit(size)
        total = await self.repository.count_documents("room_types", query)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)
        return {
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
    
    async def update_room_type(self, room_type_id: str, data: Dict[str, str]) -> RoomType:
        if not ObjectId.is_valid(room_type_id):
            raise AppException(status_code=400, message="Invalid room type id", error_code="INVALID_ROOM_TYPE_ID", field="room_type")

        if not data:
            raise AppException(status_code=400, message="No fields to update", error_code="NO_UPDATE_FIELDS", field="room_type")

        self.timestamps(data, is_new=False)

        result = await self.repository.update_by_id("room_types", room_type_id, data)

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Room type not found", error_code="ROOM_TYPE_NOT_FOUND", field="room_type")

        updated = await self.get_room_type(room_type_id)
        return updated
    
    async def toggle_room_type_status(self, room_type_id: str) -> RoomType:
        if not ObjectId.is_valid(room_type_id):
            raise AppException(status_code=400, message="Invalid room type id", error_code="INVALID_ROOM_TYPE_ID", field="room_type")

        room_type = await self.repository.find_by_id("room_types", room_type_id)
        if not room_type:
            raise AppException(status_code=404, message="Room type not found", error_code="ROOM_TYPE_NOT_FOUND", field="room_type")

        new_status = not room_type.get("status", True)
        self.timestamps(room_type, is_new=False)
        result = await self.repository.update_by_id("room_types", room_type_id, {"status": new_status})

        if result.matched_count == 0:
            raise AppException(status_code=404, message="Room type not found during status toggle", error_code="ROOM_TYPE_NOT_FOUND_TOGGLE", field="room_type")

        updated = await self.get_room_type(room_type_id)
        return updated