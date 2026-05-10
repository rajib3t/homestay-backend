# app/infrastructure/event_bus/outbox_publisher.py

import json
import asyncio
import logging

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class OutboxPublisher:

    def __init__(self, outbox_repo):
        self.outbox_repo = outbox_repo
        self.redis = get_redis()

    async def publish_pending(self):

        events = await self.outbox_repo.get_unprocessed_events()

        if not events:
            return

        logger.info(f"Found {len(events)} pending events")

        for event in events:

            try:

                payload = {
                    "event": event["event_type"],
                    "data": event["payload"]
                }

                # -----------------------------------------
                # PUSH TO REDIS QUEUE
                # -----------------------------------------

                await self.redis.lpush(
                    "event_queue",
                    json.dumps(payload)
                )

                # -----------------------------------------
                # MARK PROCESSED IN OUTBOX
                # -----------------------------------------

                await self.outbox_repo.mark_processed(
                    event["_id"]
                )

                logger.info(
                    f"Published event: {event['event_type']}"
                )

            except Exception as e:

                logger.exception(
                    f"Failed publishing event: {e}"
                )


# =========================================================
# LOOP
# =========================================================

async def outbox_loop(outbox_publisher):

    logger.info("🚀 Outbox publisher started")

    while True:

        try:

            await outbox_publisher.publish_pending()

        except Exception as e:

            logger.exception(
                f"Outbox loop failed: {e}"
            )

        await asyncio.sleep(2)