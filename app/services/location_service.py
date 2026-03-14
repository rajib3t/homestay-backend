from starlette.exceptions import HTTPException
import logging

from app.services.base_service import BaseService
from app.core.exceptions import AppException
from bson import ObjectId
from typing import Optional
import re
import uuid
from app.services.storage_service import StorageService
logger = logging.getLogger(__name__)
class LocationService(BaseService):
    async def create_country(self, country_data: dict):
        existing = await self.db.countries.find_one({"name": country_data["name"]})
            # Normalize code to uppercase
            

            # Check uniqueness by name, code, or dial_code
        existing = await self.db.countries.find_one({
            "$or": [
                {"name": country_data["name"]},
                {"code": country_data["code"]},
                
            ]
        })
        if existing:
            # Determine which field conflicts for clearer error
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
            
        
        
        result = await self.db.countries.insert_one(country_data)
        return str(result.inserted_id)
    
    async def update_country(self, country_id: str, update_data: dict):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(400, "Invalid country id")

        existing = await self.db.countries.find_one({"_id": ObjectId(country_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Country not found")

        # Check for uniqueness of name and code
        if "name" in update_data and update_data["name"] != existing["name"]:
            if await self.db.countries.find_one({"name": update_data["name"]}):
                raise HTTPException(status_code=400, detail="Country with this name already exists")
        if "code" in update_data and update_data["code"] != existing["code"]:
            if await self.db.countries.find_one({"code": update_data["code"]}):
                raise HTTPException(status_code=400, detail="Country with this code already exists")

        await self.db.countries.update_one({"_id": ObjectId(country_id)}, {"$set": update_data})
        return True
    
    async def toggle_country_status(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(400, "Invalid country id")

        existing = await self.db.countries.find_one({"_id": ObjectId(country_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Country not found")

        # Toggle the status
        new_status = not existing.get("status", True)
        await self.db.countries.update_one({"_id": ObjectId(country_id)}, {"$set": {"status": new_status}})
        return True

    async def get_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise HTTPException(status_code=400, detail="Invalid country id")

        doc = await self.db.countries.find_one({"_id": ObjectId(country_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Country not found")
        # convert ObjectId to string for API responses
        doc["_id"] = str(doc["_id"])
        # compute city count — support country stored as name or id in cities collection
        try:
            count = await self.db.cities.count_documents({
                "$or": [
                    {"country": doc["_id"]},
                    {"country": ObjectId(doc["_id"])},
                    {"country": doc.get("name")}
                ]
            })
        except Exception:
            # fallback: attempt simple name-based count
            count = await self.db.cities.count_documents({"country": doc.get("name")})
        doc["city_count"] = int(count)
        doc['cities'] = await self.list_cities_by_country(str(doc["_id"]))  # include sample cities
        return doc

    async def list_countries(self, page: int = 1, size: int = 10, sort_by: str = "name", sort_order: str = "asc", search: dict = None):
        
        # basic validation
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
        if search:
            for k, v in search.items():
                # If the value is already a dict, assume the caller provided a Mongo operator (e.g. {$regex: ...})
                if isinstance(v, dict):
                    query[k] = v
                # Convert string booleans to actual booleans so boolean fields get matched correctly
                elif isinstance(v, str):
                    lv = v.strip().lower()
                    if lv in ("true", "false"):
                        query[k] = (lv == "true")
                    else:
                        query[k] = {"$regex": v, "$options": "i"}
                else:
                    # pass through numbers, booleans, lists, etc.
                    query[k] = v
            
        cursor = self.db.countries.find(query).sort(sort_by, sort_direction).skip(skip).limit(size)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "city" in doc and not isinstance(doc["city"], str):
                doc["city"] = str(doc["city"])
            if "country" in doc and not isinstance(doc["country"], str):
                doc["country"] = str(doc["country"])
            items.append(doc)

        total = await self.db.countries.count_documents(query)

        # add city counts for each country (efficiently per-doc)
        for doc in items:
            try:
                cnt = await self.db.cities.count_documents({
                    "$or": [
                        {"country": doc["_id"]},
                        {"country": ObjectId(doc["_id"])},
                        {"country": doc.get("name")}
                    ]
                })
            except Exception:
                cnt = await self.db.cities.count_documents({"country": doc.get("name")})
            doc["city_count"] = int(cnt)
            doc['cities'] = await self.list_cities_by_country(str(doc["_id"]))  # include sample cities

        return {"items": items, "total": total, "page": page, "size": size}
    
    async def create_city(self, city_data: dict, image_bytes: Optional[bytes] = None, content_type: Optional[str] = None, storage: Optional[StorageService] = None):
        # Check if country exists
        country = await self.db.countries.find_one({"_id": ObjectId(city_data["country"])})
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        # Check if city already exists in the same country
        existing_city = await self.db.cities.find_one({"name": city_data["name"], "country": ObjectId(city_data["country"])})
        if existing_city:
            raise HTTPException(status_code=400, detail="City with this name already exists in the specified country")

        # If image bytes provided and storage is available, upload and set image key
        if image_bytes and storage:
            # generate safe key using city name and uuid
            name = city_data.get("name", "city")
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            key = f"cities/{str(country['_id'])}/{slug}-{uuid.uuid4().hex[:8]}"
            # append extension if content_type indicates common image types
            if content_type:
                lc = content_type.lower()
                if 'jpeg' in lc or 'jpg' in lc:
                    key = key + '.jpg'
                elif 'png' in lc:
                    key = key + '.png'
                elif 'webp' in lc:
                    key = key + '.webp'

            await storage.upload_bytes(key, image_bytes, content_type)
            city_data['image'] = key
            city_data['country'] = ObjectId(city_data['country'])  # ensure country is stored as ObjectId
        result = await self.db.cities.insert_one(city_data)
        return str(result.inserted_id)

    async def update_city(self, city_id: str, update_data: dict, image_bytes: Optional[bytes] = None, content_type: Optional[str] = None, storage: Optional[StorageService] = None):
        # validate ObjectId format first
        if not ObjectId.is_valid(city_id):
            raise HTTPException(status_code=400, detail="Invalid city id")

        # Check if city exists
        existing = await self.db.cities.find_one({"_id": ObjectId(city_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="City not found")

        # If name or country is being updated, check for conflicts
        name = update_data.get("name", existing.get("name"))
        country_id = update_data.get("country", existing.get("country"))
        
        if "name" in update_data or "country" in update_data:
            conflict = await self.db.cities.find_one({
                "name": name, 
                "country": country_id,
                "_id": {"$ne": ObjectId(city_id)}
            })
            if conflict:
                raise HTTPException(status_code=400, detail="City with this name already exists in the specified country")

        # Handle image update
        if image_bytes and storage:
            # Delete previous image if exists
            old_image_key = existing.get("image")
            if old_image_key:
                try:
                    await storage.delete_object(old_image_key)
                except Exception as e:
                    logger.error(f"Failed to delete old image {old_image_key}: {str(e)}")
                    # Continue anyway to update with new image

            # Generate and upload new image
            country_doc = await self.db.countries.find_one({"_id": ObjectId(country_id)})
            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            key = f"cities/{str(country_doc['_id'])}/{slug}-{uuid.uuid4().hex[:8]}"
            
            if content_type:
                lc = content_type.lower()
                if 'jpeg' in lc or 'jpg' in lc:
                    key = key + '.jpg'
                elif 'png' in lc:
                    key = key + '.png'
                elif 'webp' in lc:
                    key = key + '.webp'

            await storage.upload_bytes(key, image_bytes, content_type)
            update_data['image'] = key

        # Update the document
        if update_data:
            await self.db.cities.update_one({"_id": ObjectId(city_id)}, {"$set": update_data})
        
        return True

    async def list_cities_by_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise HTTPException(status_code=400, detail="Invalid country id")

        country = await self.db.countries.find_one({"_id": ObjectId(country_id)})
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        # match cities where the country field is stored as ObjectId, string id, or name
        query = {
            "country": {
                "$in": [country["_id"], str(country["_id"]), country.get("name")]
            }
        }

        cursor = self.db.cities.find(query)
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
            raise HTTPException(status_code=400, detail="Invalid city id")

        doc = await self.db.cities.find_one({"_id": ObjectId(city_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="City not found")
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
    async def list_cities(self, page: int = 1, size: int = 10, sort_by: str = "name", sort_order: str = "asc", search: dict = None, storage: Optional[StorageService] = None):

        # basic validation
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
        if search:
            for k, v in search.items():
                if isinstance(v, dict):
                    query[k] = v
                elif isinstance(v, str):
                    lv = v.strip().lower()
                    if lv in ("true", "false"):
                        query[k] = (lv == "true")
                    else:
                        query[k] = {"$regex": v, "$options": "i"}
                else:
                    query[k] = v
        cursor = self.db.cities.find(query).sort(sort_by, sort_direction).skip(skip).limit(size)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "country" in doc:
                # attempt to resolve country name for better API response
                try:
                    country_doc = await self.db.countries.find_one({"_id": ObjectId(doc["country"])})
                    if country_doc:
                        doc["country"] = country_doc.get("name", doc["country"])
                except Exception:
                    pass
            if storage and "image" in doc:
                try:
                    doc["image"] = storage.generate_presigned_url(doc["image"])
                except Exception:
                    pass
            items.append(doc)

        total = await self.db.cities.count_documents(query)

        return {"items": items, "total": total, "page": page, "size": size}
    
    async def create_location(self, location_data: dict):
        try:
            country_id = ObjectId(location_data["country"])
            city_id = ObjectId(location_data["city"])
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid country or city ID")

        # Check if country exists
        country = await self.db.countries.find_one({"_id": country_id})
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        # Check if city exists
        city = await self.db.cities.find_one({"_id": city_id})
        if not city:
            raise HTTPException(status_code=404, detail="City not found")

        # Check if location already exists in same city and country
        existing_location = await self.db.locations.find_one({
            "name": location_data["name"],
            "city": city_id,
            "country": country_id
        })

        if existing_location:
            raise HTTPException(
                status_code=400,
                detail="Location with this name already exists in the specified city and country"
            )

        # Prepare data to insert
        location_data["city"] = city_id
        location_data["country"] = country_id

        result = await self.db.locations.insert_one(location_data)

        return str(result.inserted_id)
    
    async def get_location(self, location_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(location_id):
            raise HTTPException(status_code=400, detail="Invalid location id")

        doc = await self.db.locations.find_one({"_id": ObjectId(location_id)})
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
    async def list_locations(self, page: int = 1, size: int = 10, sort_by: str = "name", sort_order: str = "asc", search: dict = None):
        # basic validation
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
        if search:
            for k, v in search.items():
                if isinstance(v, dict):
                    query[k] = v
                elif isinstance(v, str):
                    lv = v.strip().lower()
                    if lv in ("true", "false"):
                        query[k] = (lv == "true")
                    else:
                        query[k] = {"$regex": v, "$options": "i"}
                else:
                    query[k] = v
        cursor = self.db.locations.find(query).sort(sort_by, sort_direction).skip(skip).limit(size)
        items = []
        async for doc in cursor:
            # normalize Mongo `_id` to string so response validation succeeds
            doc["_id"] = str(doc["_id"])
            
            
            if doc.get("city"):
                    city_doc = await self.db.cities.find_one({"_id": ObjectId(doc["city"])})
                    doc["city"] = city_doc.get("name", doc["city"]) if city_doc else doc["city"]
            else:
                doc["city"] = None
            if doc.get("country"):
                country_doc = await self.db.countries.find_one({"_id": ObjectId(doc["country"])})
                doc["country"] = country_doc.get("name", doc["country"]) if country_doc else doc["country"]
            else:
                doc["country"] = None
            items.append(doc)

        total = await self.db.locations.count_documents(query)

        return {"items": items, "total": total, "page": page, "size": size}
    
    async def update_location(self, location_id: str, update_data: dict):
        # validate ObjectId format first
        if not ObjectId.is_valid(location_id):
            raise HTTPException(status_code=400, detail="Invalid location id")

        existing = await self.db.locations.find_one({"_id": ObjectId(location_id)})
        if not existing:
            raise HTTPException(status_code=404, detail="Location not found")

        # If name, city, or country is being updated, check for conflicts
        name = update_data.get("name", existing.get("name"))
        city_id = update_data.get("city", existing.get("city"))
        country_id = update_data.get("country", existing.get("country"))
        
        if "name" in update_data or "city" in update_data or "country" in update_data:
            conflict = await self.db.locations.find_one({
                "name": name, 
                "city": city_id,
                "country": country_id,
                "_id": {"$ne": ObjectId(location_id)}
            })
            if conflict:
                raise HTTPException(status_code=400, detail="Location with this name already exists in the specified city and country")

        # Update the document
        if update_data:
            await self.db.locations.update_one({"_id": ObjectId(location_id)}, {"$set": update_data})
        
        return True

    


