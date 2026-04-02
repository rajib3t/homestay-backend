from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.middleware.idempotency_route import IdempotencyRoute
from app.api.base_controller import BaseController
from app.models.user_model import ListUsers, UserCreate
from app.schemas.user_schema import ProfileResponse, UsersResponse
from app.services.user_service import UserService
from app.services.email_service import BaseEmailService
from app.utils.exception_decorate import handle_api_exceptions
from app.deps import get_user_service, get_email_service

_PAGINATION_META = lambda r: {"total": r["total"], "page": r["page"], "size": r["size"]}

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

        ]

        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)
        
    @handle_api_exceptions
    async def create_user(
        self,
        data:UserCreate,
        background_tasks: BackgroundTasks,
        user_service: UserService = Depends(get_user_service),
        email_service: BaseEmailService = Depends(get_email_service)
    ):
    
        user_id =  await user_service.create_user(data.model_dump())
        user = await user_service.get_user(user_id)
        
        # Add email sending to background tasks
        background_tasks.add_task(email_service.send_welcome_email, to_email=data.email, username=data.username)
        
        return self.build_response("User created", user)
    
    @handle_api_exceptions
    async def list_users(
        self,
        params:  ListUsers= Depends(),
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
        return self.build_response("Users list", data=result["items"], meta=_PAGINATION_META(result))

user_controller = UserController()
router = user_controller.router