from starlette.exceptions import HTTPException
import logging

from app.application.dto.city_query import CityQuery
from app.application.dto.country_query import CountryQuery
from app.serializers.city_serializer import CitySerializer
from app.services.base_service import BaseService
from app.core.exceptions import AppException
from bson import ObjectId
from typing import Optional,Dict
import re
import uuid
from app.services.storage_service import StorageService
from app.repositories.location_repository import LocationRepository
from pymongo.errors import DuplicateKeyError
logger = logging.getLogger(__name__)
class LocationService(BaseService):
    def __init__(self, repository: LocationRepository):
        super().__init__(repository.db)
        self.repository = repository
  

    async def create_country(self, country_data: Dict, session=None):

        # Normalize values
        country_data["name"] = country_data["name"].strip()
        country_data["code"] = country_data["code"].upper().strip()

        # Optional pre-check for better error messages
        existing = await self.repository.find_country_conflict(
            country_data["name"],
            country_data["code"],
            session=session
        )

        if existing:
            if existing.get("name") == country_data["name"]:
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name"
                )

            if existing.get("code") == country_data["code"]:
                raise AppException(
                    status_code=409,
                    message="Country with this code already exists",
                    error_code="COUNTRY_CODE_EXISTS",
                    field="code"
                )

        try:
            self.timestamps(country_data, is_new=True)
            result = await self.repository.insert_country(country_data, session=session)
            return str(result.inserted_id)

        except DuplicateKeyError as e:

            error_msg = str(e)

            if "name" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name"
                )

            if "code" in error_msg:
                raise AppException(
                    status_code=409,
                    message="Country with this code already exists",
                    error_code="COUNTRY_CODE_EXISTS",
                    field="code"
                )

            raise
    
    async def update_country(
        self,
        country_id: str,
        payload: dict,
        session=None,
    ):

        country_id = self._validate_country_id(country_id)

        existing = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        if not existing:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        normalized_payload = self._normalize_country_payload(payload)

        await self._ensure_country_unique(
            existing=existing,
            payload=normalized_payload,
            country_id=country_id,
            session=session,
        )

        self.timestamps(normalized_payload)

        await self.repository.update_country(
            country_id=country_id,
            update_data=normalized_payload,
            session=session,
        )

        updated_country = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        # Convert ObjectId to string for API response
        if updated_country:
            updated_country["id"] = str(updated_country.pop("_id"))

        return updated_country

    def _validate_country_id(self, country_id: str):

        if not ObjectId.is_valid(country_id):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country",
            )

        return ObjectId(country_id)

    def _normalize_country_payload(
        self,
        payload: dict,
    ):

        normalized = payload.copy()

        if "name" in normalized:
            normalized["name"] = normalized["name"].strip()

        if "code" in normalized:
            normalized["code"] = normalized["code"].strip().upper()

        return normalized

    async def _ensure_country_unique(
        self,
        existing: dict,
        payload: dict,
        country_id,
        session=None,
    ):

        name_changed = (
            "name" in payload
            and payload["name"] != existing.get("name")
        )

        code_changed = (
            "code" in payload
            and payload["code"] != existing.get("code")
        )

        if not name_changed and not code_changed:
            return

        duplicate = await self.repository.find_country_conflict(
            name=payload.get("name", existing.get("name")),
            code=payload.get("code", existing.get("code")),
            exclude_id=country_id,
            session=session,
        )

        if not duplicate:
            return

        if duplicate.get("name") == payload.get("name"):
            raise AppException(
                status_code=409,
                message="Country with this name already exists",
                error_code="COUNTRY_NAME_EXISTS",
                field="name",
            )

        if duplicate.get("code") == payload.get("code"):
            raise AppException(
                status_code=409,
                message="Country with this code already exists",
                error_code="COUNTRY_CODE_EXISTS",
                field="code",
            )
    
    async def toggle_country_status(
        self,
        country_id: str,
        updated_by: str,
        session=None,
    ):

        if not ObjectId.is_valid(country_id):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country_id",
            )

        country = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )

        updated_data = {
            "status": not country.get("status", True),
            "updated_by": updated_by,
        }

        self.timestamps(updated_data)

        await self.repository.update_country(
            country_id=country_id,
            update_data=updated_data,
            session=session,
        )

        updated_country = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        # Convert ObjectId to string for API response
        if updated_country:
            updated_country["id"] = str(updated_country.pop("_id"))

        return updated_country

    async def list_countries(
        self,
        query: CountryQuery,
        session=None,
    ):

        return await self.repository.list_countries(
            query=query,
            session=session,
        )
    
    async def get_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(status_code=400, message="Invalid country id", error_code="INVALID_COUNTRY_ID", field="country")

        doc = await self.repository.find_country_by_id(country_id)
        if not doc:
            raise AppException(status_code=404, message="Country not found", error_code="COUNTRY_NOT_FOUND", field="country")
        doc["id"] = str(doc.pop("_id"))
        # Ensure dial_code field exists for backward compatibility
        if "dial_code" not in doc:
            doc["dial_code"] = 1
        return doc

    
    async def create_city(
        self,
        city_data: dict,
        session=None,
    ):
        # Normalize
        city_data["name"] = city_data["name"].strip()

        # Validate country id
        if not ObjectId.is_valid(city_data["country"]):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country"
            )

        country_id = ObjectId(city_data["country"])

        # Check country exists
        country = await self.repository.find_country_by_id(country_id, session=session)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country"
            )

        # Check duplicate
        existing = await self.repository.find_city_conflict(
            city_data["name"], country_id,
            session=session
        )

        if existing:
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name"
            )

        city_data["country"] = country_id

        self.timestamps(city_data, is_new=True)

        try:
            result = await self.repository.insert_city(city_data, session=session)
            return str(result.inserted_id) # return ObjectId (not string)
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name"
            )
    async def update_city(
        self,
        city_id: str,
        payload: dict,
        session=None,
    ):

        city_object_id = self._validate_city_id(
            city_id
        )

        existing_city = await self._get_existing_city(
            city_object_id,
            session=session,
        )

        normalized_payload = (
            self._normalize_city_payload(
                payload=payload,
                existing_city=existing_city,
            )
        )

        await self._validate_country(
            normalized_payload["country"],
            session=session,
        )

        await self._ensure_city_unique(
            name=normalized_payload["name"],
            country_id=normalized_payload["country"],
            city_id=city_object_id,
            session=session,
        )

        self.timestamps(normalized_payload)

        await self.repository.update_city(
            city_id=city_object_id,
            update_data=normalized_payload,
            session=session,
        )

        updated_city = await self.repository.find_city_by_id(
            city_object_id,
            session=session,
        )

        return CitySerializer.serialize(
            updated_city
        )
    
    def _validate_city_id(
        self,
        city_id: str,
    ):

        if not ObjectId.is_valid(city_id):
            raise AppException(
                status_code=400,
                message="Invalid city id",
                error_code="INVALID_CITY_ID",
                field="city",
            )

        return ObjectId(city_id)
    
    async def _get_existing_city(
        self,
        city_id,
        session=None,
    ):

        city = await self.repository.find_city_by_id(
            city_id,
            session=session,
        )

        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        return city
    
    async def _get_existing_city(
        self,
        city_id,
        session=None,
    ):

        city = await self.repository.find_city_by_id(
            city_id,
            session=session,
        )

        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        return city
    def _normalize_city_payload(
        self,
        payload: dict,
        existing_city: dict,
    ):

        normalized = payload.copy()

        normalized["name"] = (
            payload.get(
                "name",
                existing_city["name"],
            )
            .strip()
        )

        country_id = payload.get(
            "country",
            existing_city["country"],
        )

        if isinstance(country_id, str):

            if not ObjectId.is_valid(country_id):
                raise AppException(
                    status_code=400,
                    message="Invalid country id",
                    error_code="INVALID_COUNTRY_ID",
                    field="country",
                )

            country_id = ObjectId(country_id)

        normalized["country"] = country_id

        return normalized

    async def _validate_country(
        self,
        country_id,
        session=None,
    ):

        country = await self.repository.find_country_by_id(
            country_id,
            session=session,
        )

        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country",
            )
        
    async def _ensure_city_unique(
        self,
        name: str,
        country_id,
        city_id,
        session=None,
    ):

        duplicate = await self.repository.find_city_conflict(
            name=name,
            country_id=country_id,
            exclude_id=city_id,
            session=session,
        )

        if duplicate:
            raise AppException(
                status_code=409,
                message=(
                    "City with this name "
                    "already exists "
                    "in the specified country"
                ),
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )
    async def list_cities_by_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(status_code=400, message="Invalid country id", error_code="INVALID_COUNTRY_ID", field="country")

        country = await self.repository.find_country_by_id(country_id)
        if not country:
            raise AppException(status_code=404, message="Country not found", error_code="COUNTRY_NOT_FOUND", field="country")

        # match cities where the country field is stored as ObjectId, string id, or name
        query = {
            "country": {
                "$in": [country["_id"], str(country["_id"]), country.get("name")]
            }
        }

        cursor = self.repository.find_cities(query)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            if "country" in doc and not isinstance(doc["country"], str):
                doc["country"] = str(doc["country"])
            items.append(doc)

        return items

    async def get_raw_city(
        self,
        city_id: str,
        session=None,
    ):

        if not ObjectId.is_valid(city_id):
            raise AppException(
                status_code=400,
                message="Invalid city id",
                error_code="INVALID_CITY_ID",
                field="city",
            )

        city = await self.repository.find_city_by_id(
            city_id,
            session=session,
        )

        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        return city
    async def get_city(
        self,
        city_id: str,
        session=None,
    ):

        if not ObjectId.is_valid(city_id):
            raise AppException(
                status_code=400,
                message="Invalid city id",
                error_code="INVALID_CITY_ID",
                field="city",
            )

        doc = await self.repository.find_city_by_id(
            city_id,
            session=session,
        )

        if not doc:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city",
            )

        doc["id"] = str(doc.pop("_id"))

        if "country" in doc and not isinstance(
            doc["country"],
            str,
        ):
            doc["country"] = str(doc["country"])

        return doc
    
    async def list_cities(
        self,
        query: CityQuery,
        session=None,
    ):

        return await self.repository.list_cities(
            query=query,
            session=session,
        )
    
    async def create_location(self, location_data: dict):
        try:
            country_id = ObjectId(location_data["country"])
            city_id = ObjectId(location_data["city"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid country or city ID")

        # Check if country exists
        country = await self.repository.find_country_by_id(country_id)
        if not country:
            raise AppException(status_code=404, message="Country not found", error_code="COUNTRY_NOT_FOUND", field="country")

        # Check if city exists
        city = await self.repository.find_city_by_id(city_id)
        if not city:
            raise AppException(status_code=404, message="City not found", error_code="CITY_NOT_FOUND", field="city")

        # Check if location already exists in same city and country
        existing_location = await self.repository.find_location_conflict(
            location_data["name"],
            city_id,
            country_id,
        )

        if existing_location:
            raise AppException(status_code=400, message="Location with this name already exists in the specified city and country", error_code="LOCATION_ALREADY_EXISTS", field="name") 
           

        # Prepare data to insert
        location_data["city"] = city_id
        location_data["country"] = country_id
        self.timestamps(location_data, is_new=True)
        result = await self.repository.insert_location(location_data)

        return str(result.inserted_id)
    
    async def get_location(self, location_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(location_id):
            raise HTTPException(status_code=400, detail="Invalid location id")

        doc = await self.repository.find_location_by_id(location_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Location not found")
        # convert ObjectId to string for API responses
        doc["id"] = str(doc.pop("_id"))  # ensure _id is a string for Pydantic validation
        # also normalize related object ids to strings
        if "country" in doc and not isinstance(doc["country"], str):
            doc["country"] = str(doc["country"])
        if "city" in doc and not isinstance(doc["city"], str):
            doc["city"] = str(doc["city"])
        return doc
    async def list_locations(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: dict = None
    ):

        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")

        if page < 1 or size < 1:
            raise HTTPException(status_code=400, detail="page and size must be positive integers")

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        query = {}

        # search filters
        if search:
            for k, v in search.items():

                if k == "country":
                    if ObjectId.is_valid(v):
                        query["country"] = ObjectId(v)
                    else:
                        countries = await self.repository.find_countries_by_name(v)

                        query["country"] = {"$in": [c["_id"] for c in countries]}

                elif k == "city":
                    if ObjectId.is_valid(v):
                        query["city"] = ObjectId(v)
                    else:
                        cities = await self.repository.find_locations_by_city_name(v)

                        query["city"] = {"$in": [c["_id"] for c in cities]}

                else:
                    query[k] = {"$regex": v, "$options": "i"} if isinstance(v, str) else v

        pipeline = [

            {"$match": query},

            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city",
                    "foreignField": "_id",
                    "as": "city_doc"
                }
            },

            {
                "$unwind": {
                    "path": "$city_doc",
                    "preserveNullAndEmptyArrays": True
                }
            },

            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country",
                    "foreignField": "_id",
                    "as": "country_doc"
                }
            },

            {
                "$unwind": {
                    "path": "$country_doc",
                    "preserveNullAndEmptyArrays": True
                }
            },

            {
                "$addFields": {
                    "city": {"$ifNull": ["$city_doc.name", ""]},
                    "country": {"$ifNull": ["$country_doc.name", ""]}
                }
            },

            {
                "$project": {
                    "city_doc": 0,
                    "country_doc": 0
                }
            },

            {"$sort": {sort_by: sort_direction}},
            {"$skip": skip},
            {"$limit": size}
        ]

        cursor = self.repository.aggregate_locations(pipeline)

        items = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            items.append(doc)

        total = await self.repository.count_locations(query)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    
    async def update_location(self, location_id: str, update_data: dict):

        if not ObjectId.is_valid(location_id):
            raise AppException(
                status_code=400,
                message="Invalid location id",
                error_code="INVALID_LOCATION_ID",
                field="location"
            )

        existing = await self.repository.find_location_by_id(location_id)
        if not existing:
            raise AppException(
                status_code=404,
                message="Location not found",
                error_code="LOCATION_NOT_FOUND",
                field="location"
            )

        # Convert ids if provided
        if "city" in update_data:
            if not ObjectId.is_valid(update_data["city"]):
                raise AppException(400, "Invalid city id", "INVALID_CITY_ID", "city")
            update_data["city"] = ObjectId(update_data["city"])

        if "country" in update_data:
            if not ObjectId.is_valid(update_data["country"]):
                raise AppException(400, "Invalid country id", "INVALID_COUNTRY_ID", "country")
            update_data["country"] = ObjectId(update_data["country"])

        name = update_data.get("name", existing.get("name"))
        city_id = update_data.get("city", existing.get("city"))
        country_id = update_data.get("country", existing.get("country"))

        # Conflict check
        if "name" in update_data or "city" in update_data or "country" in update_data:
            conflict = await self.repository.find_location_conflict(
                name,
                city_id,
                country_id,
                exclude_id=location_id,
            )

            if conflict:
                raise AppException(
                    status_code=409,
                    message="Location with this name already exists in the specified city and country",
                    error_code="LOCATION_ALREADY_EXISTS",
                    field="name"
                )

        if update_data:
            self.timestamps(update_data)
            await self.repository.update_location(location_id, update_data)

        return True

    


