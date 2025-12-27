"""
Utility functions and model loaders for the intelligence orchestrator.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ModelLoader:
    """Lazy loading of ML models used across phases."""

    def __init__(self):
        self._sentence_model = None
        self._bertopic_model = None
        self._sentiment_model = None
        self._toxicity_model = None

    def get_sentence_transformer(self):
        """Lazy load sentence transformer model."""
        if self._sentence_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading sentence transformer model...")
                self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Sentence transformer model loaded")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}. Using fallback.")
                self._sentence_model = False  # Mark as failed
        return self._sentence_model if self._sentence_model is not False else None

    def get_bertopic_model(self):
        """Lazy load BERTopic model."""
        if self._bertopic_model is None:
            try:
                from bertopic import BERTopic
                from umap import UMAP
                from hdbscan import HDBSCAN

                logger.info("Initializing BERTopic model...")
                # Use HDBSCAN for better clustering
                umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)
                hdbscan_model = HDBSCAN(min_cluster_size=2, metric="euclidean", cluster_selection_method="eom")
                self._bertopic_model = BERTopic(
                    umap_model=umap_model,
                    hdbscan_model=hdbscan_model,
                    verbose=False,
                )
                logger.info("BERTopic model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize BERTopic: {e}. Using fallback.")
                self._bertopic_model = False
        return self._bertopic_model if self._bertopic_model is not False else None

    def get_sentiment_model(self):
        """Lazy load sentiment analysis model."""
        if self._sentiment_model is None:
            try:
                from transformers import pipeline

                logger.info("Loading sentiment analysis model...")
                self._sentiment_model = pipeline(
                    "sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                logger.info("Sentiment analysis model loaded")
            except Exception as e:
                logger.warning(f"Failed to load sentiment model: {e}. Using fallback.")
                self._sentiment_model = False
        return self._sentiment_model if self._sentiment_model is not False else None

    def get_toxicity_model(self):
        """Lazy load toxicity classifier."""
        if self._toxicity_model is None:
            try:
                from transformers import pipeline

                logger.info("Loading toxicity classifier...")
                self._toxicity_model = pipeline("text-classification", model="unitary/toxic-bert")
                logger.info("Toxicity classifier loaded")
            except Exception as e:
                logger.warning(f"Failed to load toxicity model: {e}. Using fallback.")
                self._toxicity_model = False
        return self._toxicity_model if self._toxicity_model is not False else None


class MetadataBuilder:
    """Builds metadata for pipeline execution."""

    def __init__(self):
        self.models_used: List[Dict[str, str]] = []
        self.execution_timestamps: Dict[str, datetime] = {}

    def record_model_use(self, phase: str, model_name: str, version: str) -> None:
        """Record which models were used in the pipeline."""
        self.models_used.append({"phase": phase, "model": model_name, "version": version})

    def build_metadata(self) -> Dict[str, Any]:
        """Build metadata dictionary with models, timestamps, and flags."""
        # Determine if analyst review is required
        analyst_review_required = False
        # In production, check confidence thresholds
        # For now, set based on model count (more models = higher confidence)
        if len(self.models_used) < 5:
            analyst_review_required = True

        metadata = {
            "modelsUsed": self.models_used,
            "executionTimestamps": {
                phase: str(ts) for phase, ts in self.execution_timestamps.items()
            },
            "confidenceFlags": {},  # Can be populated by phases if needed
            "analystReviewRequired": analyst_review_required,
            "pipelineVersion": "1.0",
            "completedAt": datetime.utcnow().isoformat(),
        }

        return metadata
