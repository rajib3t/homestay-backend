import logging
import re
import uuid

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

        image_bytes, mime_type = (
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

    def resolve_url(self, image_key: str):

        if not image_key or not self.storage:
            return None

        try:

            return self.storage.generate_presigned_url(
                image_key
            )

        except Exception as e:

            logger.error(
                f"Error generating presigned URL: {e}"
            )

            return None


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
        
        self.image_service = CityImageService(storage)
        self.uow = uow

    async def execute(self, payload: dict):

        async with self.uow as uow:
            session = uow.get_session()
            payload["image"] = await self.image_service.upload(
                image_data=payload.get("image"),
                country_id=payload.get("country"),
                city_name=payload.get("name"),
            )

            payload["created_by"] = self.current_user.id

            city_id = await self.service.create_city(payload, session=session)
            uow.collect_event(
                CityCreatedEvent(
                    city_id=city_id,
                    created_by=self.current_user.id,
                )
            )
            city = await self.service.get_city(city_id, session=session)

        return self.build_response(city)

    def build_response(self, city):

        if city.get("image"):

            city["image"] = (
                self.image_service.resolve_url(
                    city["image"]
                )
            )

        return city


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
        self.image_service = CityImageService(storage)

    async def execute(self, query: CityQuery):

        async with self.uow as uow:

            session = uow.get_session()

            result = await self.service.list_cities(
                query=query,
                session=session,
            )

            return self.build_response(result)

    def build_response(self, result):

        if not result or not result.get("items"):
            return result

        items = [
            self.serialize_city(city)
            for city in result["items"]
        ]

        return {
            **result,
            "items": items,
        }

    def serialize_city(self, city):

        if city.get("image"):

            city["image"] = (
                self.image_service.resolve_url(
                    city["image"]
                )
            )

        return city

class GetCityUseCase(BaseUseCase):

    def __init__(self, location_service, storage, current_user, uow):
        self.location_service = location_service
        self.storage = CityImageService(storage)
        self.current_user = current_user
        self.uow = uow
    
    async def execute(self, city_id: str) : 
        
        async with self.uow as uow:
            session = uow.get_session()

            city = await self.location_service.get_city(city_id, session=session)

        if not city:
            raise AppException(404, "City not found")

        return self.build_response(city)
    
    def build_response(self, city):

        if city.get("image"):

            city["image"] = (
                self.storage.resolve_url(
                    city["image"]
                )
            )

        return city 