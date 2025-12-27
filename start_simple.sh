#!/bin/bash
set -e

# Set PYTHONPATH to include the current directory
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$(pwd)"

# Get PORT from environment or default to 8000
PORT=${PORT:-8000}

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
