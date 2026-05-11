from fastapi import Depends
from app.deps.services import get_location_service, get_storage_service
from app.deps.uow import get_uow
from app.deps.auth import get_current_user

from app.application.use_cases.locations.city import CreateCityUseCase, GetCitiesUseCase, GetCityUseCase

from app.application.use_cases.locations.country import CreateCountryUseCase, GetCountryUseCase, GetCountriesUseCase, UpdateCountryStatusUseCase, UpdateCountryUseCase    

# City Use Cases Start Here
def get_create_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return CreateCityUseCase(service, storage, current_user, uow)

def get_list_cities_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetCitiesUseCase(service, storage, current_user, uow)

def get_single_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow)
):
    return GetCityUseCase(service, storage, current_user, uow)

# City Use Cases End Here


# Country Use Cases Start Here
def get_create_country_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return CreateCountryUseCase(service, current_user, uow)


def get_single_country_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return GetCountryUseCase(service, current_user, uow)


def get_list_countries_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return GetCountriesUseCase(service, current_user, uow)


def get_update_country_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return UpdateCountryUseCase(service, current_user, uow)


def get_update_country_status_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return UpdateCountryStatusUseCase(service, current_user, uow)

# Country Use Cases End Here
