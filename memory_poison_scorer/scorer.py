"""Core scorer module — the practitioner-facing API.

Takes architecture configuration parameters and outputs persistence
risk assessment. No experiment infrastructure required.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ScorerResult:
    """Result of a persistence risk assessment."""
    risk_score: float  # 0.0 (no risk) to 1.0 (maximum persistence risk)
    p0: float  # persistence number
    predicted_halflife: float | None  # steps until half decay; None = indefinite
    persistence_probability_1000: float  # P(still active after 1000 interactions)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    recommendations: list[str]
    details: dict[str, Any]


# Architecture-specific default parameters
_ARCH_DEFAULTS = {
    "flat_vector": {"decay_rate": 0.0, "has_consolidation": False},
    "episodic": {"decay_rate": 0.995, "has_consolidation": False},
    "multi_layer": {"decay_rate": 0.995, "has_consolidation": True},
    "recency": {"decay_rate": 0.0, "has_consolidation": False},
    "rag": {"decay_rate": 0.0, "has_consolidation": False},  # alias for flat_vector
}

# Empirically calibrated from E1-E3 experiments
_RISK_THRESHOLDS = {
    "critical": 0.85,
    "high": 0.6,
    "medium": 0.3,
}


class PersistenceScorer:
    """Assess persistence risk of memory poisoning for a given architecture.

    The scorer uses the P0 framework (persistence number) to predict
    whether poisoned memories will persist, decay, or amplify in a
    given memory architecture configuration.
    """

    def __init__(
        self,
        default_poison_rate: float = 0.05,
        default_poison_similarity: float = 0.85,
    ):
        self.default_poison_rate = default_poison_rate
        self.default_poison_similarity = default_poison_similarity

    def assess(self, config: dict[str, Any]) -> ScorerResult:
        """Assess persistence risk for an architecture configuration.

        Args:
            config: Dictionary with keys:
                - architecture: str — one of "flat_vector", "episodic",
                  "multi_layer", "recency", "rag"
                - decay_rate: float — per-step decay factor (0=instant, 1=no decay)
                - similarity_threshold: float — minimum cosine similarity for retrieval
                - memory_size: int — total memory capacity
                - retrieval_k: int — number of memories retrieved per query
                - poison_rate: float (optional) — assumed fraction of poisoned memories
                - poison_similarity: float (optional) — assumed poison-to-query similarity
                - consolidation_interval: int (optional) — steps between consolidation
                - consolidation_threshold: int (optional) — retrievals to promote

        Returns:
            ScorerResult with risk assessment.
        """
        arch = config.get("architecture", "flat_vector")
        if arch == "rag":
            arch = "flat_vector"

        defaults = _ARCH_DEFAULTS.get(arch, _ARCH_DEFAULTS["flat_vector"])
        decay_rate = config.get("decay_rate", defaults["decay_rate"])
        similarity_threshold = config.get("similarity_threshold", 0.0)
        memory_size = config.get("memory_size", 1000)
        retrieval_k = config.get("retrieval_k", 5)
        poison_rate = config.get("poison_rate", self.default_poison_rate)
        poison_similarity = config.get("poison_similarity", self.default_poison_similarity)
        has_consolidation = config.get("has_consolidation", defaults["has_consolidation"])

        n_poison = int(memory_size * poison_rate)

        # Estimate retrieval probability
        if arch == "recency":
            retrieval_prob = min(1.0, retrieval_k * n_poison / memory_size)
        else:
            if poison_similarity < similarity_threshold:
                retrieval_prob = 0.0
            else:
                base_prob = min(1.0, retrieval_k * n_poison / memory_size)
                threshold_boost = 1.0 + similarity_threshold
                retrieval_prob = min(1.0, base_prob * threshold_boost)

        # Estimate effective decay
        if arch == "flat_vector":
            effective_decay = 1e-10
        elif arch == "recency":
            effective_decay = 1.0 / memory_size
        elif arch == "multi_layer" and has_consolidation:
            consolidation_prob = 0.1  # approximate
            effective_decay = (1.0 - consolidation_prob) * (1.0 - decay_rate)
        else:
            effective_decay = 1.0 - decay_rate

        # Compute P0
        if effective_decay < 1e-10:
            p0 = float("inf") if retrieval_prob > 0 else 0.0
        else:
            p0 = retrieval_prob / effective_decay

        # Predict half-life
        if p0 >= 1.0 or effective_decay < 1e-10:
            predicted_halflife = None
        else:
            import math
            net_decay = effective_decay * (1.0 - p0)
            if net_decay < 1e-10:
                predicted_halflife = None
            else:
                predicted_halflife = math.log(2) / net_decay

        # Persistence probability at 1000 steps
        if p0 >= 1.0 or effective_decay < 1e-10:
            persistence_1000 = 1.0
        else:
            import math
            net_decay = effective_decay * (1.0 - p0)
            persistence_1000 = math.exp(-net_decay * 1000)

        # Risk score (0-1)
        if p0 >= 1.0 or predicted_halflife is None:
            risk_score = 1.0
        else:
            # Normalize: halflife of 1 step = 0 risk, 1000+ steps = 1.0 risk
            risk_score = min(1.0, predicted_halflife / 1000.0)

        # Amplification risk for multi-layer
        if has_consolidation and risk_score > 0.5:
            risk_score = min(1.0, risk_score * 1.3)  # consolidation amplification

        # Risk level
        if risk_score >= _RISK_THRESHOLDS["critical"]:
            risk_level = "CRITICAL"
        elif risk_score >= _RISK_THRESHOLDS["high"]:
            risk_level = "HIGH"
        elif risk_score >= _RISK_THRESHOLDS["medium"]:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Recommendations
        recommendations = self._generate_recommendations(
            arch, risk_level, p0, decay_rate, similarity_threshold,
            has_consolidation, predicted_halflife,
        )

        return ScorerResult(
            risk_score=risk_score,
            p0=p0,
            predicted_halflife=predicted_halflife,
            persistence_probability_1000=persistence_1000,
            risk_level=risk_level,
            recommendations=recommendations,
            details={
                "architecture": arch,
                "retrieval_probability": retrieval_prob,
                "effective_decay_rate": effective_decay,
                "poison_rate": poison_rate,
                "poison_similarity": poison_similarity,
                "memory_size": memory_size,
                "retrieval_k": retrieval_k,
                "has_consolidation": has_consolidation,
            },
        )

    def _generate_recommendations(
        self,
        arch: str,
        risk_level: str,
        p0: float,
        decay_rate: float,
        similarity_threshold: float,
        has_consolidation: bool,
        predicted_halflife: float | None,
    ) -> list[str]:
        recs = []

        if risk_level in ("CRITICAL", "HIGH"):
            if decay_rate > 0.99 or decay_rate == 0.0:
                recs.append(
                    "Add or increase memory decay rate. "
                    f"Current decay provides P0={p0:.1f}. "
                    "Target decay rate <= 0.99 to bring P0 below 1.0."
                )
            if similarity_threshold < 0.3:
                recs.append(
                    "Increase similarity threshold for retrieval. "
                    f"Current threshold ({similarity_threshold}) allows broad retrieval. "
                    "Threshold >= 0.5 reduces retrieval probability of adversarial memories."
                )
            if has_consolidation:
                recs.append(
                    "Add provenance tracking before memory consolidation. "
                    "Consolidated poisoned memories persist indefinitely in semantic layer."
                )
            recs.append(
                "Consider adding memory provenance tracking (source, timestamp, trust score) "
                "to enable post-hoc identification of injected memories."
            )

        elif risk_level == "MEDIUM":
            recs.append(
                f"Monitor persistence metrics. Predicted half-life: "
                f"{predicted_halflife:.0f} steps. "
                "Consider increasing decay rate if poisoning risk is high."
            )

        else:  # LOW
            recs.append(
                "Current architecture configuration provides natural decay of poisoned memories. "
                "Standard monitoring is sufficient."
            )

        return recs
