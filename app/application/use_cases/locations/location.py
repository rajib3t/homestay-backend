from app.application.dto.location_query import LocationQuery
from app.application.use_cases.base_use_case import BaseUseCase


class CreateLocationUseCase(BaseUseCase):

    def __init__(
        self,
        location_service,
        current_user,
        uow,
    ):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, payload: dict):

        payload["created_by"] = self.current_user.id

        async with self.uow as uow:
            session = uow.get_session()

            location = await self.location_service.create_location(
                payload=payload,
                session=session,
            )

            # uow.collect_event(...)

        return location
    

class GetLocationsUseCase(BaseUseCase):

    def __init__(
        self,
        location_service,
        current_user,
        uow,
    ):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, query: LocationQuery):

        async with self.uow as uow:
            session = uow.get_session()

            return await self.location_service.list_locations(
                query=query,
                session=session,
            )
        

class GetLocationUseCase(BaseUseCase):

    def __init__(
        self,
        location_service,
        current_user,
        uow,
    ):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(
        self,
        location_id: str,
    ):

        async with self.uow as uow:

            session = uow.get_session()

            return await self.location_service.get_location(
                location_id=location_id,
                session=session,
            )
        

class UpdateLocationUseCase(BaseUseCase):

    def __init__(
        self,
        location_service,
        current_user,
        uow,
    ):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(
        self,
        location_id: str,
        payload: dict,
    ):

        payload["updated_by"] = self.current_user.id

        async with self.uow as uow:
            session = uow.get_session()

            return await self.location_service.update_location(
                location_id=location_id,
                payload=payload,
                session=session,
            )