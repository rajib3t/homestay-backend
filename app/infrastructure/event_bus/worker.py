# app/infrastructure/event_bus/worker.py

import json
import asyncio
import logging

from app.core.redis import get_redis
from app.core.database import get_database
from app.repositories.outbox_repository import OutboxRepository
from bson import ObjectId

from app.domain.events.event_factory import event_factory
from app.infrastructure.email.user_handlers import send_welcome_email_handler
from app.infrastructure.handlers.country_handlers import log_country_created_handler, log_country_updated_handler   
from app.infrastructure.handlers.user_handlers import log_user_updated_handler
 
logger = logging.getLogger(__name__)

# =========================================================
# COUNTRY EVENT HANDLERS
# =========================================================





# =========================================================
# EVENT -> HANDLER MAP
# =========================================================

EVENT_HANDLER_MAP = {
    "USER_CREATED": [
        send_welcome_email_handler
    ],
    "USER_UPDATED": [
        log_user_updated_handler
    ],
    "COUNTRY_CREATED": [
        log_country_created_handler
    ],
    "COUNTRY_UPDATED": [
        log_country_updated_handler
    ]
}

MAX_RETRIES = 5


# =========================================================
# REBUILD DOMAIN EVENT
# =========================================================

def rebuild_event(event_name: str, data: dict):
    """
    Rebuild event using the event factory pattern.
    
    This function replaces the monolithic if-else structure with a clean,
    extensible factory pattern that can handle any registered event type.
    """
    try:
        return event_factory.create_event(event_name, data)
    except ValueError as e:
        logger.error(f"Failed to rebuild event {event_name}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error rebuilding event {event_name}: {e}")
        raise


# =========================================================
# PROCESS SINGLE EVENT
# =========================================================

async def process_event(payload: dict):

    event_name = payload["event"]
    data = payload["data"]

    logger.info(f"Processing event: {event_name}")

    event = rebuild_event(event_name, data)

    handlers = EVENT_HANDLER_MAP.get(event_name, [])

    if not handlers:
        logger.warning(f"No handlers found for event: {event_name}")
        return

    for handler in handlers:
        try:
            await handler(event)

            logger.info(
                f"Handler executed: {handler.__name__}"
            )

        except Exception as e:
            logger.exception(
                f"Handler failed: {handler.__name__}"
            )
            raise e
    
    # Mark event as processed in database
    await mark_event_processed(data.get("id"))


# =========================================================
# MARK EVENT PROCESSED
# =========================================================

async def mark_event_processed(event_id: str):
    """Mark event as processed in the database"""
    if not event_id:
        logger.warning("No event ID provided for marking as processed")
        return
    
    try:
        db = get_database()
        outbox_repo = OutboxRepository(db)
        
        # Convert string ID to ObjectId if needed
        try:
            object_id = ObjectId(event_id)
        except:
            object_id = event_id
        
        await outbox_repo.mark_processed(object_id)
        logger.info(f"Event {event_id} marked as processed")
        
    except Exception as e:
        logger.exception(f"Failed to mark event {event_id} as processed: {e}")


# =========================================================
# HANDLE FAILED EVENT
# =========================================================

async def handle_failure(redis, raw, payload):

    retry_count = payload.get("retry_count", 0) + 1

    payload["retry_count"] = retry_count

    # remove failed item from processing queue
    await redis.lrem("event_processing", 1, raw)

    if retry_count > MAX_RETRIES:

        logger.error(
            f"Moving event to DLQ after {MAX_RETRIES} retries"
        )

        await redis.lpush(
            "event_dlq",
            json.dumps(payload)
        )

    else:

        logger.warning(
            f"Retrying event ({retry_count}/{MAX_RETRIES})"
        )

        await redis.lpush(
            "event_queue",
            json.dumps(payload)
        )


# =========================================================
# MAIN WORKER LOOP
# =========================================================

async def worker_loop():

    redis = get_redis()

    logger.info("🚀 Event worker started")

    while True:

        raw = None
        payload = None

        try:

            # -------------------------------------------------
            # BLOCKING POP
            #
            # Move event from:
            # event_queue -> event_processing
            # -------------------------------------------------

            raw = await redis.brpoplpush(
                "event_queue",
                "event_processing",
                timeout=5
            )

            # no message
            if raw is None:
                await asyncio.sleep(1)
                continue

            # decode bytes -> string
            if isinstance(raw, bytes):
                raw = raw.decode()

            # parse json
            payload = json.loads(raw)

            logger.info(f"Received event: {payload}")

            # process event
            await process_event(payload)

            # -------------------------------------------------
            # SUCCESS
            #
            # Remove from processing queue
            # -------------------------------------------------

            await redis.lrem(
                "event_processing",
                1,
                raw
            )

            logger.info("Event processed successfully")

        except Exception as e:

            logger.exception(f"Worker failed: {e}")

            if raw and payload:
                await handle_failure(
                    redis,
                    raw,
                    payload
                )

            await asyncio.sleep(1)