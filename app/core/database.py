from typing import Optional
import asyncio
import logging
from urllib.parse import quote_plus, urlsplit, urlunsplit, parse_qsl, urlencode

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None


db = MongoDB()


def normalize_mongo_uri(uri: str) -> str:
    """Escape MongoDB username/password credentials when needed.

    Motor/PyMongo expects reserved characters in the userinfo portion of the URI
    to be percent-encoded. This keeps already-valid URIs intact and only rewrites
    the credentials segment when present.
    """
    if not uri:
        return uri

    parsed = urlsplit(uri)
    if not parsed.username and not parsed.password:
        return uri

    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"

    if parsed.username is not None:
        username = quote_plus(parsed.username)
        if parsed.password is not None:
            password = quote_plus(parsed.password)
            netloc = f"{username}:{password}@{host}"
        else:
            netloc = f"{username}@{host}"
    else:
        netloc = host

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def add_direct_connection(uri: str) -> str:
    """Append directConnection=true to a MongoDB URI if it's not already set."""
    if not uri:
        return uri

    parsed = urlsplit(uri)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    if query.get("directConnection", "").lower() == "true":
        return uri

    query["directConnection"] = "true"
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def strip_replica_set_options(uri: str) -> str:
    """Remove replica-set-specific options for standalone fallback connections."""
    if not uri:
        return uri

    parsed = urlsplit(uri)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.pop("replicaSet", None)
    query.pop("directConnection", None)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


async def connect_to_mongo(retries: int = 3, backoff_factor: float = 0.5):
    """Attempt to connect to MongoDB with a small retry/backoff strategy.

    Raises the last exception on failure.
    """
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.debug("Connecting to MongoDB (attempt %d)", attempt)
            # Set a server selection timeout to fail faster if unreachable
            mongo_uri = normalize_mongo_uri(settings.MONGO_URI)
            if settings.MONGO_DIRECT_CONNECTION:
                mongo_uri = add_direct_connection(mongo_uri)
            db.client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify the connection by pinging the server
            await db.client.admin.command("ping")
            logger.info("Connected to MongoDB successfully")
            return
        except ServerSelectionTimeoutError as e:
            last_exc = e
            logger.warning("MongoDB connection attempt %d failed: %s", attempt, e)

            if not settings.MONGO_DIRECT_CONNECTION:
                try:
                    fallback_uri = strip_replica_set_options(
                        add_direct_connection(normalize_mongo_uri(settings.MONGO_URI))
                    )
                    logger.info("Retrying MongoDB connection with directConnection=true")
                    db.client = AsyncIOMotorClient(fallback_uri, serverSelectionTimeoutMS=5000)
                    await db.client.admin.command("ping")
                    logger.info("Connected to MongoDB successfully using direct connection fallback")
                    return
                except Exception as fallback_exc:
                    last_exc = fallback_exc
                    logger.warning("Direct connection fallback failed: %s", fallback_exc)
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
