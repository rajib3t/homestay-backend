from fastapi.params import Depends

from app.application.use_cases.property.create_property_use_case import CreatePropertyUseCase
from app.application.use_cases.property.get_properties_use_case import GetPropertiesUseCase
from app.application.use_cases.property.get_property_use_case import GetPropertyUseCase
from app.deps.auth import CurrentUser, get_current_user
from app.deps.services import get_property_service, get_storage_service
from app.deps.uow import get_uow
from app.infrastructure.uow.mongo_uow import MongoUnitOfWork
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService

async def get_property_create_use_case(
    service : PropertyService=Depends(get_property_service),
    storage : StorageService=Depends(get_storage_service),

    current_user : CurrentUser=Depends(get_current_user),
    uow : MongoUnitOfWork=Depends(get_uow),
):
    return CreatePropertyUseCase(service, storage, current_user, uow)


async def get_property_list_use_case(
    service : PropertyService=Depends(get_property_service),
    current_user : CurrentUser=Depends(get_current_user),
    storage : StorageService=Depends(get_storage_service),
    uow : MongoUnitOfWork=Depends(get_uow),
) -> GetPropertiesUseCase:
    
    return GetPropertiesUseCase(service, current_user, storage, uow)


async def get_property_use_case(
    service : PropertyService=Depends(get_property_service),
    current_user : CurrentUser=Depends(get_current_user),
    storage : StorageService=Depends(get_storage_service),
    uow : MongoUnitOfWork=Depends(get_uow),
) -> GetPropertyUseCase:
    return GetPropertyUseCase(service, current_user, storage, uow)