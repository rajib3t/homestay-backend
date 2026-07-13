from fastapi import APIRouter, Depends
from app.middleware.idempotency_route import IdempotencyRoute
from app.api.base_controller import BaseController
from app.models.app_setting_model import AppSetting
from app.schemas.app_setting_schema import AppSettingResponse
from app.utils.exception_decorate import handle_api_exceptions
from app.application.use_cases.setting.app_setting import (
    GetAppSettingUseCase,
    PostAppSettingUseCase,
)
from app.deps.app_setting import (
    get_get_app_setting,
    get_post_app_setting,
)

class AppSettingController(BaseController):
    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/setting",
            tags=["Setting"],
            route_class=IdempotencyRoute,
        )

        self.register_routes()

    def register_routes(self):
        routes = [
            ("get", "", self.get_app_settings, {"response_model": AppSettingResponse, "response_model_by_alias": False}),
            ("patch", "", self.post_app_settings, {"response_model": AppSettingResponse, "response_model_by_alias": False}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def get_app_settings(
        self,
        use_case: GetAppSettingUseCase = Depends(get_get_app_setting),
    ):
        setting = await use_case.execute()
        return self.build_response("App setting", setting)


    @handle_api_exceptions
    async def post_app_settings(
        self,
        data: AppSetting,
        use_case: PostAppSettingUseCase = Depends(get_post_app_setting),
    ):
        setting = await use_case.execute(data)
        return self.build_response("Update setting", setting)

controller = AppSettingController()
router = controller.router