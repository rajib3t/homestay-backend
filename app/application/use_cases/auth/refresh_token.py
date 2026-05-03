# app/application/use_cases/auth/refresh_token.py

from datetime import datetime, timedelta, timezone
from app.core.exceptions import AppException
from app.core.security import JWTHandler


class RefreshTokenUseCase:

    def __init__(self, token_service):
        self.token_service = token_service

    async def execute(self, refresh_token: str):

        is_valid, token_obj, error = await self.token_service.verify_token(refresh_token)

        if not is_valid:
            raise AppException(401, error or "Invalid refresh token")

        now = datetime.now(timezone.utc)

        # Expiry checks
        if token_obj.absolute_expiry and now > token_obj.absolute_expiry:
            raise AppException(401, "Session expired")

        if token_obj.expires_at and now > token_obj.expires_at:
            raise AppException(401, "Session idle timeout")

        # Rotate token
        await self.token_service.revoke_token(refresh_token)

        new_access = JWTHandler.create_access_token(
            data={"sub": str(token_obj.user_id)},
            additional_claims=token_obj.additional_claims
        )

        new_refresh = await self.token_service.create_token(
            identity=str(token_obj.user_id),
            additional_claims=token_obj.additional_claims,
            expires_at=now + timedelta(days=7),
            absolute_expiry=token_obj.absolute_expiry
        )

        return new_access, new_refresh