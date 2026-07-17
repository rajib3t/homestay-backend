from fastapi import Depends
from app.application.use_cases.setting.coming_soon_use_case import GetComingSoonSettingUseCase
from app.deps.auth import CurrentUser, require_admin
from app.deps.services import (
    get_app_setting_service,
    get_coming_soon_setting_service,
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



async def get_coming_soon_setting(
    service=Depends(get_coming_soon_setting_service),
    storage_service=Depends(get_storage_service),
    
    uow=Depends(get_uow),
):
   
    return GetComingSoonSettingUseCase(
        service,
        storage_service,
       
        uow,
    )   

async def get_post_coming_soon_setting(
    service=Depends(get_coming_soon_setting_service),
    storage_service=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
   
    from app.application.use_cases.setting.coming_soon_use_case import PostComingSoonSettingUseCase
    return PostComingSoonSettingUseCase(
        service,
        storage_service,
        current_user,
        uow,
    )