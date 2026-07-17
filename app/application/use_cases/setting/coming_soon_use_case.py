import mimetypes
from uuid import uuid4

from app.application.use_cases.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.services.coming_soon_setting_service import ComingSoonSettingService
from app.services.storage_service import StorageService


class GetComingSoonSettingUseCase(BaseUseCase):
    

    def __init__(
            self,
            service : ComingSoonSettingService,
            storage_service : StorageService,
           
            uow : MongoUnitOfWork,
    ):
        self.service = service
        self.storage_service = storage_service
        
        self.uow = uow

    async def execute(self):
        result = await self.service.get()

        if result:
            background_image_url = result.get("background_image_url")
            if isinstance(background_image_url, str) and background_image_url:
                result["background_image_url"] = self.storage_service.generate_presigned_url(background_image_url)
            elif background_image_url is not None:
                result["background_image_url"] = None

            video_url = result.get("video_url")
            if isinstance(video_url, str) and video_url:
                result["video_url"] = self.storage_service.generate_presigned_url(video_url)
            elif video_url is not None:
                result["video_url"] = None

        return result
    



class PostComingSoonSettingUseCase(BaseUseCase):
    def __init__(
            self,
            service : ComingSoonSettingService,
            storage_service : StorageService,
            current_user : CurrentUser,
            uow : MongoUnitOfWork,
    ):
        self.service = service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, data: dict):
        payload = dict(data)
        current = await self.service.get()
        old_background_image_url = current.get("background_image_url") if current else None
        old_video_url = current.get("video_url") if current else None

        background_image = payload.get("background_image_url")
        if self._is_upload_file(background_image):
            payload["background_image_url"] = await self._upload_file(
                background_image,
                folder="coming-soon/images",
                field_name="background_image_url",
            )

        video = payload.get("video_url")
        if self._is_upload_file(video):
            payload["video_url"] = await self._upload_file(
                video,
                folder="coming-soon/videos",
                field_name="video_url",
            )

        result = await self.service.save(payload)

        await self._delete_replaced_file(old_background_image_url, payload.get("background_image_url"))
        await self._delete_replaced_file(old_video_url, payload.get("video_url"))

        return result

    @staticmethod
    def _is_upload_file(value) -> bool:
        return hasattr(value, "read") and hasattr(value, "content_type")

    async def _upload_file(self, upload, *, folder: str, field_name: str) -> str:
        raw = await upload.read()
        mime_type = upload.content_type or mimetypes.guess_type(upload.filename or "")[0]
        extension = mimetypes.guess_extension(mime_type or "") or ""
        key = f"{folder}/{field_name}_{uuid4().hex}{extension}"
        return await self.storage_service.upload_bytes(key, raw, content_type=mime_type)

    async def _delete_replaced_file(self, old_value, new_value):
        if isinstance(old_value, str) and old_value and old_value != new_value:
            try:
                await self.storage_service.delete_object(old_value)
            except Exception:
                pass
