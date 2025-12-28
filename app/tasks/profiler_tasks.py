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
    # #region agent log
    import json
    import os
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "B", "location": "profiler_tasks.py:run_profile_pipeline", "message": "Celery task started", "data": {"profile_id": profile_id}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion

    async def _run() -> Dict[str, Any]:
        # Initialize database connection for Beanie
        logger.info(f"Initializing database for profile {profile_id}")
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "C", "location": "profiler_tasks.py:_run", "message": "Initializing database", "data": {"profile_id": profile_id}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        try:
            await init_database()
            logger.info(f"Database initialized successfully for profile {profile_id}")
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "C", "location": "profiler_tasks.py:_run", "message": "Database initialized successfully", "data": {"profile_id": profile_id}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion
        except Exception as db_init_error:
            logger.error(f"Database initialization failed: {db_init_error}", exc_info=True)
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "C", "location": "profiler_tasks.py:_run", "message": "Database initialization failed", "data": {"profile_id": profile_id, "error": str(db_init_error)}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion
            return {"status": "error", "reason": f"database_init_failed: {str(db_init_error)}"}

        logger.info(f"Fetching profile {profile_id}")
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "D", "location": "profiler_tasks.py:_run", "message": "Fetching profile from database", "data": {"profile_id": profile_id}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        profile = await Profile.get(PydanticObjectId(profile_id))
        if not profile:
            logger.error("Profile not found in pipeline", extra={"profile_id": profile_id})
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "D", "location": "profiler_tasks.py:_run", "message": "Profile not found", "data": {"profile_id": profile_id}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion
            return {"status": "error", "reason": "profile_not_found"}

        try:
            # SCRAPING
            await profile.mark_status(ProfileStatus.SCRAPING)
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "E", "location": "profiler_tasks.py:_run", "message": "Starting scraping phase", "data": {"profile_id": profile_id, "urls": {"instagram": bool(profile.urls.instagramUrl), "facebook": bool(profile.urls.facebookUrl), "twitter": bool(profile.urls.twitterUrl), "linkedin": bool(profile.urls.linkedinUrl), "reddit": bool(profile.urls.redditUrl), "blogs": len(profile.urls.blogUrls or [])}}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion
            scraped_items: list[ScrapedData] = await scrape_profile(profile)
            # #region agent log
            try:
                with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                    f.write(json.dumps({"sessionId": "debug-session", "runId": "worker-task", "hypothesisId": "E", "location": "profiler_tasks.py:_run", "message": "Scraping phase completed", "data": {"profile_id": profile_id, "scraped_count": len(scraped_items), "scraped_ids": [str(item.id) for item in scraped_items]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
            except:
                pass
            # #endregion

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
