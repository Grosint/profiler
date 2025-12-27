import logging
import re
from collections import Counter
from typing import Any, Dict, List

from app.models.scraped_data import ScrapedData
from app.services.toxicity_analyzer import ToxicityAnalyzer

logger = logging.getLogger(__name__)


WORD_RE = re.compile(r"\w+")
SENTENCE_RE = re.compile(r"[.!?]+")


def _basic_sentiment(text: str) -> Dict[str, float]:
    """
    Very simple lexicon-based sentiment as a placeholder.
    """
    positive_words = {"good", "great", "excellent", "happy", "love", "like"}
    negative_words = {"bad", "terrible", "awful", "hate", "angry", "sad"}

    tokens = [w.lower() for w in WORD_RE.findall(text)]
    total = len(tokens) or 1
    pos = sum(1 for t in tokens if t in positive_words)
    neg = sum(1 for t in tokens if t in negative_words)
    return {
        "positive_ratio": pos / total,
        "negative_ratio": neg / total,
    }


async def process_profile(scraped_items: List[ScrapedData]) -> Dict[str, Any]:
    """
    Aggregate and normalize text, compute basic features, and analyze comments for toxicity.
    """
    full_text_parts: List[str] = []
    per_platform_lengths: Counter[str] = Counter()

    for item in scraped_items:
        if not item.rawContent:
            continue
        full_text_parts.append(item.rawContent)
        per_platform_lengths[item.platform.value] += len(item.rawContent)

    full_text = "\n".join(full_text_parts)
    word_count = len(WORD_RE.findall(full_text))
    sentence_count = max(len(SENTENCE_RE.findall(full_text)), 1)

    sentiment = _basic_sentiment(full_text)

    # Analyze comments for toxicity and identify toxic commenters
    toxicity_analyzer = ToxicityAnalyzer()
    toxicity_analysis = toxicity_analyzer.analyze_comments_from_scraped_data(scraped_items)

    features: Dict[str, Any] = {
        "text": full_text,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": word_count / sentence_count if sentence_count else 0.0,
        "per_platform_lengths": dict(per_platform_lengths),
        "sentiment": sentiment,
        "toxicity_analysis": toxicity_analysis,
    }

    logger.info(
        "Processing phase finished",
        extra={
            "word_count": word_count,
            "sentence_count": sentence_count,
            "toxic_commenters_count": toxicity_analysis.get("statistics", {}).get("toxic_commenters_count", 0),
        },
    )
    return features
