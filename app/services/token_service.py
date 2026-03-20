from app.services.base_service import BaseService
from app.models.token_model import Token, TokenType
from app.core.security import JWTHandler
from datetime import datetime, timezone
from app.repositories.token_repository import TokenRepository

class TokenService(BaseService):
    def __init__(self, repository: TokenRepository):
        super().__init__(repository.db)
        self.repository = repository

    async def create_token(self, identity: str, additional_claims: dict = None, expires_at=None, absolute_expiry=None):
        """Creates a refresh token and saves it to the database.

        If `expires_at` is provided, it's used for the JWT `exp` claim and
        returned expiry. `absolute_expiry` is stored on the token for absolute session expiry checks.
        """
        token_string, token_expiry = JWTHandler.create_refresh_token(
            data={"sub": identity},
            additional_claims=additional_claims,
            expires_at=expires_at
        )

        token_obj = Token(
            user_id=identity,
            token=token_string,
            token_type=TokenType.REFRESH,
            expires_at=token_expiry,
            absolute_expiry=absolute_expiry,
            additional_claims=additional_claims
        )

        await self.repository.insert(token_obj.to_mongo_dict())
        return token_obj

    async def verify_token(self, token_string: str):
        """Verifies if a refresh token is valid and not revoked."""
        try:
            # Decode to check basic validity and expiration
            payload = JWTHandler.decode_token(token_string)
            if payload.get("type") != "refresh":
                return False, None, "Invalid token type"
            
            # Check database for revocation
            doc = await self.repository.find_by_token(token_string)
            if not doc:
                return False, None, "Token not found"
            
            token_obj = Token.from_mongo_doc(doc)
            if token_obj.is_revoked:
                return False, None, "Token has been revoked"
            
            if token_obj.expires_at < datetime.now(timezone.utc):
                return False, None, "Token has expired"
            
            return True, token_obj, None
        except Exception as e:
            return False, None, str(e)

    async def revoke_token(self, token_string: str):
        """Revokes a refresh token."""
        await self.repository.revoke(token_string)
