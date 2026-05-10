from app.domain.events.base_event import BaseEvent
class CountryCreatedEvent(BaseEvent):
    def __init__(self, country_id: str, created_by: str):
        super().__init__(
            aggregate_id=country_id,
            event_type="COUNTRY_CREATED",
            payload={
                "country_id": country_id,
                "created_by": created_by,
            },
        )

class CountryUpdatedEvent(BaseEvent):
    def __init__(self, country_id: str, updated_by: str):
        super().__init__(
            aggregate_id=country_id,
            event_type="COUNTRY_UPDATED",
            payload={
                "country_id": country_id,
                "updated_by": updated_by,
            },
        )