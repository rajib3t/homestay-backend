from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI OOP App"
    MONGO_URI: str
    REDIS_URL: Optional[str] = None
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_TOKEN_PREFIX: str = "refresh_token"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Environment
    ENV: str = "development"  # production | staging | development
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECURE_COOKIES: bool = False
    # S3 / MinIO settings
    S3_PROVIDER: Optional[str] = None  # 'aws' or 'minio' (optional)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_USE_SSL: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()