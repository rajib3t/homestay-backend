import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AttributeImageService:
    def __init__(self, storage_service):
        self.storage_service = storage_service

    async def upload(
              self, 
              icon_data: str, 
              path: str,
              folder: Optional[str] = None
              ) -> str:
        if not icon_data or not self.storage_service:
            return None
        image_bytes, _ = (
            await self.storage_service.convert_base64_to_bytes(
                icon_data
            )
        )

        key = f"attribute/{folder}/{path}.webp" if folder else path

        await self.storage_service.convert_and_upload_webp(
                key=key,
                data=image_bytes,
                quality=90,
            )
        
        return key
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

            await self.storage_service.delete_file(
                image_key
            )

        except Exception as e:

            logger.error(
                f"Error deleting image "
                f"{image_key}: {e}"
            )