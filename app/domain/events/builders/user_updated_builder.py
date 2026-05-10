from typing import Dict, Any

from app.domain.events.base_event import BaseEvent
from app.domain.events.builders.base_builder import EventBuilder


class UserUpdatedEventBuilder(EventBuilder):
    """Builder for UserUpdatedEvent"""
    
    @property
    def event_type(self) -> str:
        return "USER_UPDATED"
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        from app.domain.events.user_events import UserUpdatedEvent
        
        payload = data["payload"]
        return UserUpdatedEvent(
            user_id=payload["user_id"],
            updated_by=payload["updated_by"]
        )
