from typing import Optional
import asyncio
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None


db = MongoDB()


async def connect_to_mongo(retries: int = 3, backoff_factor: float = 0.5):
    """Attempt to connect to MongoDB with a small retry/backoff strategy.

    Raises the last exception on failure.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.debug("Connecting to MongoDB (attempt %d)", attempt)
            # Set a server selection timeout to fail faster if unreachable
            db.client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
            # Verify the connection by pinging the server
            await db.client.admin.command("ping")
            logger.info("Connected to MongoDB successfully")
            return
        except Exception as e:
            last_exc = e
            logger.warning("MongoDB connection attempt %d failed: %s", attempt, e)
            if attempt < retries:
                await asyncio.sleep(backoff_factor * (2 ** (attempt - 1)))

    logger.error("Could not connect to MongoDB after %d attempts", retries)
    raise last_exc


async def close_mongo_connection():
    if db.client:
        try:
            db.client.close()
            logger.info("MongoDB connection closed")
        except Exception:
            logger.exception("Error while closing MongoDB connection")


def get_database():
    if not db.client:
        raise RuntimeError("Database client is not initialized")
    return db.client.get_default_database()


def get_client():
    if not db.client:
        raise RuntimeError("Mongo client is not initialized")
    return db.client