from fastapi import APIRouter, Depends, HTTPException
from app.application.use_cases.attribute.amenity import CreateAmenityUseCase, GetAmenitiesUseCase, GetAmenityUseCase, UpdateAmenityUseCase
from app.deps.attribute_use import get_create_amenity_use_case, get_list_amenities_use_case, get_single_amenity_update_use_case, get_single_amenity_use_case
from app.middleware.idempotency_route import IdempotencyRoute
from app.deps import get_attribute_service, get_storage_service, get_current_user
from app.services.attribute_service import AttributeService
from app.services.storage_service import StorageService
from app.models.attribute_model import (
    CreateAmenity, UpdateAmenity, UpdateAmenityStatus,
    CreateFacility, UpdateFacility, UpdateFacilityStatus,
    CreateRoomType, UpdateRoomType, UpdateRoomTypeStatus,
    ListAmenities, ListFacilities, ListRoomTypes
)
from app.schemas.attribute_schema import (
    AmenityResponse, AmenitiesResponse,
    FacilityResponse, FacilitiesResponse,
    RoomTypeResponse, RoomTypesResponse
)
from app.utils.api_utils import upload_data_url_asset, replace_data_url_asset
from app.utils.exception_decorate import handle_api_exceptions

from app.application.dto.attribute import Amenity, AmenityQuery

from .base_controller import BaseController

def _pagination_meta(r):
    return {"total": r["total"], "page": r["page"], "size": r["size"]}


