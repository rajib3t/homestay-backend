import pytest

from app.application.dto.property import PropertyDTO
from app.application.use_cases.property.create_property_use_case import CreatePropertyUseCase


class DummyService:
    async def create(self, property_data, session=None):
        return "prop-1"


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
