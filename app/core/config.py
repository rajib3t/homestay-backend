from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI OOP App"
    MONGO_URI: str
    REDIS_URL: Optional[str] = None
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_TOKEN_PREFIX: str = "refresh_token"
    IDEMPOTENCY_PREFIX: str = "idempotency"
    IDEMPOTENCY_TTL_SECONDS: int = 86400
    IDEMPOTENCY_HEADER_NAME: str = "Idempotency-Key"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ADMIN_USER_USERNAME: Optional[str] = None
    ADMIN_USER_EMAIL: Optional[str] = None
    ADMIN_USER_PASSWORD: Optional[str] = None
    ADMIN_USER_FIRST_NAME: str = "Admin"
    ADMIN_USER_LAST_NAME: str = "User"
    ADMIN_USER_MOBILE: Optional[str] = None

    # Environment
    ENV: str = "development"  # production | staging | development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECURE_COOKIES: bool = False

    # Email Settings (Multiple Providers Supported)
    EMAIL_PROVIDER: str = "mock" # options: "mock", "smtp", "mailgun", "brevo"
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Mailgun
    MAILGUN_DOMAIN: Optional[str] = None
    MAILGUN_API_KEY: Optional[str] = None
    
    # Brevo
    BREVO_API_KEY: Optional[str] = None

    # S3 / MinIO settings
    S3_PROVIDER: Optional[str] = None  # 'aws' or 'minio' (optional)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_USE_SSL: bool = True




    # Default File Upload Settings
    MAX_FILE_SIZE_MB: int = 5  # Maximum file size in MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
    CORS_ALLOWED_ORIGINS: Optional[str] = None

    @property
    def cors_allowed_origins(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:3000", "http://localhost:5173"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
