import argparse
import asyncio
import logging

from app.models.user_model import UserCreate
from app.core.database import close_mongo_connection, connect_to_mongo, get_database
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a user from the terminal")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--user-type", required=True, choices=["admin", "user", "vendor"])
    parser.add_argument("--first-name", required=True)
    parser.add_argument("--last-name", required=True)
    parser.add_argument("--mobile", required=True)
    parser.add_argument("--image", default=None)
    return parser


async def main():
    parser = build_parser()
    args = parser.parse_args()

    payload = UserCreate(
        username=args.username,
        email=args.email,
        password=args.password,
        user_type=args.user_type,
        first_name=args.first_name,
        last_name=args.last_name,
        mobile=args.mobile,
        image=args.image,
    ).model_dump()

    await connect_to_mongo()
    try:
        db = get_database()
        service = UserService(UserRepository(db))
        existing = await service.repository.find_by_email(payload["email"])
        if existing:
            raise AppException(
                status_code=409,
                message="User with this email already exists",
                error_code="EMAIL_EXISTS",
                field="email",
            )

        payload["password"] = PasswordHasher.hash_password(payload["password"])
        service.timestamps(payload, is_new=True)
        result = await service.repository.insert(payload)
        logger.info("User created with id: %s", result.inserted_id)
    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(main())
