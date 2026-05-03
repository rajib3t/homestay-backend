"""Event bus and event handler setup."""


from app.infrastructure.event_bus.event_bus import EventBus
from app.domain.events.user_events import UserCreatedEvent
from app.infrastructure.email.user_handlers import send_welcome_email_handler
from app.infrastructure.event_bus.redis_event_bus import RedisEventBus


_event_bus = EventBus()
_event_bus.register(UserCreatedEvent, send_welcome_email_handler)


def get_event_bus():
    """Get the global event bus instance."""
    print(f"[DEBUG] Returning event bus instance: {RedisEventBus()}")
    return RedisEventBus()
