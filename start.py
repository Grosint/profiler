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
# Verify file structure exists BEFORE any imports
# ------------------------------------------------------------------
import os
app_dir = PROJECT_ROOT / "app"
models_dir = app_dir / "models"
logger.info(f"Checking file structure:")
logger.info(f"  PROJECT_ROOT: {PROJECT_ROOT}")
logger.info(f"  PROJECT_ROOT exists: {PROJECT_ROOT.exists()}")
logger.info(f"  app/ exists: {app_dir.exists()}")
logger.info(f"  app/models/ exists: {models_dir.exists()}")
if models_dir.exists():
    contents = list(models_dir.iterdir())
    logger.info(f"  app/models/ contents ({len(contents)} items): {[str(c.name) for c in contents]}")
    init_file = models_dir / "__init__.py"
    logger.info(f"  app/models/__init__.py exists: {init_file.exists()}")
    if init_file.exists():
        logger.info(f"  app/models/__init__.py size: {init_file.stat().st_size} bytes")

# ------------------------------------------------------------------
# Test imports step by step with detailed error handling
# ------------------------------------------------------------------
try:
    logger.info("Step 1: Testing 'import app'")
    import app
    logger.info(f"✓ Imported app from {app.__file__}")
    logger.info(f"  app.__path__: {getattr(app, '__path__', 'N/A')}")

    logger.info("Step 2: Testing 'from app import models'")
    from app import models
    logger.info(f"✓ Imported app.models from {models.__file__}")
    logger.info(f"  models.__path__: {getattr(models, '__path__', 'N/A')}")

    logger.info("Step 3: Testing 'from app.models import profile'")
    from app.models import profile
    logger.info(f"✓ Imported app.models.profile from {profile.__file__}")

    logger.info("Step 4: Testing 'from app.core.database import init_database'")
    from app.core.database import init_database
    logger.info("✓ Imported app.core.database.init_database")

    logger.info("Step 5: Testing 'from app.main import app'")
    from app.main import app as fastapi_app
    logger.info("✓ Successfully imported FastAPI app")
except ImportError as e:
    logger.error(f"ImportError: {e}")
    logger.error(f"  Error name: {e.name}")
    logger.error(f"  Error path: {getattr(e, 'path', 'N/A')}")
    logger.error(f"  Current sys.path: {sys.path}")
    logger.error(f"  Current working directory: {os.getcwd()}")
    # Try to find where app package actually is
    import importlib.util
    try:
        spec = importlib.util.find_spec("app")
        if spec:
            logger.error(f"  app package location: {spec.origin}")
            logger.error(f"  app package submodule_search_locations: {spec.submodule_search_locations}")
        else:
            logger.error("  app package spec not found!")
    except Exception as spec_e:
        logger.error(f"  Could not get app spec: {spec_e}")
    raise
except Exception as e:
    logger.exception("Failed during import test")
    raise e

# ------------------------------------------------------------------
# Uvicorn boot
# ------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8000"))

    # CRITICAL: Pass the app object directly, not a string
    # This ensures uvicorn uses the already-imported app with correct sys.path
    # If we pass a string, uvicorn does its own import which may fail
    logger.info(f"Starting uvicorn on port {port}...")
    uvicorn.run(
        fastapi_app,  # Pass the object, not "app.main:app"
        host="0.0.0.0",
        port=port,
        log_level="info",
        workers=1,        # Railway handles scaling
        access_log=True,
    )
