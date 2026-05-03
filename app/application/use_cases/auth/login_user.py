# app/application/use_cases/auth/login_user.py

from datetime import datetime, timedelta, timezone
from app.core.exceptions import AppException
from app.core.security import JWTHandler


class LoginUserUseCase:

    def __init__(self, user_service, token_service):
        self.user_service = user_service
        self.token_service = token_service

    async def execute(self, email: str, password: str):
        user = await self.user_service.authenticate_user(email, password)

        if not user:
            raise AppException(401, "Incorrect email or password")

        # Access token
        access_token = JWTHandler.create_access_token(
            data={"sub": str(user["_id"])},
            additional_claims={
                "email": user["email"],
                "user_type": user["user_type"]
            }
        )

        now = datetime.now(timezone.utc)

        # Refresh token
        refresh_token = await self.token_service.create_token(
            identity=str(user["_id"]),
            additional_claims={
                "email": user["email"],
                "user_type": user["user_type"]
            },
            expires_at=now + timedelta(days=7),
            absolute_expiry=now + timedelta(days=30)
        )

        return user, access_token, refresh_token