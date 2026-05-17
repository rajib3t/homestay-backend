from fastapi import Depends, Query
from app.application.use_cases.users.user import GetUserUseCase, GetUsersUseCase
from app.deps.uow import get_uow
from app.deps.auth import get_current_user
from app.models.user_model import ListUsers
from app.deps.services import (
    get_address_service, 
    get_company_service, 
    get_user_service, 
    get_storage_service
)

def get_list_params(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("first_name"),
    sort_order: str = Query("desc"),
    username: str = Query(None),
    email: str = Query(None),
    user_type: str = Query(None),
    first_name: str = Query(None),
    last_name: str = Query(None),
    mobile: str = Query(None)
) -> ListUsers:
    return ListUsers(
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order,
        username=username,
        email=email,
        user_type=user_type,
        first_name=first_name,
        last_name=last_name,
        mobile=mobile
    )




def get_list_users_use_case(
    user_service=Depends(get_user_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetUsersUseCase(
        user_service=user_service,
        storage_service=storage_service,
        current_user=current_user,
        uow=uow
    )

def get_single_user_use_case(
    user_service=Depends(get_user_service),
    company_service=Depends(get_company_service),
    address_service=Depends(get_address_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetUserUseCase(
        user_service=user_service,
        company_service=company_service,
        address_service=address_service,
        storage_service=storage_service,
        current_user=current_user,
        uow=uow
    )