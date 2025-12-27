"""
Phase 7: Risk & Threat Vector Calculation

Ensemble risk models with Bayesian weighting.
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class Phase7Risk:
    """Handles risk and threat vector calculation."""

    def _bayesian_weighted_risk(
        self, risk_components: List[Tuple[float, float]], prior: float = 0.3
    ) -> float:
        """
        Calculate Bayesian-weighted risk score.

        Args:
            risk_components: List of (risk_value, confidence) tuples
            prior: Prior probability of risk (default 0.3)

        Returns:
            Bayesian-weighted risk score (0-1)
        """
        if not risk_components:
            return prior

        # Bayesian update: combine evidence with prior
        # Using log-space for numerical stability
        log_prior_odds = np.log(prior / (1 - prior + 1e-10))

        # Combine evidence from components
        log_posterior_odds = log_prior_odds
        for risk_value, confidence in risk_components:
            # Likelihood ratio based on risk value and confidence
            # Higher risk value and confidence = stronger evidence
            likelihood_ratio = (risk_value * confidence) / (1 - risk_value * confidence + 1e-10)
            log_likelihood = np.log(likelihood_ratio + 1e-10)
            # Weight by confidence
            log_posterior_odds += log_likelihood * confidence

        # Convert back to probability
        posterior_odds = np.exp(log_posterior_odds)
        posterior_prob = posterior_odds / (1 + posterior_odds)

        return float(np.clip(posterior_prob, 0.0, 1.0))

    async def execute(
        self,
        identity_results: Dict[str, Any],
        narrative_results: Dict[str, Any],
        behavioral_results: Dict[str, Any],
        network_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ensemble risk models with Bayesian weighting."""
        # Calculate individual risk dimensions with confidence scores

        # 1. Ideological Risk: based on narrative themes, sentiment, and toxicity
        sentiment_trend = narrative_results.get("sentimentTrend", "neutral")
        toxicity_score = narrative_results.get("toxicityScore", 0.0)
        theme_count = len(narrative_results.get("dominantThemes", []))

        # Base risk from sentiment
        sentiment_risk = 0.1
        sentiment_confidence = 0.6
        if sentiment_trend == "negative":
            sentiment_risk = 0.5
            sentiment_confidence = 0.8
        elif sentiment_trend == "positive":
            sentiment_risk = 0.1
            sentiment_confidence = 0.7

        # Toxicity contribution
        toxicity_risk = min(0.8, toxicity_score * 1.2)
        toxicity_confidence = 0.9 if toxicity_score > 0.3 else 0.5

        # Theme persistence contribution
        theme_risk = min(0.4, theme_count * 0.08)
        theme_confidence = min(0.9, 0.5 + (theme_count * 0.1))

        # Bayesian combination of ideological risk components
        ideological_components = [
            (sentiment_risk, sentiment_confidence),
            (toxicity_risk, toxicity_confidence),
            (theme_risk, theme_confidence),
        ]
        ideological_risk = self._bayesian_weighted_risk(ideological_components, prior=0.2)

        # 2. Mobilization Risk: based on network influence, escalation, and behavioral changes
        influence_score = network_results.get("influenceScore", 0.0)
        escalation = behavioral_results.get("escalationDetected", False)
        change_points_count = len(behavioral_results.get("changePoints", []))
        trend_strength = behavioral_results.get("trendStrength", 0.0)

        # Influence contribution
        influence_risk = min(0.7, influence_score * 1.2)
        influence_confidence = 0.8 if influence_score > 0.3 else 0.5

        # Escalation contribution
        escalation_risk = 0.6 if escalation else 0.1
        escalation_confidence = 0.9 if escalation else 0.5

        # Behavioral change contribution
        change_risk = min(0.5, change_points_count * 0.15)
        change_confidence = min(0.8, 0.4 + (change_points_count * 0.1))

        # Trend strength contribution
        trend_risk = min(0.4, trend_strength * 0.5)
        trend_confidence = 0.7 if trend_strength > 0.3 else 0.4

        # Bayesian combination
        mobilization_components = [
            (influence_risk, influence_confidence),
            (escalation_risk, escalation_confidence),
            (change_risk, change_confidence),
            (trend_risk, trend_confidence),
        ]
        mobilization_risk = self._bayesian_weighted_risk(mobilization_components, prior=0.15)

        # 3. Network Risk: based on community count, connections, and centrality
        community_count = network_results.get("communityCount", 0)
        connections = network_results.get("uniqueConnections", 0)
        degree_centrality = network_results.get("degreeCentrality", 0.0)
        betweenness_centrality = network_results.get("betweennessCentrality", 0.0)

        # Community diversity risk
        community_risk = min(0.5, community_count * 0.15)
        community_confidence = min(0.8, 0.4 + (community_count * 0.1))

        # Connection volume risk
        connection_risk = min(0.6, connections / 50.0)
        connection_confidence = min(0.9, 0.5 + (connections / 100.0))

        # Centrality risk (high centrality = high influence potential)
        centrality_risk = (degree_centrality * 0.5) + (betweenness_centrality * 0.5)
        centrality_confidence = 0.8 if (degree_centrality > 0.3 or betweenness_centrality > 0.3) else 0.5

        # Bayesian combination
        network_components = [
            (community_risk, community_confidence),
            (connection_risk, connection_confidence),
            (centrality_risk, centrality_confidence),
        ]
        network_risk = self._bayesian_weighted_risk(network_components, prior=0.2)

        # 4. Volatility Risk: based on behavioral changes, frequency patterns, and identity consistency
        frequency_trend = behavioral_results.get("postingFrequencyTrend", "stable")
        persona_consistency = identity_results.get("personaConsistencyScore", 0.5)

        # Frequency pattern risk
        frequency_risk = 0.1
        frequency_confidence = 0.6
        if frequency_trend == "erratic":
            frequency_risk = 0.6
            frequency_confidence = 0.8
        elif frequency_trend == "increasing":
            frequency_risk = 0.3
            frequency_confidence = 0.7

        # Identity consistency risk (low consistency = higher volatility risk)
        consistency_risk = 1.0 - persona_consistency
        consistency_confidence = 0.7

        # Change points risk (already calculated above, reuse)
        volatility_components = [
            (frequency_risk, frequency_confidence),
            (consistency_risk, consistency_confidence),
            (change_risk, change_confidence),
        ]
        volatility_risk = self._bayesian_weighted_risk(volatility_components, prior=0.2)

        # Calculate overall confidence using Bayesian approach
        identity_confidence = identity_results.get("identityConfidence", 0.5)
        confidence_components = [
            (identity_confidence, 0.8),
            (sentiment_confidence, 0.7),
            (influence_confidence, 0.7),
        ]
        confidence_score = self._bayesian_weighted_risk(confidence_components, prior=0.5)

        if confidence_score >= 0.8:
            confidence_level = "high"
        elif confidence_score >= 0.6:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        risk_score = {
            "ideological": round(ideological_risk, 3),
            "mobilization": round(mobilization_risk, 3),
            "network": round(network_risk, 3),
            "volatility": round(volatility_risk, 3),
            "confidence": confidence_level,
            "confidenceScore": round(confidence_score, 3),
        }

        # Generate top traits based on risk dimensions
        top_traits = []
        if ideological_risk > 0.5:
            top_traits.append("elevated ideological risk indicators")
        if mobilization_risk > 0.5:
            top_traits.append("potential mobilization signals")
        if network_risk > 0.6:
            top_traits.append("high network connectivity")
        if volatility_risk > 0.5:
            top_traits.append("behavioral volatility detected")
        if escalation:
            top_traits.append("escalation indicators present")
        if toxicity_score > 0.3:
            top_traits.append("toxic content detected")

        # Add identity consistency traits
        if persona_consistency < 0.4:
            top_traits.append("low persona consistency")
        elif persona_consistency > 0.8:
            top_traits.append("high persona consistency")

        # Add narrative traits
        if theme_count > 3:
            top_traits.append("high narrative persistence")

        # Limit to top 5 traits
        top_traits = top_traits[:5]

        return {
            "riskScore": risk_score,
            "topTraits": top_traits,
        }
