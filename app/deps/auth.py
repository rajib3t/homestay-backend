"""Authentication and security dependencies."""
import logging
from dataclasses import dataclass
from fastapi import Request
from app.core.security import JWTHandler
from app.core.exceptions import AppException, TokenExpiredError, TokenInvalidError

logger = logging.getLogger(__name__)

ACCESS_TOKEN_COOKIE_NAME = "access_token"


@dataclass
class CurrentUser:
    id: str
    user_type: str  # was: role


def _extract_token(request: Request) -> str | None:
    """Extract a bearer token from the Authorization header or cookie."""
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1]
    return request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)


def get_current_user(request: Request) -> CurrentUser:
    """Dependency that returns the current user from an access token.

    Accepts `Authorization: Bearer <token>` or cookie `access_token`.

    Raises:
        AppException(401): If token is missing, invalid, expired, or lacks required claims.
    """
    token = _extract_token(request)

    if not token:
        logger.warning("Auth failure [%s]: no token provided", request.url.path)
        raise AppException(401, "Authorization token missing", error_code="TOKEN_MISSING")

    try:
        payload = JWTHandler.decode_token(token)
    except TokenExpiredError:
        logger.warning("Auth failure [%s]: token expired", request.url.path)
        raise AppException(401, "Token has expired", error_code="TOKEN_EXPIRED")
    except TokenInvalidError as e:
        logger.warning("Auth failure [%s]: invalid token — %s", request.url.path, str(e))
        raise AppException(401, "Invalid token", error_code="TOKEN_INVALID")

    token_type = payload.get("type")
    if token_type != "access":
        logger.warning(
            "Auth failure [%s]: wrong token type '%s'", request.url.path, token_type
        )
        raise AppException(
            401,
            f"Expected access token, got '{token_type}'",
            error_code="TOKEN_WRONG_TYPE",
        )

    sub = payload.get("sub")
    role = payload.get("user_type")  # was: role

    if not sub:
        logger.warning("Auth failure [%s]: missing 'sub' claim", request.url.path)
        raise AppException(401, "Token missing subject claim", error_code="TOKEN_MISSING_SUB")

    if not role:
        logger.warning("Auth failure [%s]: missing 'role' claim", request.url.path)
        raise AppException(401, "Token missing role claim", error_code="TOKEN_MISSING_ROLE")

    return CurrentUser(id=sub, user_type=role)