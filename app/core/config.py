from functools import lru_cache
from typing import Optional, Union

from pydantic import Field, field_validator
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
    CORS_ALLOW_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list]) -> list[str]:
        """
        Parse CORS_ALLOW_ORIGINS from comma-separated string or list.
        Environment variables are strings, so we need to split them.
        """
        # #region agent log
        import json
        import os
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-parse", "hypothesisId": "A", "location": "config.py:parse_cors_origins", "message": "Parsing CORS_ALLOW_ORIGINS", "data": {"input_type": type(v).__name__, "input_value": str(v)[:100] if isinstance(v, str) else v, "env_value": os.getenv("CORS_ALLOW_ORIGINS", "NOT_SET")[:100]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion

        # If already a list, return as-is
        if isinstance(v, list):
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-parse", "hypothesisId": "A", "location": "config.py:parse_cors_origins", "message": "CORS_ALLOW_ORIGINS already a list", "data": {"result": v}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion
            return v

        # If string, split by comma and strip whitespace
        if isinstance(v, str):
            # Handle "*" special case
            if v.strip() == "*":
                result = ["*"]
            else:
                result = [origin.strip() for origin in v.split(",") if origin.strip()]

            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "cors-parse", "hypothesisId": "A", "location": "config.py:parse_cors_origins", "message": "Parsed CORS_ALLOW_ORIGINS from string", "data": {"input": v[:100], "result": result}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion

            return result

        # Fallback: return as-is (shouldn't happen)
        return v

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    LOG_FILE_PATH: str = "logs/grosint_profiler.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
