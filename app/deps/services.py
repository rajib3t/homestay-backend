"""Service dependency factories."""
from fastapi import Depends
from app.core.database import get_database
from app.core.redis import get_redis
from app.core.config import settings
from app.services.address_service import AddressService
from app.services.attribute_service import AttributeService
from app.services.company_service import CompanyService
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.services.location_service import LocationService
from app.services.storage_service import StorageService
from app.repositories.address_repository import AddressRepository
from app.repositories.attribute_repository import AttributeRepository
from app.repositories.company_repository import CompanyRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.redis_token_repository import RedisTokenRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository


def get_user_service(db=Depends(get_database)):
    """Get the user service with its dependencies."""
    return UserService(
        UserRepository(db),
        company_repository=CompanyRepository(db),
        address_repository=AddressRepository(db)
    )


def get_storage_service():
    """Get the storage service."""
    return StorageService()


def get_address_service(db=Depends(get_database)):
    """Get the address service."""
    return AddressService(AddressRepository(db))


def get_company_service(db=Depends(get_database)):
    """Get the company service."""
    company_repo = CompanyRepository(db)
    address_repo = AddressRepository(db)
    return CompanyService(company_repo, address_repo)


def get_location_service(db=Depends(get_database)):
    """Get the location service."""
    return LocationService(LocationRepository(db))


def get_attribute_service(db=Depends(get_database)):
    """Get the attribute service."""
    return AttributeService(AttributeRepository(db))


def get_token_service(db=Depends(get_database)):
    """Get the token service with appropriate repository (Redis or DB)."""
    redis_client = get_redis()
    if redis_client is not None:
        session_repository = RedisTokenRepository(
            redis_client,
            key_prefix=settings.REDIS_TOKEN_PREFIX,
        )
        return TokenService(session_repository)

    return TokenService(TokenRepository(db), db=db)


def get_email_service():
    """Get the email service based on configured provider."""
    from app.services.email_service import (
        MockEmailService, SMTPEmailService, 
        MailgunEmailService, BrevoEmailService
    )

    provider = (settings.EMAIL_PROVIDER or "mock").lower()
    
    if provider == "smtp" and settings.SMTP_HOST:
        return SMTPEmailService(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
    elif provider == "mailgun" and settings.MAILGUN_DOMAIN and settings.MAILGUN_API_KEY:
        return MailgunEmailService(
            domain=settings.MAILGUN_DOMAIN,
            api_key=settings.MAILGUN_API_KEY,
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
    elif provider == "brevo" and settings.BREVO_API_KEY:
        return BrevoEmailService(
            api_key=settings.BREVO_API_KEY,
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
    else:
        return MockEmailService(
            from_email=settings.EMAILS_FROM_EMAIL,
            from_name=settings.EMAILS_FROM_NAME
        )
