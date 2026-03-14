from fastapi import Depends, Request
from app.core.database import get_database
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.services.location_service import LocationService
from app.services.storage_service import StorageService
from app.core.security import JWTHandler
from app.core.config import settings
from app.core.exceptions import AppException


def get_user_service(db=Depends(get_database)):
    return UserService(db)


def get_token_service(db=Depends(get_database)):
    return TokenService(db)



def get_current_user(request: Request) -> str:
    """Dependency that returns the current user id (sub) from an access token.

    Accepts `Authorization: Bearer <token>` or cookie `access_token`.
    """
    auth = request.headers.get("Authorization")
    token = None
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
    else:
        token = request.cookies.get("access_token")

    if not token:
        raise AppException(401, "Authorization token missing")

    try:
        payload = JWTHandler.decode_token(token)
        if payload.get("type") != "access":
            raise AppException(401, "Invalid token type")
        return payload.get("sub")
    except Exception as e:
        raise AppException(401, f"Invalid or expired token: {str(e)}")
    


def get_location_service(db=Depends(get_database)):
    return LocationService(db)


def get_storage_service():
    return StorageService()