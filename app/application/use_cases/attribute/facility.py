from copy import deepcopy
import re
from typing import Optional

from bson import ObjectId

from app.application.dto.facility import FacilityQuery
from app.application.use_cases.attribute.image_service import AttributeImageService
from app.application.use_cases.base_use_case import BaseUseCase
from app.models.attribute_model import CreateFacility, UpdateFacility
import logging

logger = logging.getLogger(__name__)

class FacilityResponseBuilder:
    def __init__(self, image_service: AttributeImageService):
        if image_service is None:
            raise ValueError("image_service is required")
        self.image_service = image_service

    async def facility(self, facility_data: dict) -> Optional[dict]:
        if not facility_data:   # check 1
            return None
       
        result = deepcopy(facility_data)
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
    

class CreateFacilityUseCase(BaseUseCase):

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

        self.response_builder = FacilityResponseBuilder(
            self.image_service
        )

    async def execute(self, payload: CreateFacility):
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
                folder="facilities"
            )

            if image_key:
                create_payload["icon"] = image_key


            facility = await self.attribute_service.create_facility(
                session=session,
                data=create_payload,
            )
            
            return await self.response_builder.facility(facility)
        


class GetFacilitiesUseCase(BaseUseCase):
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

        self.response_builder = FacilityResponseBuilder(
            self.image_service
        )

    async def execute(self, query: FacilityQuery):
        async with self.uow as uow:
            session = uow.get_session()
            result = await self.attribute_service.list_facilities(
                query=query,
                session=session
            )

            result["items"] = [
                await self.response_builder.facility(item)
                for item in result["items"]
            ]

            return result
        

class GetFacilityUseCase(BaseUseCase):

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
        self.response_builder = FacilityResponseBuilder(
            AttributeImageService(self.storage_service)
        )

    async def execute(
            self,
            facility_id: str
        ):
            async with self.uow as uow:
                session = uow.get_session()
                item = await self.attribute_service.get_facility(
                    facility_id=facility_id,
                    session=session
                )
                return await self.response_builder.facility(item)
        

class UpdateFacilityUseCase(BaseUseCase):

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
        self.response_builder = FacilityResponseBuilder(self.image_service)

    async def execute(self, facility_id: str, payload: UpdateFacility):
        update_payload = payload.model_dump(exclude={"icon"}, exclude_unset=True)
        update_payload["updated_by"] = ObjectId(self.current_user.id)
        logger.info(f"Updating facility {facility_id} with payload: {update_payload}")
        async with self.uow as uow:
            session = uow.get_session()

            # Fetch existing — raises AppException(404) if not found
            existing = await self.attribute_service.get_facility(
                facility_id=facility_id,
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

                # Delete the old file first; log but don't abort on failure
                if existing_key:
                    deleted = await self.image_service.delete(existing_key)
                    if not deleted:
                        logger.warning(
                            f"Could not delete previous icon for facility "
                            f"{facility_id}: {existing_key}"
                        )

                # Upload to the same path — overwrites at the storage level
                image_key = await self.image_service.upload(
                    icon_data=payload.icon,
                    path=upload_path,        # full key, not just the slug
                    folder=None              # path is already absolute
                )

                if image_key:
                    update_payload["icon"] = image_key

            await self.attribute_service.update_facility(
                facility_id=facility_id,
                data=update_payload,
                session=session
            )

            updated_item = await self.attribute_service.get_facility(
                facility_id=facility_id,
                session=session
            )

            return await self.response_builder.facility(updated_item)