# image_service.py

import logging

logger = logging.getLogger(__name__)

IMAGE_FIELDS = ["app_logo", "white_logo", "app_favicon"]


class BrandImageService:
    def __init__(self, storage_service):
        self.storage_service = storage_service

    async def upload(self, image_data: str, path: str) -> str:
        if not image_data or not self.storage_service:
            return None
        image_bytes, mime_type = await self.storage_service.convert_base64_to_bytes(image_data)
        return await self.storage_service.upload_bytes(path, image_bytes, content_type=mime_type)

    def resolve_url(self, image_key: str):
        if not image_key or not self.storage_service:
            return None
        try:
            return self.storage_service.generate_presigned_url(image_key)
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    async def delete(self, image_key: str):
        if not image_key or not self.storage_service:
            return
        try:
            await self.storage_service.delete(image_key)
        except Exception as e:
            logger.error(f"Error deleting image with key {image_key}: {e}")

    async def replace(self, old_key: str, new_image_data: str, path: str) -> str:
        """Delete the old image and upload the new one. Returns the new storage key."""
        if old_key:
            await self.delete(old_key)
        return await self.upload(new_image_data, path)