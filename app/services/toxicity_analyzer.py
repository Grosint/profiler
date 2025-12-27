"""
Toxicity Analyzer Service

Analyzes comments and replies for toxicity and identifies toxic commenters.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ToxicityAnalyzer:
    """Analyzes text for toxicity and tracks toxic commenters."""

    def __init__(self):
        self._toxicity_model = None
        self._sentiment_model = None

    def _get_toxicity_model(self):
        """Lazy load toxicity classifier."""
        if self._toxicity_model is None:
            try:
                from transformers import pipeline

                logger.info("Loading toxicity classifier...")
                self._toxicity_model = pipeline(
                    "text-classification",
                    model="unitary/toxic-bert",
                    return_all_scores=True
                )
                logger.info("Toxicity classifier loaded")
            except Exception as e:
                logger.warning(f"Failed to load toxicity model: {e}. Using fallback.")
                self._toxicity_model = False
        return self._toxicity_model if self._toxicity_model is not False else None

    def _get_sentiment_model(self):
        """Lazy load sentiment analysis model."""
        if self._sentiment_model is None:
            try:
                from transformers import pipeline

                logger.info("Loading sentiment analysis model...")
                self._sentiment_model = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
                )
                logger.info("Sentiment analysis model loaded")
            except Exception as e:
                logger.warning(f"Failed to load sentiment model: {e}. Using fallback.")
                self._sentiment_model = False
        return self._sentiment_model if self._sentiment_model is not False else None

    def analyze_comment(self, comment_text: str) -> Dict[str, Any]:
        """
        Analyze a single comment for toxicity.

        Returns:
            Dictionary with toxicity_score, is_toxic, toxicity_labels, and sentiment
        """
        if not comment_text or len(comment_text.strip()) == 0:
            return {
                "toxicity_score": 0.0,
                "is_toxic": False,
                "toxicity_labels": [],
                "sentiment": "neutral",
                "sentiment_score": 0.0,
            }

        toxicity_score = 0.0
        is_toxic = False
        toxicity_labels = []
        sentiment = "neutral"
        sentiment_score = 0.0

        # Use toxicity model if available
        toxicity_model = self._get_toxicity_model()
        if toxicity_model:
            try:
                results = toxicity_model(comment_text[:512])  # Limit length
                for result in results:
                    if isinstance(result, dict):
                        label = result.get("label", "").lower()
                        score = result.get("score", 0.0)
                        # Check for toxic labels
                        toxic_keywords = ["toxic", "hate", "threat", "insult", "obscene", "severe_toxic", "identity_hate"]
                        if any(keyword in label for keyword in toxic_keywords):
                            if score > toxicity_score:
                                toxicity_score = score
                            if score > 0.5:  # Threshold for toxic
                                is_toxic = True
                                toxicity_labels.append({"label": label, "score": score})
            except Exception as e:
                logger.debug(f"Toxicity analysis failed: {e}")

        # Fallback to keyword-based detection if model not available
        if not toxicity_model or toxicity_score == 0.0:
            toxicity_score, is_toxic, toxicity_labels = self._keyword_toxicity_check(comment_text)

        # Sentiment analysis
        sentiment_model = self._get_sentiment_model()
        if sentiment_model:
            try:
                result = sentiment_model(comment_text[:512])
                if isinstance(result, list) and len(result) > 0:
                    label = result[0].get("label", "").upper()
                    score = result[0].get("score", 0.0)
                    if "POSITIVE" in label or "POS" in label:
                        sentiment = "positive"
                        sentiment_score = score
                    elif "NEGATIVE" in label or "NEG" in label:
                        sentiment = "negative"
                        sentiment_score = -score
                    else:
                        sentiment = "neutral"
                        sentiment_score = 0.0
            except Exception as e:
                logger.debug(f"Sentiment analysis failed: {e}")
                sentiment, sentiment_score = self._keyword_sentiment_check(comment_text)

        return {
            "toxicity_score": round(toxicity_score, 3),
            "is_toxic": is_toxic,
            "toxicity_labels": toxicity_labels,
            "sentiment": sentiment,
            "sentiment_score": round(sentiment_score, 3),
        }

    def _keyword_toxicity_check(self, text: str) -> Tuple[float, bool, List[Dict[str, str]]]:
        """Fallback keyword-based toxicity detection."""
        toxic_keywords = {
            "hate": ["hate", "kill", "die", "stupid", "idiot", "moron", "retard", "fuck", "shit", "damn"],
            "threat": ["kill", "murder", "attack", "destroy", "harm", "hurt", "threat"],
            "insult": ["stupid", "idiot", "moron", "dumb", "fool", "loser", "pathetic"],
            "obscene": ["fuck", "shit", "damn", "asshole", "bitch", "bastard"],
        }

        text_lower = text.lower()
        max_score = 0.0
        is_toxic = False
        labels = []

        for category, keywords in toxic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                score = min(0.8, matches * 0.2)  # Cap at 0.8 for keyword-based
                if score > max_score:
                    max_score = score
                if score > 0.5:
                    is_toxic = True
                    labels.append({"label": category, "score": score})

        return max_score, is_toxic, labels

    def _keyword_sentiment_check(self, text: str) -> Tuple[str, float]:
        """Fallback keyword-based sentiment detection."""
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

        words = text.lower().split()
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        total = len(words) or 1

        if pos_count > neg_count:
            return "positive", min(0.7, pos_count / total)
        elif neg_count > pos_count:
            return "negative", -min(0.7, neg_count / total)
        else:
            return "neutral", 0.0

    def analyze_comments_from_scraped_data(
        self, scraped_items: List[Any]
    ) -> Dict[str, Any]:
        """
        Analyze all comments from scraped data and identify toxic commenters.

        Returns:
            Dictionary with:
            - toxic_commenters: List of commenters who made toxic comments
            - comment_analysis: Analysis of all comments
            - statistics: Overall statistics
        """
        toxic_commenters = defaultdict(lambda: {
            "username": "",
            "name": "",
            "platform": "",
            "toxic_comments": [],
            "total_comments": 0,
            "toxicity_score_avg": 0.0,
            "worst_comment": None,
        })

        all_comments_analysis = []
        total_comments = 0
        total_toxic_comments = 0

        for item in scraped_items:
            if not item.metadata:
                continue

            platform = item.platform.value if hasattr(item, "platform") else "unknown"
            posts = item.metadata.get("posts", []) or item.metadata.get("tweets", [])

            # Handle Reddit comments (they're separate from posts)
            if platform == "reddit" and "comments" in item.metadata:
                reddit_comments = item.metadata.get("comments", [])
                for comment in reddit_comments:
                    total_comments += 1
                    comment_text = comment.get("text", "")
                    if not comment_text:
                        continue

                    analysis = self.analyze_comment(comment_text)
                    analysis["comment_id"] = comment.get("id")
                    analysis["comment_text"] = comment_text[:200]

                    username = item.metadata.get("profile_info", {}).get("username", "unknown")
                    if username and username != "unknown":
                        commenter_key = f"{platform}:{username}"
                        toxic_commenters[commenter_key]["username"] = username
                        toxic_commenters[commenter_key]["platform"] = platform
                        toxic_commenters[commenter_key]["total_comments"] += 1

                        comment_data = {
                            "id": comment.get("id"),
                            "text": comment_text[:200],
                            "toxicity_score": analysis["toxicity_score"],
                            "is_toxic": analysis["is_toxic"],
                            "timestamp": comment.get("created_at"),
                            "subreddit": comment.get("subreddit"),
                        }

                        if analysis["is_toxic"]:
                            total_toxic_comments += 1
                            toxic_commenters[commenter_key]["toxic_comments"].append(comment_data)

                            worst = toxic_commenters[commenter_key]["worst_comment"]
                            if not worst or analysis["toxicity_score"] > worst.get("toxicity_score", 0):
                                toxic_commenters[commenter_key]["worst_comment"] = comment_data

                        all_comments_analysis.append({
                            **analysis,
                            "platform": platform,
                            "author": {"username": username},
                            "subreddit": comment.get("subreddit"),
                        })

            for post in posts:
                # Analyze comments
                comments = post.get("comments_data") or post.get("comments", [])
                for comment in comments:
                    total_comments += 1
                    comment_text = comment.get("text", "") or comment.get("message", "")
                    if not comment_text:
                        continue

                    # Analyze toxicity
                    analysis = self.analyze_comment(comment_text)
                    analysis["comment_id"] = comment.get("id")
                    analysis["comment_text"] = comment_text[:200]  # Truncate for storage

                    # Extract author info
                    author = comment.get("author", {})
                    if not author:
                        # Try alternative structures
                        author = {
                            "username": comment.get("username", ""),
                            "name": comment.get("name", ""),
                            "id": comment.get("author_id", ""),
                        }

                    username = author.get("username") or author.get("name", "unknown")
                    if username and username != "unknown":
                        commenter_key = f"{platform}:{username}"

                        # Update commenter stats
                        toxic_commenters[commenter_key]["username"] = username
                        toxic_commenters[commenter_key]["name"] = author.get("name", username)
                        toxic_commenters[commenter_key]["platform"] = platform
                        toxic_commenters[commenter_key]["total_comments"] += 1

                        comment_data = {
                            "id": comment.get("id"),
                            "text": comment_text[:200],
                            "toxicity_score": analysis["toxicity_score"],
                            "is_toxic": analysis["is_toxic"],
                            "timestamp": comment.get("created_time") or comment.get("created_at"),
                            "post_id": post.get("id"),
                        }

                        if analysis["is_toxic"]:
                            total_toxic_comments += 1
                            toxic_commenters[commenter_key]["toxic_comments"].append(comment_data)

                            # Track worst comment
                            worst = toxic_commenters[commenter_key]["worst_comment"]
                            if not worst or analysis["toxicity_score"] > worst.get("toxicity_score", 0):
                                toxic_commenters[commenter_key]["worst_comment"] = comment_data

                        all_comments_analysis.append({
                            **analysis,
                            "platform": platform,
                            "author": author,
                            "post_id": post.get("id"),
                        })

                    # Analyze comment replies
                    replies = comment.get("replies", [])
                    for reply in replies:
                        total_comments += 1
                        reply_text = reply.get("text", "") or reply.get("message", "")
                        if not reply_text:
                            continue

                        reply_analysis = self.analyze_comment(reply_text)
                        reply_author = reply.get("author", {})
                        reply_username = reply_author.get("username") or reply_author.get("name", "unknown")

                        if reply_username and reply_username != "unknown":
                            reply_key = f"{platform}:{reply_username}"
                            toxic_commenters[reply_key]["username"] = reply_username
                            toxic_commenters[reply_key]["name"] = reply_author.get("name", reply_username)
                            toxic_commenters[reply_key]["platform"] = platform
                            toxic_commenters[reply_key]["total_comments"] += 1

                            reply_data = {
                                "id": reply.get("id"),
                                "text": reply_text[:200],
                                "toxicity_score": reply_analysis["toxicity_score"],
                                "is_toxic": reply_analysis["is_toxic"],
                                "timestamp": reply.get("created_time") or reply.get("created_at"),
                                "post_id": post.get("id"),
                                "parent_comment_id": comment.get("id"),
                            }

                            if reply_analysis["is_toxic"]:
                                total_toxic_comments += 1
                                toxic_commenters[reply_key]["toxic_comments"].append(reply_data)

                                worst = toxic_commenters[reply_key]["worst_comment"]
                                if not worst or reply_analysis["toxicity_score"] > worst.get("toxicity_score", 0):
                                    toxic_commenters[reply_key]["worst_comment"] = reply_data

                # Analyze replies (for Twitter)
                replies_data = post.get("replies_data", [])
                for reply in replies_data:
                    total_comments += 1
                    reply_text = reply.get("text", "")
                    if not reply_text:
                        continue

                    reply_analysis = self.analyze_comment(reply_text)
                    reply_author = reply.get("author", {})
                    reply_username = reply_author.get("username") or reply_author.get("name", "unknown")

                    if reply_username and reply_username != "unknown":
                        reply_key = f"{platform}:{reply_username}"
                        toxic_commenters[reply_key]["username"] = reply_username
                        toxic_commenters[reply_key]["name"] = reply_author.get("name", reply_username)
                        toxic_commenters[reply_key]["platform"] = platform
                        toxic_commenters[reply_key]["total_comments"] += 1

                        reply_data = {
                            "id": reply.get("id"),
                            "text": reply_text[:200],
                            "toxicity_score": reply_analysis["toxicity_score"],
                            "is_toxic": reply_analysis["is_toxic"],
                            "timestamp": reply.get("created_at"),
                            "post_id": post.get("id"),
                        }

                        if reply_analysis["is_toxic"]:
                            total_toxic_comments += 1
                            toxic_commenters[reply_key]["toxic_comments"].append(reply_data)

                            worst = toxic_commenters[reply_key]["worst_comment"]
                            if not worst or reply_analysis["toxicity_score"] > worst.get("toxicity_score", 0):
                                toxic_commenters[reply_key]["worst_comment"] = reply_data

        # Calculate average toxicity scores for each commenter
        for commenter_key, data in toxic_commenters.items():
            if data["toxic_comments"]:
                avg_score = sum(c["toxicity_score"] for c in data["toxic_comments"]) / len(data["toxic_comments"])
                data["toxicity_score_avg"] = round(avg_score, 3)

        # Filter to only toxic commenters and sort by toxicity
        toxic_commenters_list = [
            {
                "username": data["username"],
                "name": data["name"],
                "platform": data["platform"],
                "toxic_comments_count": len(data["toxic_comments"]),
                "total_comments": data["total_comments"],
                "toxicity_score_avg": data["toxicity_score_avg"],
                "worst_comment": data["worst_comment"],
                "all_toxic_comments": data["toxic_comments"][:10],  # Limit to top 10
            }
            for data in toxic_commenters.values()
            if data["toxic_comments"]
        ]

        # Sort by toxicity score (highest first)
        toxic_commenters_list.sort(key=lambda x: x["toxicity_score_avg"], reverse=True)

        return {
            "toxic_commenters": toxic_commenters_list,
            "comment_analysis": all_comments_analysis[:1000],  # Limit for storage
            "statistics": {
                "total_comments_analyzed": total_comments,
                "total_toxic_comments": total_toxic_comments,
                "toxic_commenters_count": len(toxic_commenters_list),
                "toxicity_rate": round(total_toxic_comments / total_comments, 3) if total_comments > 0 else 0.0,
            },
        }
