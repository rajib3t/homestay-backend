"""Authentication and security dependencies."""
from fastapi import Request
from app.core.security import JWTHandler
from app.core.exceptions import AppException


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
    except Exception:
        raise AppException(401, "Invalid or expired token")
