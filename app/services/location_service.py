from starlette.exceptions import HTTPException

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
                raise HTTPException(status_code=400, detail="Country with this name already exists")
            if existing.get("code") == country_data["code"]:
                raise HTTPException(status_code=400, detail="Country with this code already exists")
            
        
        
        
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
            query = {k: {"$regex": v, "$options": "i"} for k, v in search.items()}
        cursor = self.db.countries.find(query).sort(sort_by, sort_direction).skip(skip).limit(size)
        items = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            items.append(doc)

        total = await self.db.countries.count_documents(query)

        return {"items": items, "total": total, "page": page, "size": size}
    
    async def create_city(self, city_data: dict):
        # Check if country exists
        country = await self.db.countries.find_one({"_id": ObjectId(city_data["country"])})
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")

        # Check if city already exists in the same country
        existing_city = await self.db.cities.find_one({"name": city_data["name"], "country": city_data["country"]})
        if existing_city:
            raise HTTPException(status_code=400, detail="City with this name already exists in the specified country")

        result = await self.db.cities.insert_one(city_data)
        return str(result.inserted_id)
