"""
Production entrypoint for background worker
"""

import sys
import logging
import time
from pathlib import Path

# ------------------------------------------------------------------
# Ensure project root is on PYTHONPATH
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("worker")

logger.info("Starting Worker service")
logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Python path: {sys.path}")

# ------------------------------------------------------------------
# Import worker tasks AFTER path setup
# ------------------------------------------------------------------
try:
    from app.tasks.profiler_tasks import run_profiler
    from app.tasks.post_tasks import run_post_tasks
except Exception as e:
    logger.exception("Failed to import worker tasks")
    raise e

# ------------------------------------------------------------------
# Worker loop
# ------------------------------------------------------------------
def main():
    logger.info("Worker initialized successfully")

    while True:
        try:
            logger.info("Running profiler tasks")
            run_profiler()

            logger.info("Running post tasks")
            run_post_tasks()

        except Exception:
            logger.exception("Worker cycle failed")

        # Prevent CPU burn
        time.sleep(5)


if __name__ == "__main__":
    main()
