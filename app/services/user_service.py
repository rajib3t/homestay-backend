from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from bson import ObjectId

class UserService(BaseService):

    async def create_user(self, user_data: dict):
        existing = await self.db.users.find_one({"email": user_data["email"]})
        if existing:
            raise AppException(400, "Email already exists")

        # Hash the password
        user_data["password"] = PasswordHasher.hash_password(user_data["password"])
        
        result = await self.db.users.insert_one(user_data)
        return str(result.inserted_id)

    async def get_user(self, user_id: str):
        user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise AppException(404, "User not found")
        user["_id"] = str(user["_id"])
        return user

    async def update_user(self, user_id: str, update_data: dict):
        if not update_data:
            raise AppException(400, "No fields provided for update")
        
        # Check if email is being updated and if it's already taken
        if "email" in update_data:
            existing = await self.db.users.find_one({
                "email": update_data["email"],
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing:
                raise AppException(400, "Email already exists")

        result = await self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise AppException(404, "User not found")
        
        return await self.get_user(user_id)

    async def authenticate_user(self, email: str, password: str):
        user = await self.db.users.find_one({"email": email})
        if not user:
            return None
        
        if not PasswordHasher.verify_password(password, user["password"]):
            return None
        
        user["_id"] = str(user["_id"])
        return user