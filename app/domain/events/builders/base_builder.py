from typing import Dict, Any
from abc import ABC

from app.domain.events.base_event import BaseEvent


class EventBuilder(ABC):
    """Abstract base class for event builders"""
    
    def build(self, data: Dict[str, Any]) -> BaseEvent:
        """Build an event from provided data"""
        pass
    
    @property
    def event_type(self) -> str:
        """Return the event type this builder handles"""
        pass