class AttributeController(BaseController):

    def __init__(self):
        super().__init__(service=None, storage_service=None)

        self.router = APIRouter(
            prefix="/attributes",
            tags=["Attributes"],
            route_class=IdempotencyRoute,
        )

        self.register_routes()

    # ---------------- ROUTE REGISTRATION ---------------- #

    def register_routes(self):
        routes = [
            # Amenity
            ("post",  "/amenity",              self.create_amenity,        {"response_model": AmenityResponse,    "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/amenities",            self.list_amenities,        {"response_model": AmenitiesResponse,  "response_model_by_alias": False}),
            ("get",   "/amenity/{amenity_id}", self.get_amenity,           {"response_model": AmenityResponse,    "response_model_by_alias": False}),
            ("patch", "/amenity/{amenity_id}", self.update_amenity,        {"response_model": AmenityResponse,    "response_model_by_alias": False}),
            ("patch", "/amenity/{amenity_id}/status", self.update_amenity_status, {"response_model": AmenityResponse, "response_model_by_alias": False}),

            # Facility
            ("post",  "/facility",                  self.create_facility,        {"response_model": FacilityResponse,   "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/facilities",                self.list_facilities,        {"response_model": FacilitiesResponse, "response_model_by_alias": False}),
            ("get",   "/facility/{facility_id}",    self.get_facility,           {"response_model": FacilityResponse,   "response_model_by_alias": False}),
            ("patch", "/facility/{facility_id}",    self.update_facility,        {"response_model": FacilityResponse,   "response_model_by_alias": False}),
            ("patch", "/facility/{facility_id}/status", self.update_facility_status, {"response_model": FacilityResponse, "response_model_by_alias": False}),

            # Room type
            ("post",  "/room-type",                    self.create_room_type,        {"response_model": RoomTypeResponse,  "response_model_by_alias": False, "status_code": 201}),
            ("get",   "/room-types",                   self.list_room_types,         {"response_model": RoomTypesResponse, "response_model_by_alias": False}),
            ("get",   "/room-type/{room_type_id}",     self.get_room_type,           {"response_model": RoomTypeResponse,  "response_model_by_alias": False}),
            ("patch", "/room-type/{room_type_id}",     self.update_room_type,        {"response_model": RoomTypeResponse,  "response_model_by_alias": False}),
            ("patch", "/room-type/{room_type_id}/status", self.update_room_type_status, {"response_model": RoomTypeResponse, "response_model_by_alias": False}),
        ]

        for method, path, handler, route_kwargs in routes:
            getattr(self.router, method)(path, **route_kwargs)(handler)

    # ---------------- AMENITY ---------------- #

    @handle_api_exceptions
    async def create_amenity(
        self,
        data: CreateAmenity,
        use_case: CreateAmenityUseCase = Depends(get_create_amenity_use_case)
    ):
        
        
        item = await use_case.execute(data)

        

        return self.build_response("Amenity created", item)

    @handle_api_exceptions
    async def list_amenities(
        self,
        params: ListAmenities = Depends(),
        use_case: GetAmenitiesUseCase = Depends(get_list_amenities_use_case)
    ):
        search = self.build_search(name=params.name, status=params.status)
        result = await use_case.execute(
            AmenityQuery(
                page=params.page,
                size=params.size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                filters=search
            )
        )
            
        return self.build_response("Amenities list", data=result["items"], meta=_pagination_meta(result))

    @handle_api_exceptions
    async def get_amenity(
        self,
        amenity_id: str,
        use_case: GetAmenityUseCase = Depends(get_single_amenity_use_case)
    ):
        item = await use_case.execute(amenity_id)
        
        return self.build_response("Amenity fetched", item)

    @handle_api_exceptions
    async def update_amenity(
        self,
        amenity_id: str,
        data: UpdateAmenity,
        use_case: UpdateAmenityUseCase = Depends(get_single_amenity_update_use_case)
    ):
        updated = await use_case.execute(amenity_id, data)
        return self.build_response("Amenity updated", updated)

    @handle_api_exceptions
    async def update_amenity_status(
        self,
        amenity_id: str,
        status_data: UpdateAmenity,
        use_case: UpdateAmenityUseCase = Depends(get_single_amenity_update_use_case)
    ):
        updated = await use_case.execute(amenity_id, status_data)
        return self.build_response("Amenity status updated", updated)

    # ---------------- FACILITY ---------------- #

    @handle_api_exceptions
    async def create_facility(
        self,
        data: CreateFacility,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        payload = data.model_dump()
        item_id = await service.create_facility(payload, storage_service)
        item = await service.get_facility(item_id, storage_service)
        return self.build_response("Facility created", item)

    @handle_api_exceptions
    async def list_facilities(
        self,
        params: ListFacilities = Depends(),
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        search = self.build_search(name=params.name, status=params.status)
        result = await service.list_facilities(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
            storage=storage_service,
        )
        return self.build_response("Facilities list", data=result["items"], meta=_pagination_meta(result))

    @handle_api_exceptions
    async def get_facility(
        self,
        facility_id: str,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        item = await service.get_facility(facility_id, storage_service)
        if not item:
            raise HTTPException(status_code=404, detail="Facility not found")
        return self.build_response("Facility fetched", item)

    @handle_api_exceptions
    async def update_facility(
        self,
        facility_id: str,
        data: UpdateFacility,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
        storage_service: StorageService = Depends(get_storage_service),
    ):
        update_data = data.model_dump(exclude_none=True)
        updated = await service.update_facility(facility_id, update_data, storage_service)
        return self.build_response("Facility updated", updated)

    @handle_api_exceptions
    async def update_facility_status(
        self,
        facility_id: str,
        status_data: UpdateFacilityStatus,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        updated = await service.update_facility(facility_id, {"status": status_data.status}, storage=None)
        return self.build_response("Facility status updated", updated)

    # ---------------- ROOM TYPE ---------------- #

    @handle_api_exceptions
    async def create_room_type(
        self,
        data: CreateRoomType,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        payload = data.model_dump()
        item_id = await service.create_room_type(payload)
        item = await service.get_room_type(item_id)
        return self.build_response("Room type created", item)

    @handle_api_exceptions
    async def list_room_types(
        self,
        params: ListRoomTypes = Depends(),
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        search = self.build_search(name=params.name, status=params.status)
        result = await service.list_room_types(
            page=params.page,
            size=params.size,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            search=search,
        )
        return self.build_response("Room types list", data=result["items"], meta=_pagination_meta(result))

    @handle_api_exceptions
    async def get_room_type(
        self,
        room_type_id: str,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        item = await service.get_room_type(room_type_id)
        if not item:
            raise HTTPException(status_code=404, detail="Room type not found")
        return self.build_response("Room type fetched", item)

    @handle_api_exceptions
    async def update_room_type(
        self,
        room_type_id: str,
        data: UpdateRoomType,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        update_data = data.model_dump(exclude_none=True)
        updated = await service.update_room_type(room_type_id, update_data)
        return self.build_response("Room type updated", updated)

    @handle_api_exceptions
    async def update_room_type_status(
        self,
        room_type_id: str,
        status_data: UpdateRoomTypeStatus,
        current_user: str = Depends(get_current_user),
        service: AttributeService = Depends(get_attribute_service),
    ):
        updated = await service.update_room_type(room_type_id, {"status": status_data.status})
        return self.build_response("Room type status updated", updated)


controller = AttributeController()
router = controller.router


@handle_api_exceptions
async def update_amenity_status(
    amenity_id: str,
    status_data: UpdateAmenityStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    return await controller.update_amenity_status(
        amenity_id=amenity_id,
        status_data=status_data,
        service=attribute_service,
    )


@handle_api_exceptions
async def update_facility_status(
    facility_id: str,
    status_data: UpdateFacilityStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    return await controller.update_facility_status(
        facility_id=facility_id,
        status_data=status_data,
        service=attribute_service,
    )


@handle_api_exceptions
async def update_room_type_status(
    room_type_id: str,
    status_data: UpdateRoomTypeStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    return await controller.update_room_type_status(
        room_type_id=room_type_id,
        status_data=status_data,
        service=attribute_service,
    )