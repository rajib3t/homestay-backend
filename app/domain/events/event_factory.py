from typing import Dict, Type, Any
from abc import ABC, abstractmethod

from app.domain.events.base_event import BaseEvent


class EventBuilder(ABC):
    """Abstract base class for event builders"""
    
    @abstractmethod
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        """Build an event from the provided data"""
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Return the event type this builder handles"""
        pass


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


class EventFactory:
    """Factory for creating events from data"""
    
    def __init__(self):
        self._builders: Dict[str, EventBuilder] = {}
        self._register_default_builders()
    
    def _register_default_builders(self):
        """Register default event builders"""
        self.register_builder(UserCreatedEventBuilder())
        self.register_builder(UserUpdatedEventBuilder())
        self.register_builder(CountryCreatedEventBuilder())
    
    def register_builder(self, builder: EventBuilder):
        """Register a new event builder"""
        self._builders[builder.event_type] = builder
    
    def create_event(self, event_type: str, data: Dict[str, Any]) -> BaseEvent:
        """Create an event from the given type and data"""
        builder = self._builders.get(event_type)
        
        if not builder:
            raise ValueError(f"Unknown event type: {event_type}")
        
        return builder.build(data)
    
    def get_supported_events(self) -> list[str]:
        """Get list of supported event types"""
        return list(self._builders.keys())


# Global event factory instance
event_factory = EventFactory()
