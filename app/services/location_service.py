from starlette.exceptions import HTTPException
import logging

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
  

    async def create_country(self, country_data: Dict):

        # Normalize values
        country_data["name"] = country_data["name"].strip()
        country_data["code"] = country_data["code"].upper().strip()

        # Optional pre-check for better error messages
        existing = await self.repository.find_country_conflict(
            country_data["name"],
            country_data["code"],
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
            result = await self.repository.insert_country(country_data)
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
    
    async def update_country(self, country_id: str, update_data: dict):

        # Validate ObjectId
        if not ObjectId.is_valid(country_id):
            raise AppException(
                status_code=400,
                message="Invalid country id",
                error_code="INVALID_COUNTRY_ID",
                field="country"
            )

        country_obj_id = ObjectId(country_id)

        # Normalize values
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()

        if "code" in update_data:
            update_data["code"] = update_data["code"].upper().strip()

        # Check if country exists
        existing = await self.repository.find_country_by_id(country_obj_id)
        if not existing:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country"
            )

        # Check uniqueness (exclude current country)
        conditions = []
        if "name" in update_data and update_data["name"] != existing.get("name"):
            conditions.append({"name": update_data["name"]})

        if "code" in update_data and update_data["code"] != existing.get("code"):
            conditions.append({"code": update_data["code"]})

        if conditions:
            duplicate = await self.repository.find_country_conflict(
                update_data.get("name", existing.get("name")),
                update_data.get("code", existing.get("code")),
                exclude_id=country_obj_id,
            )

            if duplicate:
                if duplicate.get("name") == update_data.get("name"):
                    raise AppException(
                        status_code=409,
                        message="Country with this name already exists",
                        error_code="COUNTRY_NAME_EXISTS",
                        field="name"
                    )

                if duplicate.get("code") == update_data.get("code"):
                    raise AppException(
                        status_code=409,
                        message="Country with this code already exists",
                        error_code="COUNTRY_CODE_EXISTS",
                        field="code"
                    )

        try:
            self.timestamps(update_data)
            await self.repository.update_country(country_obj_id, update_data)
            return True

        except DuplicateKeyError as e:
            if "name" in str(e):
                raise AppException(
                    status_code=409,
                    message="Country with this name already exists",
                    error_code="COUNTRY_NAME_EXISTS",
                    field="name"
                )

            if "code" in str(e):
                raise AppException(
                    status_code=409,
                    message="Country with this code already exists",
                    error_code="COUNTRY_CODE_EXISTS",
                    field="code"
                )

            raise
    
    async def toggle_country_status(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(400, "Invalid country id")

        existing = await self.repository.find_country_by_id(country_id)
        if not existing:
            raise AppException(
                    status_code=404,
                    message="Country not found",
                    error_code="COUNTRY_NOT_FOUND",
                    field="country"
                )

        # Toggle the status
        new_status = not existing.get("status", True)
        update_data = {"status": new_status}
        self.timestamps(update_data)
        await self.repository.update_country(country_id, update_data)
        return True

    async def list_countries(
    self,
    page: int = 1,
    size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    search: Optional[Dict] = None
):

        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(
                status_code=400,
                message="Invalid pagination parameters",
                error_code="INVALID_PAGINATION",
                field="pagination"
            )

        if page < 1 or size < 1:
            raise AppException(
                status_code=400,
                message="page and size must be positive integers",
                error_code="INVALID_PAGINATION",
                field="pagination"
            )

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        # -------- Build Search Query --------
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

        pipeline = [

            # Match filters
            {
                "$match": query
            },

            # Sort
            {
                "$sort": {sort_by: sort_direction}
            },

            # Pagination
            {
                "$skip": skip
            },
            {
                "$limit": size
            },

            # Lookup cities
            {
                "$lookup": {
                    "from": "cities",
                    "localField": "_id",
                    "foreignField": "country",
                    "as": "cities"
                }
            },

            # Add city_count
            {
                "$addFields": {
                    "city_count": {"$size": "$cities"}
                }
            },

            # Convert ObjectId to string
            {
                "$addFields": {
                    "_id": {"$toString": "$_id"},
                    "cities": {
                        "$map": {
                            "input": "$cities",
                            "as": "city",
                            "in": {
                                "_id": {"$toString": "$$city._id"},
                                "name": "$$city.name",
                                "country": {"$toString": "$$city.country"},
                                "created_at": "$$city.created_at",
                                "updated_at": "$$city.updated_at"
                            }
                        }
                    }
                }
            }

        ]

        cursor = self.repository.aggregate_countries(pipeline)

        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)

        
        total = await self.repository.count_countries(query)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    
    async def get_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(status_code=400, message="Invalid country id", error_code="INVALID_COUNTRY_ID", field="country")

        doc = await self.repository.find_country_by_id(country_id)
        if not doc:
            raise AppException(status_code=404, message="Country not found", error_code="COUNTRY_NOT_FOUND", field="country")
        doc["_id"] = str(doc["_id"])
        return doc

    
    async def create_city(
        self,
        city_data: dict,
        image_bytes: Optional[bytes] = None,
        content_type: Optional[str] = None,
        storage: Optional[StorageService] = None
    ):

        # Normalize name
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
        country = await self.repository.find_country_by_id(country_id)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country"
            )

        # Check duplicate city in same country
        existing = await self.repository.find_city_conflict(city_data["name"], country_id)

        if existing:
            raise AppException(
                status_code=409,
                message="City with this name already exists in the specified country",
                error_code="CITY_ALREADY_EXISTS",
                field="name"
            )

        # Image upload
        if image_bytes and storage:

            slug = re.sub(r"[^a-z0-9]+", "-", city_data["name"].lower()).strip("-")

            key = f"cities/{country_id}/{slug}-{uuid.uuid4().hex[:8]}.webp"

            # if content_type:
            #     if "jpeg" in content_type or "jpg" in content_type:
            #         key += ".jpg"
            #     elif "png" in content_type:
            #         key += ".png"
            #     elif "webp" in content_type:
            #         key += ".webp"

            await storage.convert_and_upload_webp(
                key=key, 
                data=image_bytes, 
                quality=90, 
                lat=17.438001,
                lon=78.395236,
                
                )
            # await storage.upload_bytes(key, image_bytes, content_type)

            city_data["image"] = key

        city_data["country"] = country_id

        try:
            
            self.timestamps(city_data, is_new=True)
            result = await self.repository.insert_city(city_data)
            return str(result.inserted_id)
    
        except DuplicateKeyError:
            raise AppException(
                status_code=409,
                message="City with this name already exists in the specified country",
                error_code="CITY_ALREADY_EXISTS",
                field="name"
            )

    async def update_city(
        self,
        city_id: str,
        update_data: dict,
        image_bytes: Optional[bytes] = None,
        content_type: Optional[str] = None,
        storage: Optional[StorageService] = None
    ):

        if not ObjectId.is_valid(city_id):
            raise AppException(
                status_code=400,
                message="Invalid city id",
                error_code="INVALID_CITY_ID",
                field="city"
            )

        city_obj_id = ObjectId(city_id)

        existing = await self.repository.find_city_by_id(city_obj_id)
        if not existing:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city"
            )

        name = update_data.get("name", existing["name"]).strip()
        country_id = update_data.get("country", existing["country"])

        if isinstance(country_id, str):
            if not ObjectId.is_valid(country_id):
                raise AppException(
                    status_code=400,
                    message="Invalid country id",
                    error_code="INVALID_COUNTRY_ID",
                    field="country"
                )
            country_id = ObjectId(country_id)

        # Check country exists
        country = await self.repository.find_country_by_id(country_id)
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country"
            )

        # Check duplicate city
        duplicate = await self.repository.find_city_conflict(name, country_id, exclude_id=city_obj_id)

        if duplicate:
            raise AppException(
                status_code=409,
                message="City with this name already exists in the specified country",
                error_code="CITY_ALREADY_EXISTS",
                field="name"
            )

        # Upload new image
        if image_bytes and storage:

            old_image = existing.get("image")
            if old_image:
                try:
                    await storage.delete_object(old_image)
                except Exception as e:
                    logger.error(f"Failed deleting image: {e}")

            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

            key = f"cities/{country_id}/{slug}-{uuid.uuid4().hex[:8]}.webp"

            # if content_type:
            #     if "jpeg" in content_type or "jpg" in content_type:
            #         key += ".jpg"
            #     elif "png" in content_type:
            #         key += ".png"
            #     elif "webp" in content_type:
            #         key += ".webp"

            # await storage.convert_and_upload_webp(key, image_bytes, 90)
            await storage.convert_and_upload_webp(
                key=key, 
                data=image_bytes, 
                quality=90, 
                
                )
            update_data["image"] = key

        update_data["name"] = name
        update_data["country"] = country_id
        self.timestamps(update_data)
        await self.repository.update_city(city_obj_id, update_data)

        return True

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
            doc["_id"] = str(doc["_id"])
            if "country" in doc and not isinstance(doc["country"], str):
                doc["country"] = str(doc["country"])
            items.append(doc)

        return items

    async def get_city(self, city_id: str, storage: Optional[StorageService] = None):
        # validate ObjectId format first
        if not ObjectId.is_valid(city_id):
            raise AppException(status_code=400, message="Invalid city id", error_code="INVALID_CITY_ID", field="city")

        doc = await self.repository.find_city_by_id(city_id)
        if not doc:
            raise AppException(status_code=404, message="City not found", error_code="CITY_NOT_FOUND", field="city")
        # convert ObjectId to string for API responses
        doc["_id"] = str(doc["_id"])
        if "country" in doc and not isinstance(doc["country"], str):
            doc["country"] = str(doc["country"])
        if storage and "image" in doc:
            try:
                doc["image"] = storage.generate_presigned_url(doc["image"])
            except Exception:
                pass
        return doc
    async def list_cities(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: dict = None,
        storage: Optional[StorageService] = None
    ):

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

       
       

        # search filter
        if search:
            for k, v in search.items():

                if k == "country":

                    if ObjectId.is_valid(v):
                        query["country"] = ObjectId(v)
                    else:
                        countries = await self.repository.find_countries_by_name(v)

                        query["country"] = {"$in": [c["_id"] for c in countries]}

                else:
                    if isinstance(v, str):
                        query[k] = {"$regex": v, "$options": "i"}
                    else:
                        query[k] = v

        pipeline = [

            {"$match": query},

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
                "$lookup": {
                    "from": "locations",
                    "localField": "_id",
                    "foreignField": "city",
                    "as": "locations"
                }
            },

            {
                "$addFields": {
                    "country": {"$ifNull": ["$country_doc.name", ""]},
                    "location_count": {"$size": "$locations"}
                }
            },

            {
                "$project": {
                    "country_doc": 0
                }
            },

            {"$sort": {sort_by: sort_direction}},
            {"$skip": skip},
            {"$limit": size}
        ]

        cursor = self.repository.aggregate_cities(pipeline)

        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])

            for loc in doc.get("locations", []):
                loc["_id"] = str(loc["_id"])

                if "city" in loc and loc["city"]:
                    loc["city"] = str(loc["city"])

                if "country" in loc and loc["country"]:
                    loc["country"] = str(loc["country"])

            if storage and "image" in doc:
                try:
                    doc["image"] = storage.generate_presigned_url(doc["image"])
                except Exception:
                    pass

            items.append(doc)

        total = await self.repository.count_cities(query)

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    
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
        doc["_id"] = str(doc["_id"])  # ensure _id is a string for Pydantic validation
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
            doc["_id"] = str(doc["_id"])
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

    


