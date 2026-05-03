# app/application/use_cases/auth/register_user.py

from app.api.auth_route import ABSOLUTE_TIMEOUT, IDLE_TIMEOUT
from app.core.security import JWTHandler
from datetime import datetime, timedelta, timezone

class RegisterUserUseCase:

    def __init__(self, user_service, token_service):
        self.user_service = user_service
        self.token_service = token_service

    async def execute(self, data: dict):
        user_id = await self.user_service.create_user(data)
        user = await self.user_service.get_user(user_id)

        access_token = JWTHandler.create_access_token(
            data={"sub": str(user["_id"])},
            additional_claims={
                "email": user["email"],
                "user_type": user["user_type"]
            }
        )

        now = datetime.now(timezone.utc)

        refresh_token = await self.token_service.create_token(
            identity=str(user["_id"]),
            additional_claims={
                "email": user["email"],
                "user_type": user["user_type"]
            },
            expires_at=now + IDLE_TIMEOUT,
            absolute_expiry=now + ABSOLUTE_TIMEOUT
        )

        return user, access_token, refresh_token