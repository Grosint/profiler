from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="",
                                      env_file=".env",
                                      env_file_encoding="utf-8",
                                      extra="ignore")

    # App
    APP_NAME: str = "GROSINT AI Profiler"
    APP_ENV: str = "local"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Security
    API_KEY: str = Field(..., description="Primary API key for external callers")
    INTERNAL_SERVICE_TOKEN: Optional[str] = Field(
        default=None, description="Token used for internal service-to-service calls"
    )

    # Database
    MONGODB_URI: str = Field(..., description="MongoDB connection URI")
    MONGODB_DB_NAME: str = "grosint_profiler"

    # Celery / Queue
    CELERY_BROKER_URL: str = Field(..., description="Celery broker URL, e.g. redis://")
    CELERY_RESULT_BACKEND: str = Field(..., description="Celery result backend URL")

    # HTTP client defaults
    HTTP_CLIENT_TIMEOUT_SECONDS: float = 20.0
    HTTP_CLIENT_MAX_RETRIES: int = 3
    HTTP_CLIENT_CIRCUIT_BREAKER_THRESHOLD: int = 5
    HTTP_CLIENT_CIRCUIT_BREAKER_RESET_SECONDS: int = 60

    # CORS
    CORS_ALLOW_ORIGINS: list[AnyHttpUrl] | list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    LOG_FILE_PATH: str = "logs/grosint_profiler.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
