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