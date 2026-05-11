from app.domain.events.base_event import BaseEvent
class CityCreatedEvent(BaseEvent):
    def __init__(self, city_id: str, created_by: str):
        super().__init__(
            aggregate_id=city_id,
            event_type="CITY_CREATED",
            payload={
                "city_id": city_id,
                "created_by": created_by,
            },
        )
