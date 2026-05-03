# app/infrastructure/event_bus/redis_event_bus.py

import json
from app.core.redis import get_redis


class RedisEventBus:

    def __init__(self):
        self.redis = get_redis()
        self.queue_name = "event_queue"

    async def publish(self, event):
        payload = {
            "event": event.__class__.__name__,
            "data": event.__dict__,
        }

        await self.redis.lpush(self.queue_name, json.dumps(payload))