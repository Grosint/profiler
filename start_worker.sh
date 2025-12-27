#!/bin/bash
set -e

# Start celery worker
exec celery -A app.core.celery_app.celery_app worker --loglevel=info
