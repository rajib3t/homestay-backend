from fastapi import Depends
from app.deps.auth import CurrentUser, require_admin
from app.deps.services import (
    get_app_setting_service,
    get_storage_service,
)
from app.services import storage_service
from app.deps.uow import get_uow
from app.application.use_cases.setting.app_setting import (
    GetAppSettingUseCase,
    PostAppSettingUseCase,
)


def get_get_app_setting(
    service=Depends(get_app_setting_service),
    storage_service=Depends(get_storage_service),

    uow=Depends(get_uow),
):
    return GetAppSettingUseCase(
        service,
        storage_service,
        uow,
    )


def get_post_app_setting(
    service=Depends(get_app_setting_service),
    storage_service=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return PostAppSettingUseCase(
        service,
        storage_service,
        current_user,
        uow,
    )
