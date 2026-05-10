"""Use case dependency factories."""
from fastapi import Depends
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from app.application.use_cases.users.get_user import GetUserUseCase
from app.application.use_cases.users.create_user import CreateUserUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.application.use_cases.locations.create_city import CreateCityUseCase
from app.deps.services import get_location_service, get_storage_service
from app.deps.services import (
    get_token_service,
    get_user_service,
    get_company_service,
    get_address_service,
    get_storage_service,
)
from app.deps.events import get_event_bus
from app.deps.auth import get_current_user
from app.application.use_cases.users.update_profile_image import UpdateUserProfileImageUseCase
from app.deps.uow import get_uow
from app.infrastructure.event_bus import event_bus

# app/deps/use_cases.py

def get_login_use_case(
    user_service=Depends(get_user_service),
    token_service=Depends(get_token_service),
):
    return LoginUserUseCase(user_service, token_service)


def get_refresh_use_case(
    token_service=Depends(get_token_service),
):
    return RefreshTokenUseCase(token_service)
def get_create_user_use_case(
    user_service=Depends(get_user_service),
    uow=Depends(get_uow),
):
    return CreateUserUseCase(
        user_service=user_service,
        uow=uow,
    )


def get_user_use_case(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    address_service=Depends(get_address_service),
    storage_service=Depends(get_storage_service),
):
    """Get the get user use case."""
    return GetUserUseCase(
        user_service,
        company_service,
        address_service,
        storage_service,
    )

def get_update_user_use_case(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    address_service=Depends(get_address_service),
    storage_service=Depends(get_storage_service),
    uow=Depends(get_uow),
):
    return UpdateUserUseCase(
        user_service,
        company_service,
        address_service,
        storage_service,
        uow,
    )


def get_create_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user=Depends(get_current_user),
):
    return CreateCityUseCase(service, storage, current_user)

def get_update_profile_image_use_case(
    user_service=Depends(get_user_service),
    storage_service=Depends(get_storage_service),
):
    return UpdateUserProfileImageUseCase(user_service, storage_service)