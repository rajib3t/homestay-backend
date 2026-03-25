from typing import Optional
import logging

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisConnection:
    client: Optional[Redis] = None


redis_connection = RedisConnection()


def _build_redis_client():
    if settings.REDIS_URL:
        return Redis.from_url(settings.REDIS_URL, decode_responses=True)

    if settings.REDIS_HOST:
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    return None


async def connect_to_redis():
    client = _build_redis_client()
    if client is None:
        logger.info("Redis is not configured; skipping connection")
        return

    redis_connection.client = client
    await redis_connection.client.ping()
    logger.info("Connected to Redis successfully")


async def close_redis_connection():
    if not redis_connection.client:
        return

    try:
        await redis_connection.client.aclose()
        logger.info("Redis connection closed")
    except Exception:
        logger.exception("Error while closing Redis connection")
    finally:
        redis_connection.client = None


def get_redis():
    return redis_connection.client