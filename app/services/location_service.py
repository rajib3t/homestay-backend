from app.services.base_service import BaseService
from app.core.exceptions import AppException
from bson import ObjectId

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
                raise AppException(400, "Country with this name already exists")
            if existing.get("code") == country_data["code"]:
                raise AppException(400, "Country with this code already exists")
            
        
        
        
        result = await self.db.countries.insert_one(country_data)
        return str(result.inserted_id)

    async def get_country(self, country_id: str):
        # validate ObjectId format first
        if not ObjectId.is_valid(country_id):
            raise AppException(400, "Invalid country id")

        doc = await self.db.countries.find_one({"_id": ObjectId(country_id)})
        if not doc:
            raise AppException(404, "Country not found")
        # convert ObjectId to string for API responses
        doc["_id"] = str(doc["_id"])
        return doc

    async def list_countries(self, page: int = 1, size: int = 10):
        # basic validation
        try:
            page = int(page)
            size = int(size)
        except Exception:
            raise AppException(400, "Invalid pagination parameters")

        if page < 1 or size < 1:
            raise AppException(400, "page and size must be positive integers")

        skip = (page - 1) * size

        cursor = self.db.countries.find().skip(skip).limit(size)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)

        total = await self.db.countries.count_documents({})

        return {"items": items, "total": total, "page": page, "size": size}