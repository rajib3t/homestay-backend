from datetime import datetime
from typing import Optional

from app.schemas.user_schema import UserData
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
        user.pop("password", None)
        user["_id"] = str(user["_id"])

        if user.get("created_at") and isinstance(user.get("created_at"), datetime):
            user["created_at"] = user["created_at"].isoformat()

        if user.get("updated_at") and isinstance(user.get("updated_at"), datetime):
            user["updated_at"] = user["updated_at"].isoformat()

        return user

    async def create_user(self, user_data: dict):
        existing = await self.repository.find_user_conflict(user_data["username"], user_data["email"], user_data["mobile"])

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
            result = await self.repository.insert(user_data)
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

    async def get_user(self, user_id: str, storage: Optional[StorageService] = None, include_company: bool = True)-> UserData:
        user = await self.repository.find_by_id(user_id)
        if not user:
            raise AppException(404, "User not found")

        if user.get("image") and storage:
            user["image"] =  storage.generate_presigned_url(user["image"])

        serialized = self._serialize_user(user)

        # Include company data if requested and available
        if include_company and self.company_repository:
            company = await self.company_repository.find_by_user_id(user_id)
            if company:
                company = company.copy()
                company["id"] = str(company.pop("_id"))

                # Format timestamps
                if company.get("created_at") and isinstance(company.get("created_at"), datetime):
                    company["created_at"] = company["created_at"].isoformat()
                if company.get("updated_at") and isinstance(company.get("updated_at"), datetime):
                    company["updated_at"] = company["updated_at"].isoformat()

                # Include address if available
                if self.address_repository:
                    address = await self.address_repository.find_by_company_id(company["id"])
                    if address:
                        address = address.copy()
                        address["id"] = str(address.pop("_id"))
                        if address.get("created_at") and isinstance(address.get("created_at"), datetime):
                            address["created_at"] = address["created_at"].isoformat()
                        if address.get("updated_at") and isinstance(address.get("updated_at"), datetime):
                            address["updated_at"] = address["updated_at"].isoformat()
                        address.pop("company_id", None)
                        address.pop("user_id", None)
                        company["address"] = address

                serialized["company"] = company

        return serialized

    async def update_user(self, user_id: str, update_data: dict, storage_service : StorageService = None):
        if not update_data:
            raise AppException(400, "No fields provided for update")
        
        # Check if email is being updated and if it's already taken
        if "email" in update_data:
            existing = await self.repository.find_by_email_excluding_id(update_data["email"], user_id)
            if existing:
                raise AppException(400, "Email already exists")

        if storage_service and "image" in update_data:
            # If the image is being updated, we can handle the upload to storage here
            image_url = await storage_service.upload_bytes(update_data["image"], f"profile_images/{user_id}.jpg")
            update_data["image"] = image_url
        if "password" in update_data:
            update_data["password"] = PasswordHasher.hash_password(update_data["password"])
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
    

    