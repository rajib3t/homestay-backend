# app_setting_use_cases.py

from app.application.use_cases.base_use_case import BaseUseCase
from app.application.use_cases.setting.image_service import BrandImageService, IMAGE_FIELDS
from app.schemas.app_setting_schema import AppSetting


class AppSettingResponseBuilder:
    def __init__(self, image_service: BrandImageService):
        self.image_service = image_service

    def build_response(self, setting:  dict) -> dict:
        if not setting:
            return None
        setting_dict = setting.copy()
        

        for field in IMAGE_FIELDS:
            if setting_dict.get(field):
                setting_dict[field] = self.image_service.resolve_url(setting_dict[field])
        return setting_dict


class GetAppSettingUseCase(BaseUseCase):
    def __init__(self, service, storage_service, uow):
        self.service = service
        self.uow = uow
        self.response_builder = AppSettingResponseBuilder(BrandImageService(storage_service))

    async def execute(self):
        async with self.uow as uow:
            session = uow.get_session()
            setting = await self.service.get_setting(session=session)
        return self.response_builder.build_response(setting)


class PostAppSettingUseCase(BaseUseCase):
    def __init__(self, service, storage_service, uow):
        self.service = service
        self.uow = uow
        self.image_service = BrandImageService(storage_service)
        self.response_builder = AppSettingResponseBuilder(self.image_service)

    async def execute(self, data: AppSetting):
        payload = data.model_dump(exclude_unset=True)

        # Fetch existing setting to get old image keys
        async with self.uow as uow:
            session = uow.get_session()
            existing = await self.service.get_setting(session=session)

        existing_dict = existing if existing else {}

        # Replace images: delete old keys, upload new base64 data
        for field in IMAGE_FIELDS:
            new_value = payload.get(field)
            old_key = existing_dict.get(field)

            if new_value and new_value != old_key:
                # new_value is base64 — upload and replace old
                new_key = await self.image_service.replace(
                    old_key=old_key,
                    new_image_data=new_value,
                    path=f"brand/{field}",
                )
                payload[field] = new_key
            # if unchanged or empty, leave payload[field] as-is

        async with self.uow as uow:
            session = uow.get_session()
            setting = await self.service.save_setting(payload, session=session)

        return self.response_builder.build_response(setting)