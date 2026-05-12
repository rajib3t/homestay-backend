import logging
import re
import uuid
from copy import deepcopy

from app.application.dto.city_query import CityQuery
from app.application.use_cases.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.domain.events.city_event import CityCreatedEvent

logger = logging.getLogger(__name__)


class CityImageService:

    def __init__(self, storage):
        self.storage = storage

    async def upload(
        self,
        image_data: str,
        country_id: str,
        city_name: str,
    ):

        if not image_data or not self.storage:
            return None

        image_bytes, _ = (
            await self.storage.convert_base64_to_bytes(
                image_data
            )
        )

        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            city_name.lower(),
        ).strip("-")

        key = (
            f"cities/"
            f"{country_id}/"
            f"{slug}-{uuid.uuid4().hex[:8]}.webp"
        )

        await self.storage.convert_and_upload_webp(
            key=key,
            data=image_bytes,
            quality=90,
        )

        return key

    async def delete(self, image_key: str):

        if not image_key or not self.storage:
            return

        try:

            await self.storage.delete_file(
                image_key
            )

        except Exception as e:

            logger.error(
                f"Error deleting image "
                f"{image_key}: {e}"
            )

    def resolve_url(self, image_key: str):

        if not image_key or not self.storage:
            return None

        try:

            return (
                self.storage.generate_presigned_url(
                    image_key
                )
            )

        except Exception as e:

            logger.error(
                f"Error generating "
                f"presigned URL: {e}"
            )

            return None


class CityResponseBuilder:

    def __init__(self, image_service):
        self.image_service = image_service

    def city(self, city: dict):

        if not city:
            return city

        result = deepcopy(city)

        if result.get("image"):

            result["image"] = (
                self.image_service.resolve_url(
                    result["image"]
                )
            )

        return result

    def cities(self, result: dict):

        if not result:
            return result

        items = result.get("items", [])

        return {
            **result,
            "items": [
                self.city(city)
                for city in items
            ]
        }


class CreateCityUseCase(BaseUseCase):

    def __init__(
        self,
        service,
        storage,
        current_user,
        uow,
    ):
        self.service = service
        self.current_user = current_user
        self.uow = uow

        image_service = CityImageService(storage)

        self.image_service = image_service
        self.response_builder = (
            CityResponseBuilder(
                image_service
            )
        )

    async def execute(self, payload: dict):

        create_payload = {
            **payload,
            "created_by": (
                self.current_user.id
            ),
        }

        image_key = (
            await self.image_service.upload(
                image_data=payload.get(
                    "image"
                ),
                country_id=payload.get(
                    "country"
                ),
                city_name=payload.get(
                    "name"
                ),
            )
        )

        create_payload["image"] = image_key

        async with self.uow as uow:

            session = uow.get_session()

            city_id = (
                await self.service.create_city(
                    create_payload,
                    session=session,
                )
            )

            uow.collect_event(
                CityCreatedEvent(
                    city_id=city_id,
                    created_by=(
                        self.current_user.id
                    ),
                )
            )

            city = (
                await self.service.get_city(
                    city_id,
                    session=session,
                )
            )

        return (
            self.response_builder.city(
                city
            )
        )


class GetCitiesUseCase(BaseUseCase):

    def __init__(
        self,
        service,
        storage,
        current_user,
        uow,
    ):
        self.service = service
        self.current_user = current_user
        self.uow = uow

        image_service = CityImageService(
            storage
        )

        self.image_service = image_service
        self.response_builder = (
            CityResponseBuilder(
                image_service
            )
        )

    async def execute(
        self,
        query: CityQuery,
    ):

        async with self.uow as uow:

            session = uow.get_session()

            result = (
                await self.service.list_cities(
                    query=query,
                    session=session,
                )
            )

        return (
            self.response_builder.cities(
                result
            )
        )


class GetCityUseCase(BaseUseCase):

    def __init__(
        self,
        service,
        storage,
        current_user,
        uow,
    ):
        self.service = service
        self.current_user = current_user
        self.uow = uow

        image_service = CityImageService(
            storage
        )

        self.image_service = image_service
        self.response_builder = (
            CityResponseBuilder(
                image_service
            )
        )

    async def execute(
        self,
        city_id: str,
    ):

        async with self.uow as uow:

            session = uow.get_session()

            city = (
                await self.service.get_city(
                    city_id,
                    session=session,
                )
            )

        if not city:
            raise AppException(
                404,
                "City not found",
            )

        return (
            self.response_builder.city(
                city
            )
        )


class UpdateCityUseCase(BaseUseCase):

    def __init__(
        self,
        service,
        storage,
        current_user,
        uow,
    ):
        self.service = service
        self.current_user = current_user
        self.uow = uow

        image_service = CityImageService(storage)

        self.image_service = image_service

        self.response_builder = (
            CityResponseBuilder(
                image_service
            )
        )

    async def execute(
        self,
        city_id: str,
        payload: dict,
    ):

        async with self.uow as uow:

            session = uow.get_session()

            existing_city = (
                await self.service.get_raw_city(
                    city_id=city_id,
                    session=session,
                )
            )

            update_payload = (
                await self._prepare_payload(
                    payload=payload,
                    existing_city=existing_city,
                )
            )

            updated_city = (
                await self.service.update_city(
                    city_id=city_id,
                    payload=update_payload,
                    session=session,
                )
            )

        await self._delete_old_image(
            old_image=existing_city.get("image"),
            new_image=update_payload.get("image"),  # None if unchanged → guard skips delete
        )

        return self.response_builder.city(updated_city)

    async def _prepare_payload(
        self,
        payload: dict,
        existing_city: dict,
    ):
        prepared = {
            **payload,
            "updated_by": self.current_user.id,
        }

        image_data = payload.get("image")

        # No image field sent — client wants to keep existing, don't touch it
        if not image_data:
            prepared.pop("image", None)  # ensure image key not in payload at all
            return prepared

        # Client sent back the existing presigned URL — treat as unchanged
        if not image_data.startswith("data:image"):
            prepared.pop("image", None)
            return prepared

        # Fresh base64 upload — upload and replace
        image_key = await self.image_service.upload(
            image_data=image_data,
            country_id=payload.get("country", existing_city["country"]),
            city_name=payload.get("name", existing_city["name"]),
        )

        prepared["image"] = image_key
        return prepared

    async def _delete_old_image(
        self,
        old_image: str,
        new_image: str,
    ):

        if (
            not old_image
            or not new_image
            or old_image == new_image
        ):
            return

        await self.image_service.delete(old_image)