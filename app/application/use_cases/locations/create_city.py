import re
import uuid
import logging
logger = logging.getLogger(__name__)
class CreateCityUseCase:
    def __init__(self, service, storage, current_user):
        self.service = service
        self.storage = storage
        self.current_user = current_user

    async def execute(self, payload: dict):

        country_id = payload.get("country")

        image_data = payload.get("image")

        if image_data and self.storage:

            image_bytes, mime_type = await self.storage.convert_base64_to_bytes(
                image_data
            )

            slug = re.sub(
                r"[^a-z0-9]+",
                "-",
                payload["name"].lower()
            ).strip("-")

            key = f"cities/{country_id}/{slug}-{uuid.uuid4().hex[:8]}.webp"

            await self.storage.convert_and_upload_webp(
                key=key,
                data=image_bytes,
                quality=90,
            )

            payload["image"] = key
        else:
            payload["image"] = None

        payload["created_by"] = self.current_user.id

        city_id = await self.service.create_city(payload)

        return await self.service.get_city(
            city_id,
            storage=self.storage
        )