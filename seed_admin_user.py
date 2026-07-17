import asyncio
import logging

from app.core.database import connect_to_mongo, close_mongo_connection, get_database
from app.repositories.user_repository import UserRepository
from app.seeds.admin_user_seeder import AdminUserSeeder


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await connect_to_mongo()
    try:
        db = get_database()
        seeder = AdminUserSeeder(UserRepository(db))
        result = await seeder.seed()
        logger.info("Admin seed result: %s", result)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
