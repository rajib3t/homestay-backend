#!/usr/bin/env python3

import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.redis import connect_to_redis, close_redis_connection
from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.infrastructure.event_bus.worker import worker_loop
from app.infrastructure.event_bus.outbox_publisher import OutboxPublisher, outbox_loop
from app.repositories.outbox_repository import OutboxRepository
from app.core.logging_config import configure_logging

async def main():
    # Configure logging
    configure_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Connect to Redis and Database
        await connect_to_redis()
        await connect_to_mongo()
        logger.info("🔗 Redis connected")
        logger.info("🗄️  Database connected")
        
        # Start outbox publisher and worker loops
        logger.info("🚀 Starting event worker...")
        
        # Create outbox publisher
        db = get_database()
        outbox_repo = OutboxRepository(db)
        outbox_publisher = OutboxPublisher(outbox_repo)
        
        # Run both loops concurrently
        worker_task = asyncio.create_task(worker_loop())
        outbox_task = asyncio.create_task(outbox_loop(outbox_publisher))
        
        # Wait for both tasks
        await asyncio.gather(worker_task, outbox_task)
        
        logger.info("Completed processing events")
    except KeyboardInterrupt:
        logger.info("⏹️  Worker stopped by user")
    except Exception as e:
        logger.exception(f"❌ Worker failed: {e}")
    finally:
        await close_redis_connection()
        await close_mongo_connection()
        logger.info("🔌 Redis and Database disconnected")

if __name__ == "__main__":
    asyncio.run(main())
