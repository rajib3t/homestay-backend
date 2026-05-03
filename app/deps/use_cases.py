"""Use case dependency factories."""
from fastapi import Depends
from app.application.use_cases.auth.login_user import LoginUserUseCase
from app.application.use_cases.auth.refresh_token import RefreshTokenUseCase
from app.application.use_cases.users.get_user import GetUserUseCase
from app.application.use_cases.users.create_user import CreateUserUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.deps.services import (
    get_token_service,
    get_user_service,
    get_company_service,
    get_address_service,
    get_storage_service,
)
from app.deps.events import get_event_bus

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
    event_bus=Depends(get_event_bus)
):
    """Get the create user use case."""
    return CreateUserUseCase(user_service, event_bus)


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
):
    """Get the update user use case."""
    return UpdateUserUseCase(
        user_service,
        company_service,
        address_service,
    )


