import uuid
from dataclasses import asdict
import logging
from typing import Any, Optional

from pydantic import BaseModel as PydanticBaseModel
from pydantic.v1 import BaseModel as PydanticV1BaseModel

from app.application.dto.property import PropertyDTO
from app.application.use_cases.base_use_case import BaseUseCase
from app.deps.auth import CurrentUser
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.models.property_model import Property

logger = logging.getLogger(__name__)

class CreatePropertyUseCase(BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        current_user: CurrentUser,
        uow: MongoUnitOfWork,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.uow = uow

    @staticmethod
    def _serialize_nested_items(items: Optional[list[Any]]) -> Optional[list[dict[str, Any]]]:
        if not items:
            return None

        serialized_items = []
        for item in items:
            if isinstance(item, (PydanticBaseModel, PydanticV1BaseModel)):
                serialized_items.append(item.model_dump() if hasattr(item, "model_dump") else item.dict())
            elif hasattr(item, "__dataclass_fields__"):
                serialized_items.append(asdict(item))
            else:
                serialized_items.append(item)

        return serialized_items

    async def _upload_image(self, image_data: str, folder: str, file_name: Optional[str] = None) -> Optional[str]:
        if not image_data or not isinstance(image_data, str) or not image_data.strip():
            return None

        try:
            image_bytes, _ = await self.storage_service.convert_base64_to_bytes(image_data)
            key = f"{folder}/{file_name or uuid.uuid4().hex}.webp"

            return await self.storage_service.convert_and_upload_webp(
                key=key,
                data=image_bytes,
                quality=90,
            )
        except Exception as e:
            logger.warning(f"Failed to upload image for {folder}/{file_name}: {str(e)}")
            return None

    async def execute(self, property_data: PropertyDTO) -> str:
        if not property_data:
            raise ValueError("property_data is required")

        async with self.uow as uow:
            session = uow.get_session()

            cover_image_url = await self._upload_image(
                property_data.cover_image,
                folder="property_images",
                file_name=f"cover-{uuid.uuid4().hex}",
            )
            feature_image_url = await self._upload_image(
                property_data.feature_image,
                folder="property_images",
                file_name=f"feature-{uuid.uuid4().hex}",
            )
            trade_license_url = await self._upload_image(
                property_data.trade_license,
                folder="property_images",
                file_name=f"trade-license-{uuid.uuid4().hex}",
            )

            gallery_images = []
            for image in property_data.gallery_images or []:
                uploaded_image = await self._upload_image(
                    image,
                    folder="property_gallery",
                    file_name=uuid.uuid4().hex,
                )
                if uploaded_image:
                    gallery_images.append(uploaded_image)

            payload = Property(
                name=property_data.name,
                vendor=property_data.vendor,
                location=property_data.location,
                city=property_data.city,
                country=property_data.country,
                address=property_data.address,
                longitude=property_data.longitude,
                latitude=property_data.latitude,
                is_published=property_data.is_published,
                is_featured=property_data.is_featured,
                description=property_data.description,
                trade_license_number=property_data.trade_license_number,
                star_rating=property_data.star_rating,
                listing_price=property_data.listing_price,
                sale_price=property_data.sale_price,
                check_in_time=property_data.check_in_time,
                checkout_time=property_data.checkout_time,
                food_options=self._serialize_nested_items(property_data.food_options),
                cover_image=cover_image_url,
                feature_image=feature_image_url,
                trade_license=trade_license_url,
                gallery_images=gallery_images,
                amenities=self._serialize_nested_items(property_data.amenities),
                facilities=self._serialize_nested_items(property_data.facilities),
                rooms=self._serialize_nested_items(property_data.rooms),
                tax_name=property_data.tax_name,
                tax_percentage=property_data.tax_percentage,
                created_by=self.current_user.id,
                updated_by=self.current_user.id,
            )

            return await self.property_service.create(
                property_data=payload,
                session=session,
            )
