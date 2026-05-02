from fastapi import APIRouter, Depends
from app.middleware.idempotency_route import IdempotencyRoute
from app.api.base_controller import BaseController
from app.models.company_model import CompanyCreate, CompanyUpdate
from app.schemas.company_schema import CompanyResponse
from app.services.company_service import CompanyService
from app.utils.exception_decorate import handle_api_exceptions
from app.deps import get_company_service, get_current_user


class CompanyController(BaseController):
    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/companies",
            tags=["Companies"],
            route_class=IdempotencyRoute,
        )
        self.register_routes()

    def register_routes(self):
        routes = [
            ("post", "/", self.create_company, {"response_model": CompanyResponse, "response_model_by_alias": False, "status_code": 201}),
            ("get", "/{company_id}", self.get_company, {"response_model": CompanyResponse, "response_model_by_alias": False}),
            ("get", "/user/{user_id}", self.get_company_by_user, {"response_model": CompanyResponse, "response_model_by_alias": False}),
            ("put", "/{company_id}", self.update_company, {"response_model": CompanyResponse, "response_model_by_alias": False}),
        ]

        for method, path, handler, kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **kwargs)

    @handle_api_exceptions
    async def create_company(
        self,
        data: CompanyCreate,
        current_user: str = Depends(get_current_user),
        company_service: CompanyService = Depends(get_company_service),
    ):
        company_id = await company_service.create_company(data.model_dump())
        company = await company_service.get_company(company_id)
        return self.build_response("Company created", company)

    @handle_api_exceptions
    async def get_company(
        self,
        company_id: str,
        current_user: str = Depends(get_current_user),
        company_service: CompanyService = Depends(get_company_service),
    ):
        company = await company_service.get_company(company_id)
        return self.build_response("Company", company)

    @handle_api_exceptions
    async def get_company_by_user(
        self,
        user_id: str,
        current_user: str = Depends(get_current_user),
        company_service: CompanyService = Depends(get_company_service),
    ):
        company = await company_service.get_company_by_user_id(user_id)
        return self.build_response("Company", company)

    @handle_api_exceptions
    async def update_company(
        self,
        company_id: str,
        data: CompanyUpdate,
        current_user: str = Depends(get_current_user),
        company_service: CompanyService = Depends(get_company_service),
    ):
        await company_service.update_company(company_id, data.model_dump(exclude_unset=True))
        updated_company = await company_service.get_company(company_id)
        return self.build_response("Company updated", updated_company)


company_controller = CompanyController()
router = company_controller.router
