from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from datetime import datetime, timedelta, timezone
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.models.user_model import UserCreate
from app.schemas.user_schema import LoginRequest, RegistrationResponse, LoginResponse, RefreshResponse
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.deps import get_user_service, get_token_service
from app.core.security import JWTHandler
from app.core.config import settings
from app.middleware.idempotency_route import IdempotencyRoute
from app.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from app.deps.use_cases import get_login_use_case, get_refresh_use_case
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
@router.post("/login")
async def login(
    login_data: LoginRequest,
    response: Response,
    use_case: LoginUserUseCase = Depends(get_login_use_case)
):
    user, access_token, refresh_token = await use_case.execute(
        login_data.email,
        login_data.password
    )

    response.set_cookie("access_token", access_token, httponly=True)
    response.set_cookie("refresh_token", refresh_token.token, httponly=True)

    return {
        "status": "success",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token.token,
            "user": user
        }
    }

@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    use_case: RefreshTokenUseCase = Depends(get_refresh_use_case)
):
    body = await request.json()

    token = body.get("refresh_token") or request.cookies.get("refresh_token")


    if not token:
        raise HTTPException(401, "Refresh token missing")

    access, refresh = await use_case.execute(token)

    response.set_cookie("refresh_token", refresh.token, httponly=True)

    return {
        "status": "success",
        "data": {
            "access_token": access,
            "refresh_token": refresh.token
        }
    }


