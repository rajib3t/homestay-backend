# app/infrastructure/event_bus/redis_event_bus.py

import logging

from app.core.json_utils import dumps as json_dumps
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class RedisEventBus:

    def __init__(self):

        self.redis = get_redis()

        self.queue_name = "event_queue"

    async def publish(self, event):

        payload = {
            "event": event.event_type,
            "data": event.payload,
        }

        await self.redis.lpush(
            self.queue_name,
            json_dumps(payload)
        )

        logger.info(
            f"Event published: {event.event_type}"
        )