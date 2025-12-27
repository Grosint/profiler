"""
ML Service - Intelligence Analysis Orchestration

This service coordinates the intelligence pipeline orchestrator to produce
comprehensive, explainable intelligence profiles.
"""

import logging
from typing import Any, Dict, List, Tuple

from app.models.profile import Profile
from app.models.profile_trait import ProfileTrait, TraitType
from app.models.scraped_data import ScrapedData
from app.services.orchestrator import IntelligenceOrchestrator

logger = logging.getLogger(__name__)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


async def run_profile_analysis(
    profile: Profile, features: Dict[str, Any], scraped_items: List[ScrapedData]
) -> Tuple[List[ProfileTrait], Dict[str, Any], Dict[str, Any]]:
    """
    Run comprehensive intelligence analysis using the orchestrator pipeline.

    This executes all 7 phases of the intelligence model pipeline:
    1. Identity & Consistency Checks
    2. Textual & Narrative Intelligence
    3. Behavioral & Temporal Analysis
    4. Image & Video Context
    5. Network & Interaction Intelligence
    6. Geo-Temporal Patterning
    7. Risk & Threat Vector Calculation

    Returns:
        Tuple of (traits, summary, metadata)
    """
    logger.info(
        "Starting comprehensive intelligence analysis",
        extra={"profile_id": str(profile.id), "scraped_items_count": len(scraped_items)},
    )

    # Initialize orchestrator
    orchestrator = IntelligenceOrchestrator()

    # Run full pipeline
    summary, metadata = await orchestrator.run_full_pipeline(profile, scraped_items, features)

    # Generate ProfileTrait objects from summary for backward compatibility
    traits: List[ProfileTrait] = []

    # Extract traits from risk scores
    risk_score = summary.get("overallRiskScore", {})
    if isinstance(risk_score, dict):
        # Ideological risk trait
        ideological = risk_score.get("ideological", 0.0)
        if ideological > 0.3:
            traits.append(
                ProfileTrait(
                    profile=profile,
                    traitType=TraitType.RISK,
                    traitName="Ideological Risk",
                    score=ideological,
                    confidence=risk_score.get("confidence", "medium") == "high" and 0.8 or 0.6,
                    evidenceSnippets=summary.get("narratives", {}).get("dominantThemes", [])[:3],
                    extra={"dimension": "ideological", "source": "Phase7"},
                )
            )

        # Mobilization risk trait
        mobilization = risk_score.get("mobilization", 0.0)
        if mobilization > 0.3:
            traits.append(
                ProfileTrait(
                    profile=profile,
                    traitType=TraitType.RISK,
                    traitName="Mobilization Risk",
                    score=mobilization,
                    confidence=risk_score.get("confidence", "medium") == "high" and 0.8 or 0.6,
                    evidenceSnippets=[],
                    extra={"dimension": "mobilization", "source": "Phase7"},
                )
            )

        # Network risk trait
        network_risk = risk_score.get("network", 0.0)
        if network_risk > 0.3:
            traits.append(
                ProfileTrait(
                    profile=profile,
                    traitType=TraitType.COMMUNICATION,
                    traitName="Network Influence",
                    score=network_risk,
                    confidence=risk_score.get("confidence", "medium") == "high" and 0.8 or 0.6,
                    evidenceSnippets=[],
                    extra={"dimension": "network", "source": "Phase5"},
                )
            )

        # Volatility risk trait
        volatility = risk_score.get("volatility", 0.0)
        if volatility > 0.3:
            traits.append(
                ProfileTrait(
                    profile=profile,
                    traitType=TraitType.PERSONALITY,
                    traitName="Behavioral Volatility",
                    score=volatility,
                    confidence=risk_score.get("confidence", "medium") == "high" and 0.8 or 0.6,
                    evidenceSnippets=[],
                    extra={"dimension": "volatility", "source": "Phase3"},
                )
            )

    # Identity confidence trait
    identity_features = summary.get("features", {}).get("identity", {})
    identity_conf = identity_features.get("identityConfidence", 0.5)
    if identity_conf > 0.0:
        traits.append(
            ProfileTrait(
                profile=profile,
                traitType=TraitType.PERSONALITY,
                traitName="Identity Consistency",
                score=identity_conf,
                confidence=0.7,
                evidenceSnippets=[],
                extra={"dimension": "identity", "source": "Phase1"},
            )
        )

    # Persist traits
    for t in traits:
        await t.insert()

    logger.info(
        "Intelligence analysis completed",
        extra={
            "profile_id": str(profile.id),
            "traits_count": len(traits),
            "risk_confidence": risk_score.get("confidence", "unknown") if isinstance(risk_score, dict) else "unknown",
        },
    )

    return traits, summary, metadata
