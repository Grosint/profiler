"""
Production entrypoint for Celery worker
Works on:
- Local
- Docker
- Railway
"""

import sys
import logging
import os
from pathlib import Path

# ------------------------------------------------------------------
# Ensure project root is on PYTHONPATH
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set PYTHONPATH environment variable for Celery subprocess
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("worker")

logger.info("Starting Celery worker service")
logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Python path: {sys.path[:3]}...")
logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}")

# ------------------------------------------------------------------
# Verify Celery app can be imported AFTER path setup
# ------------------------------------------------------------------
try:
    from app.core.celery_app import celery_app
    logger.info("✓ Successfully imported Celery app")
except Exception as e:
    logger.exception("Failed to import Celery app")
    raise e

# ------------------------------------------------------------------
# Start Celery worker
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Use celery's command-line interface but ensure path is correct
    import subprocess

    logger.info("Starting Celery worker...")
    # #region agent log
    import json
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-startup", "hypothesisId": "H", "location": "start_worker.py:__main__", "message": "Starting Celery worker process", "data": {"project_root": str(PROJECT_ROOT), "pythonpath": os.environ.get("PYTHONPATH", "not set")}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    # Run celery worker - it will use the imported celery_app
    # The -A flag tells celery where to find the app
    cmd = [
        sys.executable,
        "-m", "celery",
        "-A", "app.core.celery_app.celery_app",
        "worker",
        "--loglevel=info"
    ]

    logger.info(f"Command: {' '.join(cmd)}")
    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-startup", "hypothesisId": "H", "location": "start_worker.py:__main__", "message": "Executing Celery worker command", "data": {"command": " ".join(cmd)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    # Use execve to replace current process with celery worker
    # This ensures PYTHONPATH is preserved
    os.execve(
        sys.executable,
        cmd,
        os.environ  # Pass environment with PYTHONPATH set
    )
