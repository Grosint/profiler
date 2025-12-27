"""
Production entrypoint for FastAPI API service
Works on:
- Local
- Docker
- Railway
"""

import sys
import logging
from pathlib import Path

# ------------------------------------------------------------------
# Ensure project root is on PYTHONPATH
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ------------------------------------------------------------------
# Logging config (early, before app import)
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("startup")

logger.info("Starting API service")
logger.info(f"Project root: {PROJECT_ROOT}")
logger.info(f"Python path: {sys.path}")

# ------------------------------------------------------------------
# Import FastAPI app AFTER path setup
# ------------------------------------------------------------------
try:
    from app.main import app
except Exception as e:
    logger.exception("Failed to import FastAPI app")
    raise e

# ------------------------------------------------------------------
# Uvicorn boot
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1,        # Railway handles scaling
        access_log=True,
    )
