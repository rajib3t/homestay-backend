from app.core.exceptions import AppException
from app.domain.events.country_event import CountryCreatedEvent
class CreateCountryUseCase:
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
    

