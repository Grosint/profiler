"""
Phase 1: Identity & Consistency Checks

Enhanced string similarity and stylometry analysis for identity confidence.
"""

import logging
import re
import statistics
from difflib import SequenceMatcher
from typing import Any, Dict, List

from app.models.profile import Profile
from app.models.scraped_data import ScrapedData

logger = logging.getLogger(__name__)


class Phase1Identity:
    """Handles identity and consistency checks."""

    async def execute(
        self, profile: Profile, scraped_items: List[ScrapedData], features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced string similarity and stylometry analysis for identity confidence."""
        # Extract usernames/aliases from scraped data
        usernames: List[str] = []
        texts: List[str] = []

        for item in scraped_items:
            if item.metadata:
                # Extract potential usernames from metadata
                if "username" in item.metadata:
                    usernames.append(str(item.metadata["username"]).lower())
                if "author" in item.metadata:
                    usernames.append(str(item.metadata["author"]).lower())
            if item.rawContent:
                texts.append(item.rawContent)

        # Enhanced String Similarity Analysis
        identity_confidence = 0.5  # Default moderate confidence
        if usernames:
            unique_usernames = list(set(usernames))
            if len(unique_usernames) == 1:
                identity_confidence = 0.9  # High consistency
            elif len(unique_usernames) <= 3:
                # Use SequenceMatcher for pairwise similarity
                similarities = []
                for i, u1 in enumerate(unique_usernames):
                    for u2 in unique_usernames[i + 1 :]:
                        # Calculate multiple similarity metrics
                        ratio_sim = SequenceMatcher(None, u1, u2).ratio()
                        # Jaccard similarity on character n-grams
                        n = 2
                        set1 = set(u1[i : i + n] for i in range(len(u1) - n + 1))
                        set2 = set(u2[i : i + n] for i in range(len(u2) - n + 1))
                        jaccard = len(set1 & set2) / len(set1 | set2) if (set1 | set2) else 0
                        # Combined similarity
                        combined_sim = (ratio_sim * 0.7) + (jaccard * 0.3)
                        similarities.append(combined_sim)
                if similarities:
                    avg_sim = sum(similarities) / len(similarities)
                    identity_confidence = 0.5 + (avg_sim * 0.4)  # Scale to 0.5-0.9
            else:
                identity_confidence = 0.3  # Low consistency

        # Enhanced Stylometry Analysis
        persona_consistency = 0.6  # Default moderate
        if len(texts) >= 2:
            # Multiple stylometric features
            sentence_lengths = []
            word_lengths = []
            punctuation_ratios = []
            capitalization_ratios = []

            for text in texts:
                # Sentence length analysis
                sentences = re.split(r"[.!?]+", text)
                lengths = [len(s.split()) for s in sentences if s.strip()]
                if lengths:
                    sentence_lengths.append(sum(lengths) / len(lengths))

                # Average word length
                words = re.findall(r"\b\w+\b", text)
                if words:
                    avg_word_len = sum(len(w) for w in words) / len(words)
                    word_lengths.append(avg_word_len)

                # Punctuation ratio
                punct_count = len(re.findall(r"[.!?,;:—]", text))
                punct_ratio = punct_count / max(len(text), 1)
                punctuation_ratios.append(punct_ratio)

                # Capitalization ratio
                caps_count = len(re.findall(r"[A-Z]", text))
                caps_ratio = caps_count / max(len(text), 1)
                capitalization_ratios.append(caps_ratio)

            # Calculate consistency scores for each feature
            consistency_scores = []
            for feature_list in [sentence_lengths, word_lengths, punctuation_ratios, capitalization_ratios]:
                if len(feature_list) > 1:
                    std_dev = statistics.stdev(feature_list)
                    mean_val = statistics.mean(feature_list)
                    if mean_val > 0:
                        cv = std_dev / mean_val  # Coefficient of variation
                        consistency = max(0.0, min(1.0, 1.0 - cv))
                        consistency_scores.append(consistency)

            if consistency_scores:
                persona_consistency = sum(consistency_scores) / len(consistency_scores)

        return {
            "identityConfidence": round(identity_confidence, 3),
            "personaConsistencyScore": round(persona_consistency, 3),
        }
