"""
Intelligence Model Pipeline Orchestrator

This module implements the comprehensive intelligence analysis pipeline
as specified in the system prompt. It coordinates multiple AI/ML models
to produce explainable, auditable intelligence profiles.
"""

import logging
from typing import Any, Dict, List, Tuple

from app.models.profile import Profile
from app.models.scraped_data import ScrapedData

from .phase1_identity import Phase1Identity
from .phase2_narrative import Phase2Narrative
from .phase3_behavioral import Phase3Behavioral
from .phase4_visual import Phase4Visual
from .phase5_network import Phase5Network
from .phase6_geospatial import Phase6Geospatial
from .phase7_risk import Phase7Risk
from .utils import MetadataBuilder, ModelLoader

logger = logging.getLogger(__name__)


class IntelligenceOrchestrator:
    """
    Orchestrates the execution of all intelligence models in the correct order,
    stores intermediate outputs, and aggregates results into a unified profile summary.
    """

    def __init__(self):
        self.model_loader = ModelLoader()
        self.metadata_builder = MetadataBuilder()
        self.phase1 = Phase1Identity()
        self.phase2 = Phase2Narrative(self.model_loader)
        self.phase3 = Phase3Behavioral()
        self.phase4 = Phase4Visual()
        self.phase5 = Phase5Network()
        self.phase6 = Phase6Geospatial()
        self.phase7 = Phase7Risk()

    async def run_full_pipeline(
        self, profile: Profile, scraped_items: List[ScrapedData], features: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute all 7 phases of the intelligence pipeline in order.

        Returns:
            Tuple of (summary, metadata) matching the specification structure.
        """
        logger.info(
            "Starting intelligence pipeline",
            extra={"profile_id": str(profile.id), "scraped_items_count": len(scraped_items)},
        )

        summary: Dict[str, Any] = {
            "overallRiskScore": {},
            "topTraits": [],
            "features": {
                "identity": {},
                "behavioral": {},
                "visual": {},
                "network": {},
                "geospatial": {},
            },
            "narratives": {},
            "toxicCommenters": [],
        }

        try:
            # PHASE 1: Identity & Consistency Checks
            logger.info("Phase 1: Identity & Consistency Checks")
            identity_results = await self.phase1.execute(profile, scraped_items, features)
            summary["features"]["identity"] = identity_results
            self.metadata_builder.record_model_use("Phase1", "StringSimilarity", "1.0")
            self.metadata_builder.record_model_use("Phase1", "Stylometry", "1.0")

            # PHASE 2: Textual & Narrative Intelligence
            logger.info("Phase 2: Textual & Narrative Intelligence")
            narrative_results = await self.phase2.execute(scraped_items, features)
            summary["narratives"] = narrative_results
            self.metadata_builder.record_model_use("Phase2", "TransformerEmbeddings", "BERT-based")
            self.metadata_builder.record_model_use("Phase2", "BERTopic", "1.0")
            self.metadata_builder.record_model_use("Phase2", "SentimentAnalysis", "1.0")
            self.metadata_builder.record_model_use("Phase2", "ToxicityClassifier", "1.0")

            # PHASE 3: Behavioral & Temporal Analysis
            logger.info("Phase 3: Behavioral & Temporal Analysis")
            behavioral_results = await self.phase3.execute(scraped_items, features)
            summary["features"]["behavioral"] = behavioral_results
            self.metadata_builder.record_model_use("Phase3", "TemporalAnalysis", "LSTM-based")
            self.metadata_builder.record_model_use("Phase3", "ChangePointDetection", "1.0")

            # PHASE 4: Image & Video Context (if available)
            logger.info("Phase 4: Image & Video Context")
            visual_results = await self.phase4.execute(scraped_items)
            summary["features"]["visual"] = visual_results
            if visual_results.get("hasVisualData"):
                self.metadata_builder.record_model_use("Phase4", "YOLO", "ObjectDetection")
                self.metadata_builder.record_model_use("Phase4", "CLIP", "ImageTextRelevance")
                self.metadata_builder.record_model_use("Phase4", "OCR", "TextExtraction")

            # PHASE 5: Network & Interaction Intelligence
            logger.info("Phase 5: Network & Interaction Intelligence")
            network_results = await self.phase5.execute(scraped_items, features)
            summary["features"]["network"] = network_results
            self.metadata_builder.record_model_use("Phase5", "GraphAnalysis", "NetworkX")
            self.metadata_builder.record_model_use("Phase5", "CommunityDetection", "1.0")

            # PHASE 6: Geo-Temporal Patterning (if available)
            logger.info("Phase 6: Geo-Temporal Patterning")
            geospatial_results = await self.phase6.execute(scraped_items)
            summary["features"]["geospatial"] = geospatial_results
            if geospatial_results.get("hasGeospatialData"):
                self.metadata_builder.record_model_use("Phase6", "DBSCAN", "Clustering")
                self.metadata_builder.record_model_use("Phase6", "IsolationForest", "AnomalyDetection")
                self.metadata_builder.record_model_use("Phase6", "HMM", "PatternOfLife")

            # PHASE 7: Risk & Threat Vector Calculation
            logger.info("Phase 7: Risk & Threat Vector Calculation")
            risk_results = await self.phase7.execute(
                identity_results, narrative_results, behavioral_results, network_results
            )
            summary["overallRiskScore"] = risk_results["riskScore"]
            summary["topTraits"] = risk_results["topTraits"]
            self.metadata_builder.record_model_use("Phase7", "EnsembleRisk", "BayesianWeighting")

            # Extract toxic commenters from features
            if "toxicity_analysis" in features:
                toxicity_data = features["toxicity_analysis"]
                summary["toxicCommenters"] = toxicity_data.get("toxic_commenters", [])
                summary["commentStatistics"] = toxicity_data.get("statistics", {})
                logger.info(
                    "Toxic commenters identified",
                    extra={
                        "toxic_commenters_count": len(summary["toxicCommenters"]),
                        "total_toxic_comments": toxicity_data.get("statistics", {}).get("total_toxic_comments", 0),
                    },
                )

            # Build metadata
            metadata = self.metadata_builder.build_metadata()

            logger.info("Intelligence pipeline completed successfully", extra={"profile_id": str(profile.id)})
            return summary, metadata

        except Exception as e:
            logger.exception("Intelligence pipeline failed", extra={"profile_id": str(profile.id)})
            raise
