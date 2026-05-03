"""Event bus and event handler setup."""
from app.infrastructure.event_bus.event_bus import EventBus
from app.domain.events.user_events import UserCreatedEvent
from app.infrastructure.email.user_handlers import send_welcome_email_handler


_event_bus = EventBus()
_event_bus.register(UserCreatedEvent, send_welcome_email_handler)


def get_event_bus():
    """Get the global event bus instance."""
    return _event_bus
