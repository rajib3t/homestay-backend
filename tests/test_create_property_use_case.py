from unittest.mock import AsyncMock

import pytest

from app.application.dto.property import Amenity, Facility, FoodOption, PropertyDTO, Room
from app.application.use_cases.property.create_property_use_case import CreatePropertyUseCase
from app.application.use_cases.property.update_property_use_case import UpdatePropertyUseCase
from app.models.property_model import Property
from app.schemas.property_schema import PropertyResponseSchema
from app.services.base_service import BaseService


class DummyService:
    def __init__(self):
        self.create = AsyncMock(return_value="prop-1")
        self.update = AsyncMock(return_value=None)


class DummyStorage:
    async def convert_base64_to_bytes(self, image_data: str):
        return b"fake-image-bytes", "image/jpeg"

    async def convert_and_upload_webp(self, **kwargs):
        return "property_images/cover.webp"


class DummyCurrentUser:
    id = "user-1"


class DummyUOW:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get_session(self):
        return None


@pytest.mark.asyncio
async def test_create_property_use_case_returns_created_property_id():
    dto = PropertyDTO(
        name="Ocean View",
        vendor="vendor-1",
        location="Dhaka",
        city="Dhaka",
        country="Bangladesh",
        address="123 Main Street",
        longitude=90.4125,
        latitude=23.8103,
        description="A nice property",
        cover_image="data:image/jpeg;base64,abcd",
    )

    use_case = CreatePropertyUseCase(
        DummyService(),
        DummyStorage(),
        DummyCurrentUser(),
        DummyUOW(),
    )

    result = await use_case.execute(dto)

    assert result == "prop-1"


def test_base_service_timestamps_supports_pydantic_v1_models():
    service = BaseService(db=None)
    property_model = Property(
        name="Ocean View",
        vendor="vendor-1",
        location="Dhaka",
        city="Dhaka",
        country="Bangladesh",
        address="123 Main Street",
        longitude=90.4125,
        latitude=23.8103,
    )

    updated_model = service.timestamps(property_model, is_new=True)

    assert updated_model.created_at is not None
    assert updated_model.updated_at is not None


def test_property_response_schema_generates_json_schema():
    schema = PropertyResponseSchema.model_json_schema()

    assert "status" in schema["properties"]
    assert "data" in schema["properties"]
    assert "$ref" in schema["properties"]["data"]
    assert "PropertySchema" in schema["$defs"]
    assert "_id" in schema["$defs"]["PropertySchema"]["properties"]


@pytest.mark.asyncio
async def test_create_property_use_case_serializes_nested_options():
    dto = PropertyDTO(
        name="Ocean View",
        vendor="vendor-1",
        location="Dhaka",
        city="Dhaka",
        country="Bangladesh",
        address="123 Main Street",
        longitude=90.4125,
        latitude=23.8103,
        cover_image="data:image/jpeg;base64,abcd",
        food_options=[FoodOption(name="Breakfast", allow=True)],
        amenities=[Amenity(name="WiFi", allow=True)],
        facilities=[Facility(name="Parking", allow=True)],
        rooms=[Room(name="Deluxe", type="double")],
    )

    service = DummyService()
    use_case = CreatePropertyUseCase(
        service,
        DummyStorage(),
        DummyCurrentUser(),
        DummyUOW(),
    )

    await use_case.execute(dto)

    payload = service.create.await_args.kwargs["property_data"]
    assert payload.food_options[0].name == "Breakfast"
    assert payload.food_options[0].allow is True
    assert payload.amenities[0].name == "WiFi"
    assert payload.amenities[0].allow is True
    assert payload.facilities[0].name == "Parking"
    assert payload.facilities[0].allow is True
    assert payload.rooms[0].name == "Deluxe"
    assert payload.rooms[0].type == "double"


@pytest.mark.asyncio
async def test_update_property_use_case_uploads_and_serializes_nested_payloads():
    dto = PropertyDTO(
        name="Ocean View",
        vendor="vendor-1",
        location="Dhaka",
        city="Dhaka",
        country="Bangladesh",
        address="123 Main Street",
        longitude=90.4125,
        latitude=23.8103,
        cover_image="data:image/jpeg;base64,abcd",
        feature_image="data:image/jpeg;base64,efgh",
        trade_license="data:image/jpeg;base64,ijkl",
        gallery_images=["data:image/jpeg;base64,mnop"],
        food_options=[FoodOption(name="Breakfast", allow=True)],
        amenities=[Amenity(name="WiFi", allow=True)],
        facilities=[Facility(name="Parking", allow=True)],
        rooms=[Room(name="Deluxe", type="double")],
    )

    service = DummyService()
    use_case = UpdatePropertyUseCase(
        service,
        DummyStorage(),
        DummyCurrentUser(),
        DummyUOW(),
    )

    await use_case.execute("prop-1", dto)

    payload = service.update.await_args.kwargs["data"]
    assert payload.cover_image == "property_images/cover.webp"
    assert payload.feature_image == "property_images/cover.webp"
    assert payload.trade_license == "property_images/cover.webp"
    assert payload.gallery_images == ["property_images/cover.webp"]
    assert payload.food_options[0].name == "Breakfast"
    assert payload.amenities[0].name == "WiFi"
    assert payload.facilities[0].name == "Parking"
    assert payload.rooms[0].name == "Deluxe"
    assert payload.updated_by == "user-1"
