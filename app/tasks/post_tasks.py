"""
Celery tasks for post analysis pipeline.
"""

import asyncio
import logging
from typing import Any, Dict

from app.core.celery_app import celery_app
from app.core.database import init_database
from app.models.post import Post, PostStatus
from app.services.post_analysis_service import analyze_post

logger = logging.getLogger(__name__)


@celery_app.task(name="run_post_analysis_pipeline")
def run_post_analysis_pipeline(post_id: str) -> Dict[str, Any]:
    """
    Celery task entrypoint for the post analysis pipeline.

    Pipeline: SCRAPING → PROCESSING → ANALYZING → COMPLETED/FAILED.
    """
    logger.info(f"Celery task run_post_analysis_pipeline called for post_id: {post_id}")

    async def _run() -> Dict[str, Any]:
        # Initialize database connection for Beanie
        logger.info(f"Initializing database for post {post_id}")
        try:
            await init_database()
            logger.info(f"Database initialized successfully for post {post_id}")
        except Exception as db_init_error:
            logger.error(f"Database initialization failed: {db_init_error}", exc_info=True)
            return {"status": "error", "reason": f"database_init_failed: {str(db_init_error)}"}

        logger.info(f"Starting post analysis pipeline for post {post_id}")
        try:
            from beanie import PydanticObjectId
            post = await Post.get(PydanticObjectId(post_id))
            if not post:
                logger.error(f"Post {post_id} not found in database")
                return {"status": "error", "reason": "post_not_found"}

            logger.info(f"Found post {post_id}, current status: {post.status}")
            await analyze_post(post_id)
            logger.info(f"Post analysis pipeline completed for post {post_id}")
            return {"status": "ok"}
        except Exception as exc:
            logger.exception(f"Post analysis pipeline failed for post {post_id}: {exc}", exc_info=True)
            try:
                from beanie import PydanticObjectId
                post = await Post.get(PydanticObjectId(post_id))
                if post:
                    await post.mark_status(PostStatus.FAILED, error_message=str(exc))
                    logger.info(f"Updated post {post_id} status to FAILED")
            except Exception as status_error:
                logger.error(f"Failed to update post status after error: {status_error}")
            return {"status": "error", "reason": str(exc)}

    # Handle event loop properly for Celery prefork workers
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_run())
