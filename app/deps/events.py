from fastapi import Depends

from app.infrastructure.event_bus.redis_event_bus import RedisEventBus
from app.infrastructure.event_bus.outbox_publisher import OutboxPublisher
from app.repositories.outbox_repository import OutboxRepository
from app.core.database import get_database


_redis_event_bus = RedisEventBus()


def get_event_bus():
    return _redis_event_bus


def get_outbox_publisher(
    db=Depends(get_database),
):
    outbox_repo = OutboxRepository(db)

    return OutboxPublisher(
        outbox_repo=outbox_repo,
        event_bus=_redis_event_bus,
    )