from typing import Dict, Any

from app.domain.events.base_event import BaseEvent
from app.domain.events.builders.base_builder import EventBuilder


class CityCreatedEventBuilder(EventBuilder):
    """Builder for CityCreatedEvent"""
    
    @property
    def event_type(self) -> str:
        return "CITY_CREATED"
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        from app.domain.events.city_event import CityCreatedEvent
        
        payload = data["payload"]
        return CityCreatedEvent(
            city_id=payload["city_id"],
            name=payload["name"],
            country=payload["country"],
            created_by=payload["created_by"]
        )
