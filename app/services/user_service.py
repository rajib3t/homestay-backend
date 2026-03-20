from datetime import datetime
from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.repositories.user_repository import UserRepository

class UserService(BaseService):
    def __init__(self, repository: UserRepository):
        super().__init__(repository.db)
        self.repository = repository

    @staticmethod
    def _serialize_user(user: dict):
        user = user.copy()
        user.pop("password", None)
        user["_id"] = str(user["_id"])

        if user.get("created_at") and isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()

        if user.get("updated_at") and isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()

        return user

    async def create_user(self, user_data: dict):
        existing = await self.repository.find_by_email(user_data["email"])
        if existing:
            raise AppException(400, "Email already exists")

        # Hash the password
        user_data["password"] = PasswordHasher.hash_password(user_data["password"])
        self.timestamps(user_data, is_new=True)
        result = await self.repository.insert(user_data)
        return str(result.inserted_id)

    async def get_user(self, user_id: str):
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise AppException(404, "User not found")
        return self._serialize_user(user)

    async def update_user(self, user_id: str, update_data: dict):
        if not update_data:
            raise AppException(400, "No fields provided for update")
        
        # Check if email is being updated and if it's already taken
        if "email" in update_data:
            existing = await self.repository.find_by_email_excluding_id(update_data["email"], user_id)
            if existing:
                raise AppException(400, "Email already exists")

        self.timestamps(update_data)
        result = await self.repository.update_by_id(user_id, update_data)
        
        if result.matched_count == 0:
            raise AppException(404, "User not found")
        
        return await self.get_user(user_id)

    async def authenticate_user(self, email: str, password: str):
        user = await self.repository.find_by_email(email)
        if not user:
            return None
        
        if not PasswordHasher.verify_password(password, user["password"]):
            return None
        
        return self._serialize_user(user)