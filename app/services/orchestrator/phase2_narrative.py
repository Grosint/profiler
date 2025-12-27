"""
Phase 2: Textual & Narrative Intelligence

Transformer embeddings, topic modeling, sentiment, and toxicity analysis.
"""

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from app.models.scraped_data import ScrapedData

from .utils import ModelLoader

logger = logging.getLogger(__name__)


class Phase2Narrative:
    """Handles textual and narrative intelligence analysis."""

    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader

    def _calculate_sentiment(self, text: str) -> float:
        """Fallback sentiment calculation using lexicon."""
        positive_words = {
            "good", "great", "excellent", "happy", "love", "like", "amazing",
            "wonderful", "fantastic", "best", "awesome", "brilliant", "positive",
            "success", "win", "joy", "pleased", "delighted", "satisfied",
        }
        negative_words = {
            "bad", "terrible", "awful", "hate", "angry", "sad", "horrible",
            "worst", "fail", "failure", "disappointed", "frustrated", "negative",
            "problem", "issue", "upset", "annoyed", "disgusted", "furious",
        }

        words = re.findall(r"\b\w+\b", text.lower())
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        total = len(words) or 1

        return (pos_count - neg_count) / max(total, 1)

    async def execute(
        self, scraped_items: List[ScrapedData], features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transformer embeddings, topic modeling, sentiment, and toxicity analysis."""
        # Aggregate all text content
        all_texts: List[str] = []
        timestamps: List[datetime] = []

        for item in scraped_items:
            if item.rawContent:
                all_texts.append(item.rawContent)
                timestamps.append(item.scrapedAt)

        if not all_texts:
            return {
                "dominantThemes": [],
                "themeEvolution": [],
                "sentimentTrend": "neutral",
                "toxicityScore": 0.0,
            }

        # Try to use BERTopic for topic modeling
        dominant_themes = []
        theme_evolution = []
        bertopic_model = self.model_loader.get_bertopic_model()

        if bertopic_model and len(all_texts) >= 3:
            try:
                # Fit BERTopic model
                topics, probs = bertopic_model.fit_transform(all_texts)
                # Get top topics
                topic_info = bertopic_model.get_topic_info()
                if len(topic_info) > 0:
                    # Get top 5 topics (excluding outlier topic -1)
                    top_topics = topic_info[topic_info["Topic"] != -1].head(5)
                    for _, row in top_topics.iterrows():
                        # Get top words for this topic
                        topic_words = bertopic_model.get_topic(row["Topic"])
                        if topic_words:
                            # Get top 3 words and join them as a theme
                            theme_words = [word for word, _ in topic_words[:3]]
                            dominant_themes.append(" ".join(theme_words))

                # Theme evolution: split into early and recent periods
                if len(all_texts) >= 4 and timestamps:
                    sorted_items = sorted(zip(timestamps, all_texts), key=lambda x: x[0])
                    mid = len(sorted_items) // 2
                    early_texts = [t for _, t in sorted_items[:mid]]
                    late_texts = [t for _, t in sorted_items[mid:]]

                    if len(early_texts) >= 2:
                        early_topics, _ = bertopic_model.transform(early_texts)
                        early_topic_info = bertopic_model.get_topic_info()
                        early_theme_words = []
                        if len(early_topic_info) > 0:
                            top_early = early_topic_info[early_topic_info["Topic"] != -1].head(1)
                            if len(top_early) > 0:
                                topic_words = bertopic_model.get_topic(int(top_early.iloc[0]["Topic"]))
                                early_theme_words = [word for word, _ in topic_words[:3]] if topic_words else []

                    if len(late_texts) >= 2:
                        late_topics, _ = bertopic_model.transform(late_texts)
                        late_topic_info = bertopic_model.get_topic_info()
                        late_theme_words = []
                        if len(late_topic_info) > 0:
                            top_late = late_topic_info[late_topic_info["Topic"] != -1].head(1)
                            if len(top_late) > 0:
                                topic_words = bertopic_model.get_topic(int(top_late.iloc[0]["Topic"]))
                                late_theme_words = [word for word, _ in topic_words[:3]] if topic_words else []

                    if early_theme_words or late_theme_words:
                        theme_evolution = [
                            {"period": "early", "themes": early_theme_words[:3]},
                            {"period": "recent", "themes": late_theme_words[:3]},
                        ]
            except Exception as e:
                logger.warning(f"BERTopic analysis failed: {e}. Using fallback.")
                bertopic_model = None

        # Fallback to basic word frequency if BERTopic failed
        if not dominant_themes:
            full_text = " ".join(all_texts)
            words = re.findall(r"\b[a-z]{4,}\b", full_text.lower())
            word_freq = Counter(words)
            stop_words = {
                "that", "this", "with", "from", "have", "been", "will", "would",
                "could", "should", "their", "there", "these", "those", "about",
                "which", "other", "more", "very", "what", "when", "where", "your",
            }
            filtered_words = {w: c for w, c in word_freq.items() if w not in stop_words}
            top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:5]
            dominant_themes = [word for word, _ in top_words]

        # Sentiment Analysis using transformer model
        sentiment_scores = []
        sentiment_model = self.model_loader.get_sentiment_model()

        for text in all_texts:
            if sentiment_model:
                try:
                    result = sentiment_model(text[:512])  # Limit length
                    # Map labels to scores: POSITIVE -> 1, NEGATIVE -> -1, NEUTRAL -> 0
                    label = result[0]["label"].upper()
                    score = result[0]["score"]
                    if "POSITIVE" in label or "POS" in label:
                        sentiment_scores.append(score)
                    elif "NEGATIVE" in label or "NEG" in label:
                        sentiment_scores.append(-score)
                    else:
                        sentiment_scores.append(0.0)
                except Exception as e:
                    logger.debug(f"Sentiment analysis failed for text: {e}")
                    sentiment_scores.append(self._calculate_sentiment(text))
            else:
                sentiment_scores.append(self._calculate_sentiment(text))

        # Determine sentiment trend
        if len(sentiment_scores) >= 2:
            mid = len(sentiment_scores) // 2
            first_half_avg = sum(sentiment_scores[:mid]) / len(sentiment_scores[:mid])
            second_half_avg = sum(sentiment_scores[mid:]) / len(sentiment_scores[mid:])
            if second_half_avg > first_half_avg + 0.1:
                sentiment_trend = "positive"
            elif second_half_avg < first_half_avg - 0.1:
                sentiment_trend = "negative"
            else:
                sentiment_trend = "neutral"
        else:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
            if avg_sentiment > 0.1:
                sentiment_trend = "positive"
            elif avg_sentiment < -0.1:
                sentiment_trend = "negative"
            else:
                sentiment_trend = "neutral"

        # Toxicity Analysis
        toxicity_score = 0.0
        toxicity_model = self.model_loader.get_toxicity_model()
        if toxicity_model:
            try:
                toxic_scores = []
                for text in all_texts[:50]:  # Limit to avoid timeout
                    try:
                        result = toxicity_model(text[:512])
                        # Check if any label indicates toxicity
                        for item in result:
                            if isinstance(item, dict):
                                label = item.get("label", "").lower()
                                score = item.get("score", 0.0)
                                if any(toxic in label for toxic in ["toxic", "hate", "threat", "insult", "obscene"]):
                                    toxic_scores.append(score)
                    except Exception:
                        continue
                if toxic_scores:
                    toxicity_score = sum(toxic_scores) / len(toxic_scores)
            except Exception as e:
                logger.warning(f"Toxicity analysis failed: {e}")

        return {
            "dominantThemes": dominant_themes[:5],
            "themeEvolution": theme_evolution,
            "sentimentTrend": sentiment_trend,
            "toxicityScore": round(toxicity_score, 3),
        }
