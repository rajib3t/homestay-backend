from datetime import datetime
from typing import Optional

from app.application.dto.user import UserQuery
from app.schemas.user_schema import UserData
from app.serializers.user_serializer import UserSerializer
from app.services.base_service import BaseService
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.repositories.user_repository import UserRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.address_repository import AddressRepository
from pymongo.errors import DuplicateKeyError

from app.services.storage_service import StorageService

class UserService(BaseService):
    def __init__(self, repository: UserRepository, company_repository: CompanyRepository = None, address_repository: AddressRepository = None):
        super().__init__(repository.db)
        self.repository = repository
        self.company_repository = company_repository
        self.address_repository = address_repository

    
 


    @staticmethod
    def _serialize_user(user: dict):
        user = user.copy()

        # Remove sensitive fields
        user.pop("password", None)

        # Normalize Mongo ID
        if "_id" in user:
            user["id"] = str(user.pop("_id"))

        # Serialize datetimes
        if user.get("created_at") and isinstance(user["created_at"], datetime):
            user["created_at"] = user["created_at"].isoformat()

        if user.get("updated_at") and isinstance(user["updated_at"], datetime):
            user["updated_at"] = user["updated_at"].isoformat()

        return user

    async def create_user(self, user_data: dict, session=None):
        existing = await self.repository.find_user_conflict(user_data["username"], user_data["email"], user_data["mobile"], session=session)

        if existing:
            if existing.get("username") == user_data["username"]:
                raise AppException(
                    status_code=409,
                    message="User with this username already exists",
                    error_code="USERNAME_EXISTS",
                    field="username"
                )
            if existing.get("email") == user_data["email"]:
                raise AppException(
                    status_code=409,
                    message="User with this email already exists",
                    error_code="EMAIL_EXISTS",
                    field="email"
                )
            if existing.get("mobile") == user_data["mobile"]:
                raise AppException(
                    status_code=409,
                    message="User with this mobile number already exists",
                    error_code="MOBILE_EXISTS",
                    field="mobile"
                )
        
        try:
            # Hash the password
            user_data["password"] = PasswordHasher.hash_password(user_data["password"])
            self.timestamps(user_data, is_new=True)
            result = await self.repository.insert(user_data, session=session)
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            # This is a fallback in case of a race condition where two requests try to create a user with the same email/username/mobile at the same time.
            # The unique index in MongoDB will prevent the duplicate and raise this error.
            error_msg = str(e)

            if "username" in error_msg:
                raise AppException(
                    status_code=409,
                    message="User with this username already exists",
                    error_code="USERNAME_EXISTS",
                    field="username"
                )

            if "email" in error_msg:
                raise AppException(
                    status_code=409,
                    message="User with this email already exists",
                    error_code="EMAIL_EXISTS",
                    field="email"
                )

            if "mobile" in error_msg:
                raise AppException(
                    status_code=409,
                    message="User with this mobile number already exists",
                    error_code="MOBILE_EXISTS",
                    field="mobile"
                )

            raise

    async def get_user(self, user_id: str, session=None):
        user = await self.repository.find_by_id(user_id, session=session)
        if not user:
            raise AppException(404, "User not found")

        return self._serialize_user(user)

    async def update_user(self, user_id: str, update_data: dict, session=None):
        if not update_data:
            raise AppException(400, "No fields provided for update")

        # Unique email check
        if "email" in update_data:
            existing = await self.repository.find_by_email_excluding_id(
                update_data["email"], user_id
            )
            if existing:
                raise AppException(400, "Email already exists")

        # Hash password if present
        if "password" in update_data:
            update_data["password"] = PasswordHasher.hash_password(
                update_data["password"]
            )

        self.timestamps(update_data)

        result = await self.repository.update_by_id(user_id, update_data, session=session)

        if result.matched_count == 0:
            raise AppException(404, "User not found")

        # return minimal / updated entity (no company, no storage)
        return await self.get_user(user_id)

    async def authenticate_user(self, email: str, password: str):
        user = await self.repository.find_by_email(email)
        if not user:
            return None
        
        if not PasswordHasher.verify_password(password, user["password"]):
            return None
        
        return self._serialize_user(user)
    
    async def get_users(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "first_name",
        sort_order: str = "asc",
        search: dict = None,
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

        users_cursor = self.repository.collection.find(query).sort(sort_by, sort_direction).skip(skip).limit(size)
        total = await self.repository.count_documents(query)
        items = []
        async for doc in users_cursor:
            items.append(self._serialize_user(doc))
        return {
           "total": total,
            "page": page,
            "size": size,
            "items": items
        }
    

    def _serialize_user(self, user: dict) -> dict:
            user = user.copy()

            if "_id" in user:
                user["id"] = str(user.pop("_id"))

            return user
    


    async def list_users(
        self,
        query: UserQuery,
        session=None
    ) :
        await self.validate_pagination(query.page, query.size)
        filters = await self.build_query_filters(query.filters)
        skip = (query.page - 1) * query.size
        sort_direction = 1 if query.sort_order.lower() == "asc" else -1
        self.user_serializer = UserSerializer()

        cursor = (
                self.repository
                .find_many(filters, session=session)
                .sort(query.sort_by, sort_direction)
                .skip(skip)
                .limit(query.size)
            )
        

        
        total = await self.repository.count_documents( filters, session=session)
        items = []
        async for doc in cursor:
            items.append(self.user_serializer.serialize(doc))
        
        return {
            "total": total,
            "page": query.page,
            "size": query.size,
            "items": items
        }

        
