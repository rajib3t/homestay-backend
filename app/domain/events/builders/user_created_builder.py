from typing import Dict, Any

from app.domain.events.base_event import BaseEvent
from app.domain.events.builders.base_builder import EventBuilder


class UserCreatedEventBuilder(EventBuilder):
    """Builder for UserCreatedEvent"""
    
    @property
    def event_type(self) -> str:
        return "USER_CREATED"
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        from app.domain.events.user_events import UserCreatedEvent
        
        payload = data["payload"]
        return UserCreatedEvent(
            user_id=payload["user_id"],
            email=payload["email"],
            username=payload.get("username", payload.get("email", "").split("@")[0])
        )
