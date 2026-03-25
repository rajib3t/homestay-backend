from fastapi import APIRouter, Depends, HTTPException, status
from app.deps import get_attribute_service, get_storage_service
from app.models.attribute_model import CreateAmenity, CreateFacility, CreateRoomType, ListAmenities, ListFacilities, ListRoomTypes, UpdateAmenity, UpdateAmenityStatus, UpdateFacility, UpdateFacilityStatus, UpdateRoomType, UpdateRoomTypeStatus
from app.schemas.attribute_schema import AmenitiesResponse, AmenityResponse, FacilityResponse, FacilitiesResponse, RoomTypeResponse, RoomTypesResponse
from app.services.attribute_service import AttributeService
from app.services.storage_service import StorageService
from app.utils.api_utils import (
    handle_exception,
    build_search,
    replace_data_url_asset,
    upload_data_url_asset,
)

router = APIRouter(prefix="/attributes", tags=["Attributes"])
# This file defines API routes for managing attributes such as amenities. 
# It includes a route for creating a new amenity, which accepts data including the name, an optional icon (which can be a data URL), and status. 
# The route interacts with the AttributeService to handle business logic and uses StorageService for handling file uploads if an icon is provided as a data URL. 
# The response includes the created amenity details or appropriate error messages in case of failure.
@router.post(
    "/amenity",
    response_model=AmenityResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_amenity(
    amenity_data: CreateAmenity,
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> AmenityResponse:
    try:
        new_amenity = {
            "name": amenity_data.name,
            "icon": None,
            "status": amenity_data.status
        }

        icon_value = amenity_data.icon

        if icon_value and icon_value.startswith("data:"):
            new_amenity["icon"] = await upload_data_url_asset(
                storage_service,
                icon_value,
                "amenities",
                amenity_data.name,
            )
        else:
            new_amenity["icon"] = icon_value

        amenity_id = await attribute_service.create_amenity(new_amenity, storage_service)

        amenity = await attribute_service.get_amenity(amenity_id)

        return {
            "status": "success",
            "message": "Amenity created successfully",
            "data": amenity
        }

    except Exception as e:
        handle_exception(e)
    

@router.get(
    "/amenities",
    response_model=AmenitiesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_amenities(
    params: ListAmenities = Depends(),
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage_service: StorageService = Depends(get_storage_service)
) -> AmenitiesResponse:
    
        try:
            search = build_search(
            name=params.name,
            status=params.status,
            
        )
            
            
            result = await attribute_service.list_amenities(
                page=params.page,
                size=params.size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                search=search,
                storage=storage_service
            )
            return {
                "status": "success",
                "message": "Amenities retrieved successfully",
                "meta": {
                    "total": result["total"],
                    "page": result["page"],
                    "size": result["size"],
                },
                "data": result["items"],
            }
        except Exception as e:
            handle_exception(e)
        
@router.get(
    "/amenity/{amenity_id}",
    response_model=AmenityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_amenity(
    amenity_id: str,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> AmenityResponse:
    try:
        amenity = await attribute_service.get_amenity(amenity_id)
        if not amenity:
            raise HTTPException(status_code=404, detail="Amenity not found")
        return {
            "status": "success",
            "message": "Amenity retrieved successfully",
            "data": amenity
        }
    except Exception as e:
        handle_exception(e)

@router.patch(
    "/amenity/{amenity_id}",
    response_model=AmenityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_amenity(
    amenity_id: str,
    amenity_data: UpdateAmenity,
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    try:
        update_data = amenity_data.model_dump(exclude_none=True)

        icon_value = update_data.get("icon")

        if isinstance(icon_value, str) and icon_value.startswith("data:"):
            existing = await attribute_service.get_amenity(amenity_id)
            name_for_key = update_data.get("name") or existing.get("name") or "amenity"
            update_data["icon"] = await replace_data_url_asset(
                storage_service,
                icon_value,
                "amenities",
                name_for_key,
                existing.get("icon"),
            )

        updated_amenity = await attribute_service.update_amenity(
            amenity_id,
            update_data,
            storage_service
        )

        return {
            "status": "success",
            "message": "Amenity updated successfully",
            "data": updated_amenity
        }

    except Exception as e:
        handle_exception(e)

@router.patch(
    "/amenity/{amenity_id}/status",
    response_model=AmenityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_amenity_status(
    amenity_id: str,
    status_data: UpdateAmenityStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> AmenityResponse:
    try:
        updated_amenity = await attribute_service.update_amenity(
            amenity_id,
            {"status": status_data.status},
            storage=None,
        )

        return {
            "status": "success",
            "message": "Amenity status updated successfully",
            "data": updated_amenity,
        }
    except Exception as e:
        handle_exception(e)

@router.post(
    "/facility",
    response_model=FacilityResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_facility(
    facility_data: CreateFacility,
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage: StorageService = Depends(get_storage_service),
) -> FacilityResponse:
    try:
        new_facility = {
            "name": facility_data.name,
            "icon": facility_data.icon,
            "status": facility_data.status
        }

        facility_id = await attribute_service.create_facility(new_facility, storage)

        facility = await attribute_service.get_facility(facility_id)

        return {
            "status": "success",
            "message": "Facility created successfully",
            "data": facility
        }

    except Exception as e:
        handle_exception(e)

    
@router.get(
    "/facility/{facility_id}",
    response_model=FacilityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_facility(
    facility_id: str,
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage: StorageService = Depends(get_storage_service)
) -> FacilityResponse:
    try:
        facility = await attribute_service.get_facility(facility_id, storage)
        if not facility:
            raise HTTPException(status_code=404, detail="Facility not found")
        return {
            "status": "success",
            "message": "Facility retrieved successfully",
            "data": facility
        }
    except Exception as e:
        handle_exception(e)
@router.get(
    "/facilities",
    response_model=FacilitiesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_facilities(
    params: ListFacilities = Depends(),
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage_service: StorageService = Depends(get_storage_service)
):
        try:
            search = build_search(
            name=params.name,
            status=params.status,
            
        )
            
            
            result = await attribute_service.list_facilities(
                page=params.page,
                size=params.size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                search=search,
                storage=storage_service
            )
            return {
                "status": "success",
                "message": "Facilities retrieved successfully",
                "meta": {
                    "total": result["total"],
                    "page": result["page"],
                    "size": result["size"],
                },
                "data": result["items"],
            }
        except Exception as e:
            handle_exception(e)
    

@router.patch(
    "/facility/{facility_id}",
    response_model=FacilityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_facility(
    facility_id: str,
    facility_data: UpdateFacility,
    attribute_service: AttributeService = Depends(get_attribute_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    try:
        update_data = facility_data.model_dump(exclude_none=True)

        icon_value = update_data.get("icon")

        if isinstance(icon_value, str) and icon_value.startswith("data:"):
            existing = await attribute_service.get_facility(facility_id)
            name_for_key = update_data.get("name") or existing.get("name") or "facility"
            update_data["icon"] = await replace_data_url_asset(
                storage_service,
                icon_value,
                "facilities",
                name_for_key,
                existing.get("icon"),
            )

        updated_facility = await attribute_service.update_facility(
            facility_id,
            update_data,
            storage_service
        )

        return {
            "status": "success",
            "message": "Facility updated successfully",
            "data": updated_facility
        }

    except Exception as e:
        handle_exception(e)
    
@router.patch(
    "/facility/{facility_id}/status",
    response_model=FacilityResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_facility_status(
    facility_id: str,
    status_data: UpdateFacilityStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> FacilityResponse:
    try:
        updated_facility = await attribute_service.update_facility(
            facility_id,
            {"status": status_data.status},
            storage=None,
        )

        return {
            "status": "success",
            "message": "Facility status updated successfully",
            "data": updated_facility,
        }
    except Exception as e:
        handle_exception(e)
    

@router.post(
    "/room-type",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_by_alias=False,
)
async def create_room_type(
    room_type_data: CreateRoomType,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> RoomTypeResponse:
        try:
            new_room_type = {
                "name": room_type_data.name,
                "capacity": room_type_data.capacity,
                "status": room_type_data.status
            }

            room_type_id = await attribute_service.create_room_type(new_room_type)

            room_type = await attribute_service.get_room_type(room_type_id)

            return {
                "status": "success",
                "message": "Room type created successfully",
                "data": room_type
            }

        except Exception as e:
            handle_exception(e)


@router.get(
    "/room-type/{room_type_id}",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def get_room_type(
    room_type_id: str,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> RoomTypeResponse:
    try:
        room_type = await attribute_service.get_room_type(room_type_id)
        if not room_type:
            raise HTTPException(status_code=404, detail="Room type not found")
        return {
            "status": "success",
            "message": "Room type retrieved successfully",
            "data": room_type
        }
    except Exception as e:
        handle_exception(e)


@router.get(
    "/room-types",
    response_model=RoomTypesResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def list_room_types(
    params: ListRoomTypes = Depends(),
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> RoomTypesResponse:
        try:
            search = build_search(
            name=params.name,
            status=params.status,
            
        )
            
            
            result = await attribute_service.list_room_types(
                page=params.page,
                size=params.size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                search=search,
            )
            return {
                "status": "success",
                "message": "Room types retrieved successfully",
                "meta": {
                    "total": result["total"],
                    "page": result["page"],
                    "size": result["size"],
                },
                "data": result["items"],
            }
        except Exception as e:
            handle_exception(e)

@router.patch(
    "/room-type/{room_type_id}",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_room_type(
    room_type_id: str,
    room_type_data: UpdateRoomType,
    attribute_service: AttributeService = Depends(get_attribute_service),
):
    try:
        update_data = room_type_data.model_dump(exclude_none=True)

        updated_room_type = await attribute_service.update_room_type(
            room_type_id,
            update_data,
        )

        return {
            "status": "success",
            "message": "Room type updated successfully",
            "data": updated_room_type
        }

    except Exception as e:
        handle_exception(e)

@router.patch(
    "/room-type/{room_type_id}/status",
    response_model=RoomTypeResponse,
    status_code=status.HTTP_200_OK,
    response_model_by_alias=False,
)
async def update_room_type_status(
    room_type_id: str,
    status_data: UpdateRoomTypeStatus,
    attribute_service: AttributeService = Depends(get_attribute_service),
) -> RoomTypeResponse:
    try:
        updated_room_type = await attribute_service.update_room_type(
            room_type_id,
            {"status": status_data.status},
        )

        return {
            "status": "success",
            "message": "Room type status updated successfully",
            "data": updated_room_type,
        }
    except Exception as e:
        handle_exception(e)