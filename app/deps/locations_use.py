from fastapi import Depends
from app.application.use_cases.locations.location import CreateLocationUseCase, GetLocationUseCase, GetLocationsUseCase, UpdateLocationUseCase
from app.deps.services import get_location_service, get_storage_service
from app.deps.uow import get_uow
from app.deps.auth import CurrentUser, get_current_user, require_admin

from app.application.use_cases.locations.city import CreateCityUseCase, GetCitiesUseCase, GetCityUseCase, UpdateCityUseCase, GetCityBySlugUseCase, UpdateCityBySlugUseCase

from app.application.use_cases.locations.country import CreateCountryUseCase, GetCountryUseCase, GetCountriesUseCase, UpdateCountryStatusUseCase, UpdateCountryUseCase    

# City Use Cases Start Here
def get_create_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return CreateCityUseCase(service, storage, current_user, uow)

def get_list_cities_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return GetCitiesUseCase(service, storage, current_user, uow)

def get_single_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return GetCityUseCase(service, storage, current_user, uow)

def get_update_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return UpdateCityUseCase(service, storage, current_user, uow)

def get_city_by_slug_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return GetCityBySlugUseCase(service, storage, current_user, uow)

def get_update_city_by_slug_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow)
):
    return UpdateCityBySlugUseCase(service, storage, current_user, uow)

# City Use Cases End Here


# Country Use Cases Start Here
def get_create_country_use_case(
    service=Depends(get_location_service),
   current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return CreateCountryUseCase(service, current_user, uow)


def get_single_country_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return GetCountryUseCase(service, current_user, uow)


def get_list_countries_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return GetCountriesUseCase(service, current_user, uow)


def get_update_country_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return UpdateCountryUseCase(service, current_user, uow)


def get_update_country_status_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return UpdateCountryStatusUseCase(service, current_user, uow)

# Country Use Cases End Here


# Location Use Cases Start Here
def get_create_location_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return CreateLocationUseCase(service, current_user, uow)


def get_list_locations_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return GetLocationsUseCase(service, current_user, uow)

def get_single_location_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return GetLocationUseCase(service, current_user, uow)

def get_update_location_use_case(
    service=Depends(get_location_service),
    current_user : CurrentUser=Depends(require_admin),
    uow=Depends(get_uow),
):
    return UpdateLocationUseCase(service, current_user, uow)