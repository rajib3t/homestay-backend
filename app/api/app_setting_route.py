from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.application.use_cases.setting.coming_soon_use_case import GetComingSoonSettingUseCase, PostComingSoonSettingUseCase
from app.core.exceptions import AppException
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
    get_coming_soon_setting,
    get_post_coming_soon_setting,
)


ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_MIME_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-m4v"}


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
            ("get", "/coming-soon", self.get_coming_soon_setting, {"response_model": dict, "response_model_by_alias": False}),
            ("patch", "/coming-soon", self.post_coming_soon_setting, {"response_model": dict, "response_model_by_alias": False}),
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
    

    @handle_api_exceptions
    async def get_coming_soon_setting(
        self,
        use_case: GetComingSoonSettingUseCase = Depends(get_coming_soon_setting),
    ):
        setting = await use_case.execute()
        return self.build_response("Coming soon setting", setting)

    @handle_api_exceptions
    async def post_coming_soon_setting(
        self,
        background_image_url: UploadFile | None = File(None),
        video_url: UploadFile | None = File(None),
        launch_date: str | None = Form(None),
        use_case: PostComingSoonSettingUseCase = Depends(get_post_coming_soon_setting),
    ):
        if background_image_url and background_image_url.content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise AppException(
                status_code=400, 
                message="Invalid image format. Allowed formats: JPEG, JPG, PNG, WEBP, GIF",
                error_code="INVALID_IMAGE_FORMAT"
                )

        if video_url and video_url.content_type not in ALLOWED_VIDEO_MIME_TYPES:
            raise AppException(status_code=400, message="Invalid video format. Allowed formats: MP4, AVI, MOV", error_code="INVALID_VIDEO_FORMAT")

        data = {
            "background_image_url": background_image_url,
            "video_url": video_url,
            "launch_date": launch_date,
        }
        setting = await use_case.execute(data)
        return self.build_response("Update coming soon setting", setting)

controller = AppSettingController()
router = controller.router
