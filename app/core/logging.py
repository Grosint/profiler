import logging
import logging.config
import os
from typing import Any, Dict

from pythonjsonlogger import jsonlogger

from .config import get_settings


def _ensure_log_dir(path: str) -> None:
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def get_logging_config() -> Dict[str, Any]:
    settings = get_settings()
    _ensure_log_dir(settings.LOG_FILE_PATH)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
            "json": {
                "()": jsonlogger.JsonFormatter,
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(profile_id)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings.LOG_JSON else "standard",
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.LOG_FILE_PATH,
                "maxBytes": settings.LOG_FILE_MAX_BYTES,
                "backupCount": settings.LOG_FILE_BACKUP_COUNT,
                "formatter": "json" if settings.LOG_JSON else "standard",
                "level": settings.LOG_LEVEL,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": settings.LOG_LEVEL,
        },
        "loggers": {
            "uvicorn": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
            "celery": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
        },
    }


def setup_logging() -> None:
    config = get_logging_config()
    logging.config.dictConfig(config)
