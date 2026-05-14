from fastapi import Depends


from app.application.use_cases.attribute.amenity  import CreateAmenityUseCase, GetAmenitiesUseCase, GetAmenityUseCase, UpdateAmenityUseCase
from app.application.use_cases.attribute.facility import CreateFacilityUseCase, GetFacilitiesUseCase, GetFacilityUseCase, UpdateFacilityUseCase
from app.deps.auth import get_current_user
from app.deps.services import get_attribute_service, get_storage_service
from app.deps.uow import get_uow


# Dependency injection functions for Amenity use cases

def get_create_amenity_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return CreateAmenityUseCase(
        service, 
        storage_service, 
        current_user,
        uow
    )


def get_list_amenities_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetAmenitiesUseCase(
        service,
        storage_service,
        current_user,
        uow
    )


def get_single_amenity_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetAmenityUseCase(
        service,
        storage_service,
        current_user,
        uow
    )

def get_single_amenity_update_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return UpdateAmenityUseCase(
        service,
        storage_service,
        current_user,
        uow
    )

# Similar dependency functions can be created for Facility and other attribute use cases as needed

def get_create_facility_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return CreateFacilityUseCase(
        service, 
        storage_service, 
        current_user,
        uow
    )

def get_list_facilities_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetFacilitiesUseCase(
        service,
        storage_service,
        current_user,
        uow
    )

def get_single_facility_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    # This function can be implemented similarly to get_single_amenity_use_case when the GetFacilityUseCase is defined
    return GetFacilityUseCase(
        service,
        storage_service,
        current_user,
        uow
    )


def get_single_facility_update_use_case(
    service=Depends(get_attribute_service),
    storage_service=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    # This function can be implemented similarly to get_single_amenity_update_use_case when the UpdateFacilityUseCase is defined
    return UpdateFacilityUseCase(
        service,
        storage_service,
        current_user,
        uow
    )
