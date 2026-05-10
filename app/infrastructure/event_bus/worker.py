# app/infrastructure/event_bus/worker.py

import json
import asyncio
import logging

from app.core.redis import get_redis

from app.domain.events.user_events import UserCreatedEvent
from app.infrastructure.email.user_handlers import send_welcome_email_handler

logger = logging.getLogger(__name__)

# =========================================================
# EVENT -> HANDLER MAP
# =========================================================

EVENT_HANDLER_MAP = {
    "USER_CREATED": [
        send_welcome_email_handler
    ]
}

MAX_RETRIES = 5


# =========================================================
# REBUILD DOMAIN EVENT
# =========================================================

def rebuild_event(event_name: str, data: dict):

    if event_name == "USER_CREATED":
        return UserCreatedEvent(**data)

    raise ValueError(f"Unknown event: {event_name}")


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