"""
Phase 3: Behavioral & Temporal Analysis

LSTM/temporal analysis, change-point detection, posting frequency.
"""

import logging
import statistics
from collections import defaultdict
from typing import Any, Dict, List

import numpy as np

from app.models.scraped_data import ScrapedData

logger = logging.getLogger(__name__)


class Phase3Behavioral:
    """Handles behavioral and temporal analysis."""

    def _detect_change_points(self, counts: List[float], dates: List[str]) -> List[str]:
        """Detect change points using statistical methods."""
        if len(counts) < 3:
            return []

        change_points = []
        try:
            # Use PELT (Pruned Exact Linear Time) algorithm for change point detection
            from ruptures import Binseg, Window

            # Convert to numpy array
            signal = np.array(counts, dtype=float)

            # Use binary segmentation for change point detection
            algo = Binseg(model="rbf").fit(signal)
            # Detect up to 5 change points
            n_bkps = min(5, len(counts) // 2)
            if n_bkps > 0:
                bkps = algo.predict(n_bkps=n_bkps)
                # Convert breakpoint indices to dates
                for bkp in bkps[:-1]:  # Last one is always the end
                    if 0 < bkp < len(dates):
                        change_points.append(dates[bkp])
        except ImportError:
            # Fallback to statistical variance method
            logger.debug("ruptures not available, using statistical fallback")
            for i in range(1, len(counts) - 1):
                window = counts[max(0, i - 1) : min(len(counts), i + 2)]
                if len(window) >= 2:
                    mean_val = statistics.mean(window)
                    if mean_val > 0:
                        std_dev = statistics.stdev(window) if len(window) > 1 else 0
                        if abs(counts[i] - mean_val) > 2 * std_dev and std_dev > 0:
                            change_points.append(dates[i])
        except Exception as e:
            logger.warning(f"Change point detection failed: {e}")

        return change_points[:5]

    def _lstm_temporal_analysis(self, counts: List[float]) -> Dict[str, Any]:
        """LSTM-based temporal pattern analysis."""
        if len(counts) < 4:
            return {"pattern": "insufficient_data", "trend_strength": 0.0}

        try:
            import torch
            import torch.nn as nn

            # Prepare data for LSTM
            sequence_length = min(3, len(counts) - 1)
            X = []
            y = []

            for i in range(len(counts) - sequence_length):
                X.append(counts[i : i + sequence_length])
                y.append(counts[i + sequence_length])

            if not X:
                return {"pattern": "insufficient_data", "trend_strength": 0.0}

            X = np.array(X, dtype=np.float32)
            y = np.array(y, dtype=np.float32)

            # Normalize
            X_mean, X_std = X.mean(), X.std() + 1e-8
            y_mean, y_std = y.mean(), y.std() + 1e-8
            X = (X - X_mean) / X_std
            y = (y - y_mean) / y_std

            # Simple LSTM model
            class SimpleLSTM(nn.Module):
                def __init__(self, input_size=1, hidden_size=10, num_layers=1):
                    super().__init__()
                    self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
                    self.fc = nn.Linear(hidden_size, 1)

                def forward(self, x):
                    lstm_out, _ = self.lstm(x)
                    return self.fc(lstm_out[:, -1, :])

            # Train a simple model
            model = SimpleLSTM(input_size=1, hidden_size=10)
            criterion = nn.MSELoss()
            optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

            X_tensor = torch.from_numpy(X).unsqueeze(-1)
            y_tensor = torch.from_numpy(y).unsqueeze(-1)

            # Quick training (few epochs for speed)
            model.train()
            for _ in range(10):
                optimizer.zero_grad()
                outputs = model(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()

            # Predict trend
            model.eval()
            with torch.no_grad():
                predictions = model(X_tensor).squeeze().numpy()
                predictions = predictions * y_std + y_mean

            # Calculate trend strength
            if len(predictions) > 1:
                trend = np.polyfit(range(len(predictions)), predictions, 1)[0]
                trend_strength = abs(trend) / (np.std(predictions) + 1e-8)
                pattern = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
            else:
                pattern = "stable"
                trend_strength = 0.0

            return {"pattern": pattern, "trend_strength": float(trend_strength)}

        except Exception as e:
            logger.warning(f"LSTM analysis failed: {e}. Using statistical fallback.")
            # Fallback to simple trend analysis
            if len(counts) >= 2:
                trend = np.polyfit(range(len(counts)), counts, 1)[0]
                pattern = "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable"
                trend_strength = abs(trend) / (statistics.stdev(counts) + 1e-8) if len(counts) > 1 else 0.0
                return {"pattern": pattern, "trend_strength": float(trend_strength)}
            return {"pattern": "stable", "trend_strength": 0.0}

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
        import re

        words = re.findall(r"\b\w+\b", text.lower())
        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        total = len(words) or 1

        return (pos_count - neg_count) / max(total, 1)

    async def execute(
        self, scraped_items: List[ScrapedData], features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """LSTM/temporal analysis, change-point detection, posting frequency."""
        if not scraped_items:
            return {
                "postingFrequencyTrend": "stable",
                "escalationDetected": False,
                "changePoints": [],
            }

        # Sort by timestamp
        sorted_items = sorted(scraped_items, key=lambda x: x.scrapedAt)

        if len(sorted_items) < 2:
            return {
                "postingFrequencyTrend": "stable",
                "escalationDetected": False,
                "changePoints": [],
            }

        # Group by time periods (daily buckets)
        daily_counts: Dict[str, int] = defaultdict(int)
        for item in sorted_items:
            date_key = item.scrapedAt.strftime("%Y-%m-%d")
            daily_counts[date_key] += 1

        dates = sorted(daily_counts.keys())
        counts = [daily_counts[d] for d in dates]

        # LSTM-based temporal analysis
        lstm_results = self._lstm_temporal_analysis(counts)

        # Determine frequency trend
        if len(counts) >= 2:
            # Use LSTM pattern if available
            if lstm_results.get("pattern") != "insufficient_data":
                frequency_trend = lstm_results["pattern"]
            else:
                # Fallback to statistical analysis
                if len(counts) >= 3:
                    std_dev = statistics.stdev(counts) if len(counts) > 1 else 0
                    mean_count = statistics.mean(counts)
                    coefficient_of_variation = std_dev / mean_count if mean_count > 0 else 0

                    if coefficient_of_variation > 0.5:
                        frequency_trend = "erratic"
                    else:
                        first_half = counts[: len(counts) // 2]
                        second_half = counts[len(counts) // 2 :]
                        first_avg = sum(first_half) / len(first_half) if first_half else 0
                        second_avg = sum(second_half) / len(second_half) if second_half else 0

                        if second_avg > first_avg * 1.5:
                            frequency_trend = "increasing"
                        else:
                            frequency_trend = "stable"
                else:
                    if counts[1] > counts[0] * 1.5:
                        frequency_trend = "increasing"
                    else:
                        frequency_trend = "stable"
        else:
            frequency_trend = "stable"

        # Change point detection
        change_points = self._detect_change_points(counts, dates)

        # Escalation detection: check for increasing negative sentiment or aggression
        escalation_detected = False
        if len(sorted_items) >= 3:
            mid = len(sorted_items) // 2
            early_text = " ".join([item.rawContent for item in sorted_items[:mid] if item.rawContent])
            late_text = " ".join([item.rawContent for item in sorted_items[mid:] if item.rawContent])

            early_sentiment = self._calculate_sentiment(early_text)
            late_sentiment = self._calculate_sentiment(late_text)

            # Escalation if sentiment becomes significantly more negative
            if late_sentiment < early_sentiment - 0.2:
                escalation_detected = True

        return {
            "postingFrequencyTrend": frequency_trend,
            "escalationDetected": escalation_detected,
            "changePoints": change_points,
            "temporalPattern": lstm_results.get("pattern", "stable"),
            "trendStrength": lstm_results.get("trend_strength", 0.0),
        }
