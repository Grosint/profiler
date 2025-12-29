from functools import lru_cache
from typing import Optional

from pydantic import Field, computed_field
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
    API_KEY: Optional[str] = Field(
        default=None, description="Primary API key for external callers (deprecated - no longer required)"
    )
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

    # CORS - Store as string to avoid JSON parsing issues
    CORS_ALLOW_ORIGINS_STR: str = Field(default="*", alias="CORS_ALLOW_ORIGINS", exclude=True)
    CORS_ALLOW_CREDENTIALS: bool = Field(default=False, description="CORS allow credentials - must be False when using '*' origins")
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    @computed_field
    @property
    def CORS_ALLOW_ORIGINS(self) -> list[str]:
        """
        Parse CORS_ALLOW_ORIGINS from environment variable.
        Supports "*" for all origins or comma-separated list of specific origins.
        """
        if not self.CORS_ALLOW_ORIGINS_STR or self.CORS_ALLOW_ORIGINS_STR.strip() == "":
            return ["*"]

        origins_str = self.CORS_ALLOW_ORIGINS_STR.strip()
        if origins_str == "*":
            return ["*"]

        # Parse comma-separated origins
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        return origins if origins else ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    LOG_FILE_PATH: str = "logs/grosint_profiler.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
