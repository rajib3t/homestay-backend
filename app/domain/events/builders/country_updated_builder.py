from typing import Dict, Any

from app.domain.events.base_event import BaseEvent
from app.domain.events.builders.base_builder import EventBuilder


class CountryUpdatedEventBuilder(EventBuilder):
    """Builder for CountryUpdatedEvent"""
    
    @property
    def event_type(self) -> str:
        return "COUNTRY_UPDATED"
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        from app.domain.events.country_event import CountryUpdatedEvent
        
        payload = data["payload"]
        return CountryUpdatedEvent(
            country_id=payload["country_id"],
            updated_by=payload["updated_by"]
        )
