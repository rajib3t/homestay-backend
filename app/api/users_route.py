

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from app.application.use_cases.users.update_profile_image import UpdateUserProfileImageUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.deps.use_cases import get_update_profile_image_use_case, get_update_user_use_case
from app.middleware.idempotency_route import IdempotencyRoute
from app.api.base_controller import BaseController
from app.models.user_model import ListUsers, UserCreate, UserPasswordUpdate, UserProfileImageUpdate, UserUpdate
from app.schemas.user_schema import ProfileResponse, UsersResponse, UserResponse
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.services.company_service import CompanyService
from app.services.address_service import AddressService
from app.services.email_service import BaseEmailService
from app.utils.api_utils import replace_data_url_asset
from app.utils.exception_decorate import handle_api_exceptions
from app.deps import get_storage_service, get_user_service,  get_current_user, get_create_user_use_case
from app.application.use_cases.users.create_user import CreateUserUseCase
from app.deps.auth import CurrentUser
from app.deps.user_use import get_list_users_use_case, get_list_params, get_single_user_use_case
from app.application.use_cases.users.user import GetUsersUseCase, GetUserUseCase
from app.application.dto.user import UserQuery

import logging
def _pagination_meta(r):
    return {"total": r["total"], "page": r["page"], "size": r["size"]}

class UserController(BaseController):
    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/users",
            tags=["Users"],
            route_class=IdempotencyRoute,
        )
        self.register_routes()

    def register_routes(self):
        routes = [
            # Routes will be added here in the future
            ("post",  "/", self.create_user, {"response_model": ProfileResponse, "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/", self.list_users, {"response_model": UsersResponse, "response_model_by_alias": False}),
            ("get",   "/{user_id}", self.get_user, {"response_model": UserResponse, "response_model_by_alias": False}),  
            ("put",   "/{user_id}", self.update_user, {"response_model": UserResponse, "response_model_by_alias": False}),
            ("put",   "/{user_id}/profile-image", self.update_profile_image, {"response_model": UserResponse, "response_model_by_alias": False}),
            ("put",   "/{user_id}/password", self.update_user_password, {"response_model": UserResponse, "response_model_by_alias": False}),

        ]

        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)
        
    @handle_api_exceptions
    async def create_user(
            self,
            
            data: UserCreate,
            current_user: CurrentUser = Depends(get_current_user),
            use_case: CreateUserUseCase = Depends(get_create_user_use_case)
):      
        
        create_payload = data.model_dump()
        create_payload["created_by"] = current_user.id
        user = await use_case.execute(create_payload)
        return self.build_response("User created", user)
    
    @handle_api_exceptions
    async def list_users(
        self,
        params:  ListUsers= Depends(get_list_params),
        use_case : GetUsersUseCase= Depends(get_list_users_use_case)
        
    ):
        search = self.build_search(
            
            email=params.email,
            user_type=params.user_type,
            first_name=params.first_name,
            last_name=params.last_name,
            mobile=params.mobile
        )
        result = await use_case.execute(
            UserQuery(
                page=params.page,
                size=params.size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                filters=search,
            )
            
        )
        return self.build_response("Users list", data=result["items"], meta=_pagination_meta(result))

    @handle_api_exceptions
    async def get_user(
        self,
        user_id: str,
        use_case: GetUserUseCase = Depends(get_single_user_use_case)
    ):
        user = await use_case.execute(user_id)
        return self.build_response("User", user)
    

    @handle_api_exceptions
    async def update_profile_image(
        self,
        user_id: str,
        data: UserProfileImageUpdate,
        current_user: CurrentUser = Depends(get_current_user),
        use_case: UpdateUserProfileImageUseCase = Depends(get_update_profile_image_use_case)
    ):
        result = await use_case.execute(user_id, data.image)
        return self.build_response("Profile image updated", result)

    @handle_api_exceptions
    async def update_user_password(
        self,
        user_id: str,
        data: UserPasswordUpdate,
        current_user: CurrentUser = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        await service.update_user(user_id, {"password": data.new_password})
        user_data = await service.get_user(user_id, storage=storage_service)
        return self.build_response("Password updated", user_data)
       
    @handle_api_exceptions
    async def update_user(
        self,
        user_id: str,
        data: UserUpdate,
        current_user: CurrentUser = Depends(get_current_user),
        use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
    ):
        update_payload = data.model_dump(exclude_unset=True)
        update_payload["updated_by"] = current_user.id
        user = await use_case.execute(user_id, update_payload)
        return self.build_response("User updated", user)

user_controller = UserController()
router = user_controller.router