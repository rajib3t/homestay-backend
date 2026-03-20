import pytest

from app.api.attribute_route import (
    update_amenity_status,
    update_facility_status,
    update_room_type_status,
)
from app.api.location_route import get_country
from app.models.attribute_model import (
    UpdateAmenityStatus,
    UpdateFacilityStatus,
    UpdateRoomTypeStatus,
)
from app.schemas.user_schema import RefreshResponse


class StubLocationService:
    def __init__(self):
        self.country_calls = []

    async def get_country(self, country_id: str):
        self.country_calls.append(country_id)
        return {
            "_id": country_id,
            "name": "Bangladesh",
            "code": "BD",
            "dial_code": 880,
            "status": True,
            "city_count": 0,
        }


class StubAttributeService:
    def __init__(self):
        self.calls = []
        self.toggles = []

    async def update_amenity(self, amenity_id, data, storage=None):
        self.calls.append(("amenity", amenity_id, data, storage))
        return {"_id": amenity_id, "name": "Pool", "icon": None, "status": data["status"]}

    async def update_facility(self, facility_id, data, storage=None):
        self.calls.append(("facility", facility_id, data, storage))
        return {"_id": facility_id, "name": "Parking", "icon": None, "status": data["status"]}

    async def update_room_type(self, room_type_id, data):
        self.calls.append(("room_type", room_type_id, data, None))
        return {"_id": room_type_id, "name": "Deluxe", "capacity": 2, "status": data["status"]}

    async def toggle_amenity_status(self, amenity_id):
        self.toggles.append(("amenity", amenity_id))
        raise AssertionError("toggle_amenity_status should not be called")

    async def toggle_facility_status(self, facility_id):
        self.toggles.append(("facility", facility_id))
        raise AssertionError("toggle_facility_status should not be called")

    async def toggle_room_type_status(self, room_type_id):
        self.toggles.append(("room_type", room_type_id))
        raise AssertionError("toggle_room_type_status should not be called")


@pytest.mark.asyncio
async def test_get_country_route_uses_single_argument_service_signature():
    service = StubLocationService()
    response = await get_country(country_id="country-1", service=service)

    assert response["data"]["_id"] == "country-1"
    assert service.country_calls == ["country-1"]


@pytest.mark.asyncio
async def test_status_endpoints_use_explicit_status_updates():
    service = StubAttributeService()
    amenity_response = await update_amenity_status(
        amenity_id="amenity-1",
        status_data=UpdateAmenityStatus(status=False),
        attribute_service=service,
    )
    facility_response = await update_facility_status(
        facility_id="facility-1",
        status_data=UpdateFacilityStatus(status=False),
        attribute_service=service,
    )
    room_type_response = await update_room_type_status(
        room_type_id="room-1",
        status_data=UpdateRoomTypeStatus(status=False),
        attribute_service=service,
    )

    assert amenity_response["data"]["status"] is False
    assert facility_response["data"]["status"] is False
    assert room_type_response["data"]["status"] is False
    assert service.calls == [
        ("amenity", "amenity-1", {"status": False}, None),
        ("facility", "facility-1", {"status": False}, None),
        ("room_type", "room-1", {"status": False}, None),
    ]
    assert service.toggles == []


def test_refresh_response_accepts_rotated_refresh_token():
    response = RefreshResponse.model_validate(
        {
            "status": "success",
            "message": "Token refreshed successfully",
            "data": {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
            },
        }
    )

    assert response.data.access_token == "access-token"
    assert response.data.refresh_token == "refresh-token"