from datetime import datetime, timezone

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.repositories.user_repository import UserRepository
from app.models.user_model import UserType


class AdminUserSeeder:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def seed(self) -> dict:
        username = (settings.ADMIN_USER_USERNAME or "").strip().lower()
        email = (settings.ADMIN_USER_EMAIL or "").strip().lower()
        password = settings.ADMIN_USER_PASSWORD or ""
        mobile = (settings.ADMIN_USER_MOBILE or "").strip()

        if not username or not email or not password or not mobile:
            raise AppException(
                status_code=400,
                message=(
                    "Admin seed requires ADMIN_USER_USERNAME, ADMIN_USER_EMAIL, "
                    "ADMIN_USER_PASSWORD, and ADMIN_USER_MOBILE"
                ),
                error_code="ADMIN_SEED_CONFIG_INVALID",
            )

        existing = await self.user_repository.find_by_email(email)
        if existing:
            return {"created": False, "reason": "Admin user already exists"}

        now = datetime.now(timezone.utc)
        admin_user = {
            "username": username,
            "email": email,
            "password": PasswordHasher.hash_password(password),
            "user_type": UserType.ADMIN.value,
            "first_name": settings.ADMIN_USER_FIRST_NAME,
            "last_name": settings.ADMIN_USER_LAST_NAME,
            "mobile": mobile,
            "image": None,
            "created_at": now,
            "updated_at": now,
        }

        result = await self.user_repository.insert(admin_user)
        return {"created": True, "inserted_id": str(result.inserted_id)}
