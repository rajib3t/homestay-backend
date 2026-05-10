from fastapi import Depends
from app.deps.services import get_location_service, get_storage_service
from app.deps.uow import get_uow
from app.deps.auth import get_current_user

from app.application.use_cases.locations.create_city import CreateCityUseCase

from app.application.use_cases.locations.country import CreateCountryUseCase


def get_create_city_use_case(
    service=Depends(get_location_service),
    storage=Depends(get_storage_service),
    current_user=Depends(get_current_user),
):
    return CreateCityUseCase(service, storage, current_user)

def get_create_country_use_case(
    service=Depends(get_location_service),
    current_user=Depends(get_current_user),
    uow=Depends(get_uow),
):
    return CreateCountryUseCase(service, current_user, uow)
