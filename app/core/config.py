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
    CORS_ALLOW_CREDENTIALS: bool = False  # Must be False when using "*" origins
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    @computed_field
    @property
    def CORS_ALLOW_ORIGINS(self) -> list[str]:
        """
        Parse CORS_ALLOW_ORIGINS from comma-separated string.
        Supports "*" for all origins or specific origins separated by commas.
        """
        # #region agent log
        import json
        import os
        env_value = os.getenv("CORS_ALLOW_ORIGINS", "NOT_SET")
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "config-cors", "hypothesisId": "G", "location": "config.py:CORS_ALLOW_ORIGINS", "message": "CORS_ALLOW_ORIGINS property accessed", "data": {"cors_allow_origins_str": self.CORS_ALLOW_ORIGINS_STR, "env_cors_allow_origins": env_value}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        # Parse comma-separated origins from environment variable
        if not self.CORS_ALLOW_ORIGINS_STR or self.CORS_ALLOW_ORIGINS_STR.strip() == "":
            # Default to "*" if not set
            parsed_origins = ["*"]
        elif self.CORS_ALLOW_ORIGINS_STR.strip() == "*":
            parsed_origins = ["*"]
        else:
            # Split by comma and strip whitespace
            parsed_origins = [origin.strip() for origin in self.CORS_ALLOW_ORIGINS_STR.split(",") if origin.strip()]
            if not parsed_origins:
                parsed_origins = ["*"]  # Fallback to "*" if parsing fails
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "config-cors", "hypothesisId": "G", "location": "config.py:CORS_ALLOW_ORIGINS", "message": "CORS_ALLOW_ORIGINS parsed", "data": {"parsed_origins": parsed_origins}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        return parsed_origins

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    LOG_FILE_PATH: str = "logs/grosint_profiler.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
