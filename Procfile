web: PYTHONPATH=/app:$PYTHONPATH python start.py
worker: PYTHONPATH=/app:$PYTHONPATH celery -A app.core.celery_app.celery_app worker --loglevel=info
