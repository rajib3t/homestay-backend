import logging

logger = logging.getLogger(__name__)


class UserImageService:
    def __init__(self, storage_service):
        self.storage_service = storage_service

    async def upload(self, image_data: str, path: str) -> str:
        if not image_data or not self.storage_service:
            return None
        image_bytes, _ = (
            await self.storage_service.convert_base64_to_bytes(
                image_data
            )
        )

        key = path
        
        return await self.storage_service.convert_and_upload_webp(key, image_bytes)
    
    def resolve_url(self, image_key: str):

        if not image_key or not self.storage_service:
            return None

        try:

            return (
                self.storage_service.generate_presigned_url(
                    image_key
                )
            )

        except Exception as e:

            logger.error(
                f"Error generating "
                f"presigned URL: {e}"
            )

            return None
        
    async def delete(self, image_key: str):

        if not image_key or not self.storage_service:
            return

        try:
            await self.storage_service.delete(image_key)
        except Exception as e:

            logger.error(
                f"Error deleting image with key {image_key}: {e}"
            )