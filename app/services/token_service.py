from app.services.base_service import BaseService
from app.models.token_model import Token, TokenType
from app.core.security import JWTHandler
from datetime import datetime
from bson import ObjectId

class TokenService(BaseService):

    async def create_token(self, identity: str, additional_claims: dict = None):
        """Creates a refresh token and saves it to the database."""
        token_string, expires_at = JWTHandler.create_refresh_token(
            data={"sub": identity},
            additional_claims=additional_claims
        )
        
        token_obj = Token(
            user_id=identity,
            token=token_string,
            token_type=TokenType.REFRESH,
            expires_at=expires_at,
            additional_claims=additional_claims
        )
        
        await self.db[Token.COLLECTION_NAME].insert_one(token_obj.to_mongo_dict())
        return token_obj

    async def verify_token(self, token_string: str):
        """Verifies if a refresh token is valid and not revoked."""
        try:
            # Decode to check basic validity and expiration
            payload = JWTHandler.decode_token(token_string)
            if payload.get("type") != "refresh":
                return False, None, "Invalid token type"
            
            # Check database for revocation
            doc = await self.db[Token.COLLECTION_NAME].find_one({"token": token_string})
            if not doc:
                return False, None, "Token not found"
            
            token_obj = Token.from_mongo_doc(doc)
            if token_obj.is_revoked:
                return False, None, "Token has been revoked"
            
            if token_obj.expires_at < datetime.utcnow():
                return False, None, "Token has expired"
            
            return True, token_obj, None
        except Exception as e:
            return False, None, str(e)

    async def revoke_token(self, token_string: str):
        """Revokes a refresh token."""
        await self.db[Token.COLLECTION_NAME].update_one(
            {"token": token_string},
            {"$set": {"is_revoked": True}}
        )
