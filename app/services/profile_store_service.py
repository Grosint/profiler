"""
Profile Store Service - Persists intelligence analysis results

Handles storing the comprehensive summary, metadata, and analyst review flags.
"""

import logging
from typing import Any, Dict, List

from app.models.profile import Profile, ProfileStatus
from app.models.profile_trait import ProfileTrait

logger = logging.getLogger(__name__)


async def persist_analysis_results(
    profile: Profile, traits: List[ProfileTrait], summary: Dict[str, Any], metadata: Dict[str, Any] = None
) -> None:
    """
    Persist comprehensive intelligence analysis results on the Profile.

    This includes:
    - The structured summary with all 7 phases of analysis
    - Metadata with models used, timestamps, and confidence flags
    - Analyst review requirements
    """
    # Store summary
    profile.summary = summary

    # Store metadata (merge with existing if present)
    if metadata:
        if profile.metadata is None:
            profile.metadata = {}
        profile.metadata.update(metadata)

        # Check if analyst review is required
        analyst_review_required = metadata.get("analystReviewRequired", False)
        if analyst_review_required:
            if "flags" not in profile.metadata:
                profile.metadata["flags"] = {}
            profile.metadata["flags"]["analystReviewRequired"] = True
            logger.info(
                "Analyst review flagged",
                extra={"profile_id": str(profile.id), "reason": "low_confidence_or_insufficient_data"},
            )

    # Mark as completed
    await profile.mark_status(ProfileStatus.COMPLETED)

    logger.info(
        "Profile intelligence results persisted",
        extra={
            "profile_id": str(profile.id),
            "traits_count": len(traits),
            "models_used": len(metadata.get("modelsUsed", [])) if metadata else 0,
            "analyst_review_required": metadata.get("analystReviewRequired", False) if metadata else False,
        },
    )
