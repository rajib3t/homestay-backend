

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.application.use_cases.users.get_user import GetUserUseCase
from app.application.use_cases.users.update_user import UpdateUserUseCase
from app.deps.use_cases import get_update_user_use_case
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
from app.deps import get_storage_service, get_user_service,  get_current_user, get_create_user_use_case, get_user_use_case
from app.application.use_cases.users.create_user import CreateUserUseCase
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
            current_user: str = Depends(get_current_user),
            use_case: CreateUserUseCase = Depends(get_create_user_use_case)
):
        user = await use_case.execute(data.model_dump())
        return self.build_response("User created", user)
    
    @handle_api_exceptions
    async def list_users(
        self,
        params:  ListUsers= Depends(),
        current_user: str = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
        
    ):
        search = self.build_search(
            username=params.username,
            email=params.email,
            user_type=params.user_type,
            first_name=params.first_name,
            last_name=params.last_name,
            mobile=params.mobile
        )
        result = await service.get_users(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
            
        )
        return self.build_response("Users list", data=result["items"], meta=_pagination_meta(result))

    @handle_api_exceptions
    async def get_user(
        self,
        user_id: str,
        current_user: str = Depends(get_current_user),
        use_case: GetUserUseCase = Depends(get_user_use_case)
    ):
        user = await use_case.execute(user_id, include_company=True)
        return self.build_response("User", user)
    

    @handle_api_exceptions
    async def update_profile_image(
        self,
        user_id:str,
        data: UserProfileImageUpdate,
        current_user: str = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
        storage_service : StorageService = Depends(get_storage_service)
    ) : 
        
        payload = data.model_dump()
        image = payload.get("image")

        if image is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is required")
        
        if isinstance(image, str) and image.startswith("data:"):
            existing_user = await service.get_user(user_id)
            if existing_user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            
            old_image = existing_user.get("image") if existing_user.get("image") else None
            payload['image'] = await replace_data_url_asset(
                storage_service,
                image,
                "profile_images",
                user_id,
                old_key=old_image
            )
                
        await service.update_user(user_id, {"image": payload['image']})
        updated_user = await service.get_user(user_id, storage=storage_service)
        return self.build_response("Profile image updated", updated_user)

    @handle_api_exceptions
    async def update_user_password(
        self,
        user_id: str,
        data: UserPasswordUpdate,
        current_user: str = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
    ):
        await service.update_user(user_id, {"password": data.new_password})
        user_data = await service.get_user(user_id)
        return self.build_response("Password updated", user_data)
       
    @handle_api_exceptions
    async def update_user(
        self,
        user_id: str,
        data: UserUpdate,
        use_case: UpdateUserUseCase = Depends(get_update_user_use_case)
    ):
        user = await use_case.execute(user_id, data.model_dump(exclude_unset=True))
        return self.build_response("User updated", user)

user_controller = UserController()
router = user_controller.router