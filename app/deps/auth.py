"""Authentication and security dependencies."""
import logging
from dataclasses import dataclass
from typing import Optional, Union
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import JWTHandler
from app.core.exceptions import AppException, TokenExpiredError, TokenInvalidError
from app.models.user_model import UserType

logger = logging.getLogger(__name__)

ACCESS_TOKEN_COOKIE_NAME = "access_token"
security = HTTPBearer(auto_error=False)

@dataclass
class CurrentUser:
    id: str
    user_type: str  # was: role


def _extract_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    request: Request,
) -> Optional[str]:
    if credentials:
        return credentials.credentials

    return request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)


def get_current_user(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    ) -> CurrentUser:
    """Dependency that returns the current user from an access token.

    Accepts `Authorization: Bearer <token>` or cookie `access_token`.

    Raises:
        AppException(401): If token is missing, invalid, expired, or lacks required claims.
    """
    token = _extract_token(credentials, request)

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



async def require_role(current_user: CurrentUser = Depends(get_current_user), required_roles: list[UserType] = None):
    """Dependency that checks if the current user has one of the required roles.
    
    Args:
        current_user: The current authenticated user
        required_roles: List of allowed roles. If None, allows all authenticated users.
        
    Raises:
        AppException(403): If user doesn't have required role
    """
    if required_roles is None:
        return current_user
    
    user_role = current_user.user_type
    
    # Convert UserType enum to string if needed
    if isinstance(user_role, UserType):
        user_role = user_role.value
    
    allowed_roles = [role.value if isinstance(role, UserType) else role for role in required_roles]
    
    if user_role not in allowed_roles:
        logger.warning(
            "Access denied [%s]: user %s with role '%s' tried to access endpoint requiring roles: %s",
            "unknown", current_user.public_id, user_role, allowed_roles
        )
        raise AppException(
            403,
            f"Access denied. Required role: one of {allowed_roles}",
            error_code="INSUFFICIENT_PERMISSIONS"
        )
    
    return current_user


async def require_admin(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires superadmin role."""
    return await require_role(current_user, [UserType.ADMIN])

async def require_vendor(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires vendor role."""
    return await require_role(current_user, [UserType.VENDOR])

async def require_user(current_user: CurrentUser = Depends(get_current_user)):
    """Dependency that requires user role."""
    return await require_role(current_user, [UserType.USER])