import logging
from typing import Any, Dict

from beanie import PydanticObjectId

from app.core.celery_app import celery_app
from app.core.database import init_database
from app.models.profile import Profile, ProfileStatus
from app.models.scraped_data import ScrapedData
from app.services.scraping_service import scrape_profile
from app.services.processing_service import process_profile
from app.services.ml_service import run_profile_analysis
from app.services.profile_store_service import persist_analysis_results

logger = logging.getLogger(__name__)


@celery_app.task(name="run_profile_pipeline")
def run_profile_pipeline(profile_id: str) -> Dict[str, Any]:
    """
    Celery task entrypoint for the profiling pipeline.

    Pipeline: SCRAPING → PROCESSING → ANALYZING → COMPLETED/FAILED.
    """
    import asyncio

    async def _run() -> Dict[str, Any]:
        # Initialize database connection for Beanie
        logger.info(f"Initializing database for profile {profile_id}")
        try:
            await init_database()
            logger.info(f"Database initialized successfully for profile {profile_id}")
        except Exception as db_init_error:
            logger.error(f"Database initialization failed: {db_init_error}", exc_info=True)
            return {"status": "error", "reason": f"database_init_failed: {str(db_init_error)}"}

        logger.info(f"Fetching profile {profile_id}")
        profile = await Profile.get(PydanticObjectId(profile_id))
        if not profile:
            logger.error("Profile not found in pipeline", extra={"profile_id": profile_id})
            return {"status": "error", "reason": "profile_not_found"}

        try:
            # SCRAPING
            await profile.mark_status(ProfileStatus.SCRAPING)
            scraped_items: list[ScrapedData] = await scrape_profile(profile)

            # PROCESSING
            await profile.mark_status(ProfileStatus.PROCESSING)
            features = await process_profile(scraped_items)

            # ANALYZING
            await profile.mark_status(ProfileStatus.ANALYZING)
            traits, summary, metadata = await run_profile_analysis(profile, features, scraped_items)

            # PERSIST RESULTS
            await persist_analysis_results(profile, traits, summary, metadata)

            logger.info("Profile pipeline completed", extra={"profile_id": profile_id})
            return {"status": "ok"}
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Profile pipeline failed", extra={"profile_id": profile_id})
            if profile:
                await profile.mark_status(ProfileStatus.FAILED, error_message=str(exc))
            return {"status": "error", "reason": str(exc)}

    # Fix: Handle event loop properly for Celery prefork workers
    # asyncio.run() closes the event loop which causes issues with Celery prefork
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_run())
