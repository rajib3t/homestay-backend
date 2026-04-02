from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from datetime import datetime, timedelta, timezone
from app.models.user_model import UserCreate
from app.schemas.user_schema import LoginRequest, RegistrationResponse, LoginResponse, RefreshResponse
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.deps import get_user_service, get_token_service
from app.core.security import JWTHandler
from typing import Optional
from app.core.config import settings
from app.middleware.idempotency_route import IdempotencyRoute

router = APIRouter(prefix="/auth", tags=["Authentication"], route_class=IdempotencyRoute)


# SESSION CONFIG
IDLE_TIMEOUT = timedelta(days=7)
ABSOLUTE_TIMEOUT = timedelta(days=30)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def register(
    user_data: UserCreate,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service)
):

    user_id = await user_service.create_user(user_data.model_dump())
    user = await user_service.get_user(user_id)

    access_token = JWTHandler.create_access_token(
        data={"sub": str(user["_id"])},
        additional_claims={"email": user["email"], "user_type": user["user_type"]}
    )

    # create refresh token session
    now = datetime.now(timezone.utc)

    refresh_token_obj = await token_service.create_token(
        identity=str(user["_id"]),
        additional_claims={"email": user["email"], "user_type": user["user_type"]},
        expires_at=now + IDLE_TIMEOUT,
        absolute_expiry=now + ABSOLUTE_TIMEOUT
    )

    user_response = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "user_type": user["user_type"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "mobile": user["mobile"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }

    cookie_secure = settings.SECURE_COOKIES
    samesite_val = "none" if cookie_secure else "lax"

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=samesite_val
    )

    response.set_cookie(
        "refresh_token",
        refresh_token_obj.token,
        httponly=True,
        secure=cookie_secure,
        samesite=samesite_val
    )

    return {
        "status": "success",
        "message": "User registered successfully",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token_obj.token,
            "user": user_response,
        },
    }


@router.post("/login", response_model=LoginResponse, response_model_by_alias=False)
async def login(
    login_data: LoginRequest,
    response: Response,
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service)
):

    user = await user_service.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = JWTHandler.create_access_token(
        data={"sub": str(user["_id"])},
        additional_claims={"email": user["email"], "user_type": user["user_type"]}
    )

    now = datetime.now(timezone.utc)

    refresh_token_obj = await token_service.create_token(
        identity=str(user["_id"]),
        additional_claims={"email": user["email"], "user_type": user["user_type"]},
        expires_at=now + IDLE_TIMEOUT,
        absolute_expiry=now + ABSOLUTE_TIMEOUT
    )

    user_response = {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "user_type": user["user_type"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "mobile": user["mobile"],
        "created_at": user["created_at"],
        "updated_at": user["updated_at"],
    }

    cookie_secure = settings.SECURE_COOKIES
    samesite_val = "none" if cookie_secure else "lax"

    response.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=cookie_secure,
        samesite=samesite_val
    )

    response.set_cookie(
        "refresh_token",
        refresh_token_obj.token,
        httponly=True,
        secure=cookie_secure,
        samesite=samesite_val
    )

    return {
        "status": "success",
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token_obj.token,
            "user": user_response,
        },
    }


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    token_service: TokenService = Depends(get_token_service)
):

    refresh_token_string = request.cookies.get("refresh_token")

    if not refresh_token_string:
        try:
            body = await request.json()
            refresh_token_string = body.get("refresh_token")
        except Exception:
            pass

    if not refresh_token_string:
        raise HTTPException(status_code=401, detail="Refresh token is missing")

    is_valid, token_obj, error = await token_service.verify_token(refresh_token_string)

    if not is_valid:
        raise HTTPException(status_code=401, detail=error or "Invalid refresh token")

    now = datetime.now(timezone.utc)

    # Check absolute expiry
    if token_obj.absolute_expiry and now > token_obj.absolute_expiry:
        raise HTTPException(
            status_code=401,
            detail="Session expired. Please login again."
        )

    # Check idle expiry
    if token_obj.expires_at and now > token_obj.expires_at:
        raise HTTPException(
            status_code=401,
            detail="Session idle timeout. Please login again."
        )

    # Rotate refresh token
    await token_service.revoke_token(refresh_token_string)

    new_access_token = JWTHandler.create_access_token(
        data={"sub": str(token_obj.user_id)},
        additional_claims=token_obj.additional_claims
    )

    new_refresh_token_obj = await token_service.create_token(
        identity=str(token_obj.user_id),
        additional_claims=token_obj.additional_claims,
        expires_at=now + IDLE_TIMEOUT,
        absolute_expiry=token_obj.absolute_expiry
    )

    response.set_cookie(
        "refresh_token",
        new_refresh_token_obj.token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite=("none" if settings.SECURE_COOKIES else "lax"),
        max_age=7 * 24 * 60 * 60
    )

    return {
        "status": "success",
        "message": "Token refreshed successfully",
        "data": {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_obj.token,
        },
    }