from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "grosint_profiler",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Auto-discover tasks from the tasks module
celery_app.autodiscover_tasks(["app.tasks"])
