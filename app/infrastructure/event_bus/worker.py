# app/infrastructure/event_bus/worker.py

import json
import asyncio

from app.core.redis import get_redis

from app.domain.events.user_events import UserCreatedEvent
# from app.domain.events.token_events import TokenCreatedEvent

from app.infrastructure.email.user_handlers import send_welcome_email_handler
# from app.infrastructure.logging.token_handlers import log_token_created_handler


EVENT_HANDLER_MAP = {
    "UserCreatedEvent": [send_welcome_email_handler],
    # "TokenCreatedEvent": [log_token_created_handler],
}


async def process_event(payload):
    event_name = payload["event"]
    data = payload["data"]

    event = rebuild_event(event_name, data)

    handlers = EVENT_HANDLER_MAP.get(event_name, [])

    for handler in handlers:
        try:
            await handler(event)
        except Exception as e:
            print(f"[ERROR] Handler failed: {handler.__name__}, {e}")


def rebuild_event(event_name, data):
    if event_name == "UserCreatedEvent":
        return UserCreatedEvent(**data)

    # if event_name == "TokenCreatedEvent":
    #     return TokenCreatedEvent(**data)

    raise ValueError(f"Unknown event: {event_name}")


async def worker_loop():
    redis = get_redis()
    queue_name = "event_queue"

    print("🚀 Event worker started...")

    while True:
        _, raw = await redis.brpop(queue_name)  # blocking pop
        payload = json.loads(raw)

        await process_event(payload)