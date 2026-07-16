import uuid
import logging
from dataclasses import asdict
from typing import Any, Optional
from urllib.parse import urlparse, unquote

from pydantic import BaseModel as PydanticBaseModel
from pydantic.v1 import BaseModel as PydanticV1BaseModel

from app.application.dto.property import PropertyDTO
from app.application.use_cases.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.models.property_model import Property
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


class UpdatePropertyUseCase(BaseUseCase):
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

    def _extract_storage_key(self, image_value: Optional[str]) -> Optional[str]:
        if not image_value or not isinstance(image_value, str):
            return None

        image_value = image_value.strip()
        if not image_value:
            return None

        if image_value.startswith(("http://", "https://")):
            parsed = urlparse(image_value)
            path = unquote(parsed.path.lstrip("/"))

            if self.storage_service.bucket and path.startswith(f"{self.storage_service.bucket}/"):
                return path[len(self.storage_service.bucket) + 1 :]

            return path or None

        return image_value

    async def _delete_image(self, image_value: Optional[str]) -> None:
        key = self._extract_storage_key(image_value)
        if not key:
            return

        try:
            await self.storage_service.delete_object(key)
        except Exception as e:
            logger.warning(f"Failed to delete image {key}: {str(e)}")

    async def _upload_image(self, image_data: str, folder: str, file_name: Optional[str] = None) -> Optional[str]:
        if not image_data or not isinstance(image_data, str) or not image_data.strip():
            return None

        image_data = image_data.strip()

        # Keep already-uploaded images stable. The frontend often sends back
        # the current presigned URL, and we should preserve the underlying
        # object key rather than trying to decode it as base64.
        if image_data.startswith(("http://", "https://")):
            parsed = urlparse(image_data)
            path = unquote(parsed.path.lstrip("/"))

            if self.storage_service.bucket and path.startswith(f"{self.storage_service.bucket}/"):
                return path[len(self.storage_service.bucket) + 1 :]

            # Fallback: if the URL path already looks like a storage key, keep it.
            if path:
                return path

            return None

        if not image_data.startswith("data:image/"):
            return image_data

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

    async def execute(self, property_id: str, data: PropertyDTO):
        if not data:
            raise AppException(status_code=400, message="Property data is required", error_code="PROPERTY_DATA_REQUIRED", field="property_data")
        async with self.uow as uow:
            session = uow.get_session()
            existing_property = await self.property_service.get(property_id, session=session)
            
            cover_image_url = await self._upload_image(
                data.cover_image,
                folder="property_images",
                file_name=f"cover-{uuid.uuid4().hex}",
            )
            feature_image_url = await self._upload_image(
                data.feature_image,
                folder="property_images",
                file_name=f"feature-{uuid.uuid4().hex}",
            )
            trade_license_url = await self._upload_image(
                data.trade_license,
                folder="property_images",
                file_name=f"trade-license-{uuid.uuid4().hex}",
            )

            gallery_images = []
            for image in data.gallery_images or []:
                uploaded_image = await self._upload_image(
                    image,
                    folder="property_gallery",
                    file_name=uuid.uuid4().hex,
                )
                if uploaded_image:
                    gallery_images.append(uploaded_image)

            payload = Property(
                name=data.name,
                vendor=data.vendor,
                location=data.location,
                city=data.city,
                country=data.country,
                address=data.address,
                longitude=data.longitude,
                latitude=data.latitude,
                is_published=data.is_published,
                is_featured=data.is_featured,
                description=data.description,
                trade_license_number=data.trade_license_number,
                star_rating=data.star_rating,
                listing_price=data.listing_price,
                sale_price=data.sale_price,
                check_in_time=data.check_in_time,
                checkout_time=data.checkout_time,
                food_options=self._serialize_nested_items(data.food_options),
                cover_image=cover_image_url or data.cover_image,
                feature_image=feature_image_url or data.feature_image,
                trade_license=trade_license_url or data.trade_license,
                # Preserve `None` as "not provided", but allow an explicit empty
                # list to clear removed gallery images.
                gallery_images=gallery_images if data.gallery_images is not None else data.gallery_images,
                amenities=self._serialize_nested_items(data.amenities),
                facilities=self._serialize_nested_items(data.facilities),
                rooms=self._serialize_nested_items(data.rooms),
                tax_name=data.tax_name,
                tax_percentage=data.tax_percentage,
                updated_by=self.current_user.id,
            )

            result = await self.property_service.update(
                property_id=property_id,
                property_data=payload,
                session=session,
            )

            # Delete replaced/removed images only after the update has succeeded.
            await self._delete_replaced_images(existing_property, payload)

            return result

    async def _delete_replaced_images(self, existing_property: Optional[dict], payload: Property) -> None:
        if not existing_property:
            return

        old_cover = self._extract_storage_key(existing_property.get("cover_image"))
        new_cover = self._extract_storage_key(payload.cover_image)
        if old_cover and old_cover != new_cover:
            await self._delete_image(old_cover)

        old_feature = self._extract_storage_key(existing_property.get("feature_image"))
        new_feature = self._extract_storage_key(payload.feature_image)
        if old_feature and old_feature != new_feature:
            await self._delete_image(old_feature)

        old_trade_license = self._extract_storage_key(existing_property.get("trade_license"))
        new_trade_license = self._extract_storage_key(payload.trade_license)
        if old_trade_license and old_trade_license != new_trade_license:
            await self._delete_image(old_trade_license)

        old_gallery = {
            self._extract_storage_key(image)
            for image in (existing_property.get("gallery_images") or [])
        }
        new_gallery = {
            self._extract_storage_key(image)
            for image in (payload.gallery_images or [])
        }

        for key in (old_gallery - new_gallery):
            if key:
                await self._delete_image(key)
