from typing import Dict, Any

from app.domain.events.base_event import BaseEvent
from app.domain.events.builders.base_builder import EventBuilder


class CountryCreatedEventBuilder(EventBuilder):
    """Builder for CountryCreatedEvent"""
    
    @property
    def event_type(self) -> str:
        return "COUNTRY_CREATED"
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        from app.domain.events.country_event import CountryCreatedEvent
        
        payload = data["payload"]
        return CountryCreatedEvent(
            country_id=payload["country_id"],
            created_by=payload["created_by"]
        )
