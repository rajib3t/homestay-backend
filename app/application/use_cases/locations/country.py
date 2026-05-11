from app.application.dto.country_query import CountryQuery
from app.core.exceptions import AppException
from app.domain.events.country_event import CountryCreatedEvent, CountryUpdatedEvent
from app.application.use_cases.base_use_case import BaseUseCase

class CreateCountryUseCase(BaseUseCase):
    def __init__(self, location_service, current_user, uow):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, payload):
        payload["created_by"] = self.current_user.id
        
        async with self.uow as uow:
            session = uow.get_session()

            country_id = await self.location_service.create_country(
                payload, session=session
            )

            uow.collect_event(CountryCreatedEvent(country_id, self.current_user.id))

        return await self._build_country_response(country_id)
    

    async def _build_country_response(self, country_id):
        country = await self.location_service.get_country(country_id)
        if not country:
            raise AppException(404, "Country not found")
        return country
    

class GetCountryUseCase(BaseUseCase):
    def __init__(self, location_service, current_user, uow):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow
    
    async def execute(self, country_id):
        
        async with self.uow as uow:
            session = uow.get_session()

            country = await self.location_service.get_country(country_id, session=session)

        if not country:
            raise AppException(404, "Country not found")

        return await self.build_response(country)
    
    async def build_response(self, country):
        
        return country


class GetCountriesUseCase(BaseUseCase):
    def __init__(self, location_service, current_user, uow):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow
    
    async def execute(self, query: CountryQuery):
        async with self.uow as uow:
            session = uow.get_session()

            

            countries = await self.location_service.list_countries(
                query=query,
                session=session,
            )

        return await self.build_response(countries)

    
    

    
    async def build_response(self, countries):
        
        return countries




class UpdateCountryUseCase(BaseUseCase):
    def __init__(self, location_service, current_user, uow):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, country_id, payload):
        payload["updated_by"] = self.current_user.id
        
        async with self.uow as uow:
            session = uow.get_session()

            country = await self.location_service.update_country(
                country_id, payload, session=session
            )
            uow.collect_event(CountryUpdatedEvent(country_id, self.current_user.id))
        return await self.build_response(country)   
    


    async def build_response(self, country):
        
        if not country:
            raise AppException(404, "Country not found")

        return country



# use_cases/update_country_status.py

class UpdateCountryStatusUseCase(BaseUseCase):

    def __init__(self, location_service, current_user, uow):
        self.location_service = location_service
        self.current_user = current_user
        self.uow = uow

    async def execute(self, country_id: str):

        async with self.uow as uow:

            country = await self.location_service.toggle_country_status(
                country_id=country_id,
                updated_by=self.current_user.id,
                session=uow.get_session(),
            )

            uow.collect_event(
                CountryUpdatedEvent(
                    country["id"],
                    self.current_user.id
                )
            )

            return await self.build_response(country)


    async def build_response(self, country):
        
        if not country:
            raise AppException(404, "Country not found")

        return country