import re

from bson import ObjectId
from app.application.dto.attribute import AmenityQuery
from app.application.use_cases.attribute.image_service import AttributeImageService
from app.application.use_cases.base_use_case import BaseUseCase
from app.application.use_cases.locations import city
from app.models.attribute_model import CreateAmenity, UpdateAmenity
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)
class AmenityResponseBuilder:
    def __init__(self, image_service: AttributeImageService):
        if image_service is None:
            raise ValueError("image_service is required")
        self.image_service = image_service

    async def amenity(self, amenity_data: dict) -> dict | None:
        if not amenity_data:   # check 1
            return None
       
        result = deepcopy(amenity_data)
        icon_key = result.get("icon")
        
        if icon_key:
            resolved = self.image_service.resolve_url(icon_key)
            if resolved is None:
                # Explicit: icon exists but URL resolution failed
                result["icon"] = None
                result["icon_url_error"] = "URL resolution failed"
            else:
                result["icon"] = resolved

        return result
class CreateAmenityUseCase(BaseUseCase):

    def __init__(
        self,
        attribute_service,
        storage_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

        self.image_service = AttributeImageService(
            self.storage_service
        )

        self.response_builder = AmenityResponseBuilder(
            self.image_service
        )

    async def execute(self, payload: CreateAmenity):
        create_payload = payload.model_dump(exclude={"icon"})
        create_payload["created_by"] = ObjectId(self.current_user.id)

        async with self.uow as uow:
            session = uow.get_session()

           
            path = re.sub(
            r"[^a-z0-9]+",
            "-",
                create_payload.get("name", "").lower(),
            ).strip("-")
            # Upload first — if this fails, nothing is written to DB
            image_key = await self.image_service.upload(
                icon_data=payload.icon,
                path=path,
                folder="amenities"
            )

            if image_key:
                create_payload["icon"] = image_key

            # Single write — no follow-up update needed
            item = await self.attribute_service.create_amenity(
                create_payload,
                session=session
            )

            return await self.response_builder.amenity(item)
        

class GetAmenitiesUseCase(BaseUseCase):

    def __init__(
        self,
        attribute_service,
        storage_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

        self.response_builder = AmenityResponseBuilder(
            AttributeImageService(self.storage_service)
        )

    async def execute(self, query: AmenityQuery):

        async with self.uow as uow:

            session = uow.get_session()

            result = await self.attribute_service.list_amenities(
                query=query,
                session=session
            )

            result["items"] = [
                await self.response_builder.amenity(item)
                for item in result["items"]
            ]

            return result
        

class GetAmenityUseCase(BaseUseCase):

    def __init__(
        self,
        attribute_service,
        storage_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

        self.image_service = AttributeImageService(
            self.storage_service
        )
        self.response_builder = AmenityResponseBuilder(
            AttributeImageService(self.storage_service)
        )

    async def execute(
            self,
            amenity_id: str
        ):
            async with self.uow as uow:
                session = uow.get_session()
                item = await self.attribute_service.get_amenity(
                    amenity_id=amenity_id,
                    session=session
                )
                return await self.response_builder.amenity(item)
            


class UpdateAmenityUseCase(BaseUseCase):

    def __init__(
        self,
        attribute_service,
        storage_service,
        current_user,
        uow,
    ):
        self.attribute_service = attribute_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

        self.image_service = AttributeImageService(self.storage_service)
        self.response_builder = AmenityResponseBuilder(self.image_service)

    async def execute(self, amenity_id: str, payload: UpdateAmenity):
        update_payload = payload.model_dump(exclude={"icon"}, exclude_unset=True)
        update_payload["updated_by"] = ObjectId(self.current_user.id)

        async with self.uow as uow:
            session = uow.get_session()

            # Fetch existing — raises AppException(404) if not found
            existing = await self.attribute_service.get_amenity(
                amenity_id=amenity_id,
                session=session
            )

            if payload.icon:
                existing_key = existing.get("icon")

                # Reuse the exact same storage path so the key never changes.
                # Falls back to a name-derived path only if no prior key exists
                # (e.g. first-time icon on a record created without one).
                if existing_key:
                    upload_path = existing_key          # e.g. "attribute/amenities/pool.webp"
                else:
                    slug = re.sub(
                        r"[^a-z0-9]+", "-",
                        update_payload.get("name", "").lower()
                    ).strip("-")
                    upload_path = f"attribute/amenities/{slug}.webp"

                # If there's an existing image, delete it from storage
                if existing_key:
                    try:
                        await self.image_service.delete(existing_key)
                        logger.info(f"Deleted old icon from storage: {existing_key}")
                    except Exception as e:
                        logger.error(f"Error deleting old icon: {e}")
                        # Continue with the update even if deletion fails

                # Upload to the same path — overwrites at the storage level
                image_key = await self.image_service.upload(
                    icon_data=payload.icon,
                    path=upload_path,        # full key, not just the slug
                    folder=None              # path is already absolute
                )

                if image_key:
                    update_payload["icon"] = image_key

            await self.attribute_service.update_amenity(
                amenity_id=amenity_id,
                data=update_payload,
                session=session
            )

            updated_item = await self.attribute_service.get_amenity(
                amenity_id=amenity_id,
                session=session
            )

            return await self.response_builder.amenity(updated_item)