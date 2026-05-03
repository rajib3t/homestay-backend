# app/infrastructure/queue/redis.py

import redis
from app.core.config import settings

def get_redis_connection():
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )