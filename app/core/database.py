import logging
from beanie import init_beanie
from beanie.exceptions import CollectionWasNotInitialized
from motor.motor_asyncio import AsyncIOMotorClient

from .config import get_settings
from app.models.profile import Profile
from app.models.scraped_data import ScrapedData
from app.models.profile_trait import ProfileTrait

logger = logging.getLogger(__name__)

# Store client per process (works with Celery prefork)
_client: AsyncIOMotorClient | None = None
_initialized: bool = False


async def init_database() -> None:
    """Initialize Beanie database connection. Idempotent - safe to call multiple times."""
    global _client, _initialized

    # Check if already initialized in this process
    if _initialized:
        try:
            # Verify it's still working
            Profile.get_settings()
            return
        except CollectionWasNotInitialized:
            # Was initialized but lost connection, reinitialize
            _initialized = False
            logger.warning("Beanie connection lost, reinitializing...")

    settings = get_settings()
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        logger.info("Created new MongoDB client")

    db = _client[settings.MONGODB_DB_NAME]
    await init_beanie(
        database=db,
        document_models=[Profile, ScrapedData, ProfileTrait],
    )
    _initialized = True
    logger.info("Beanie database initialized successfully")
