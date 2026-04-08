"""Tests for memory_poison_scorer — the pip-installable artifact."""

import pytest

from memory_poison_scorer import PersistenceScorer, ScorerResult


class TestScorerBasic:
    def setup_method(self):
        self.scorer = PersistenceScorer()

    def test_returns_scorer_result(self):
        result = self.scorer.assess({"architecture": "flat_vector"})
        assert isinstance(result, ScorerResult)

    def test_risk_score_bounded(self):
        for arch in ["flat_vector", "episodic", "multi_layer", "recency"]:
            result = self.scorer.assess({"architecture": arch})
            assert 0.0 <= result.risk_score <= 1.0

    def test_risk_level_valid(self):
        result = self.scorer.assess({"architecture": "episodic"})
        assert result.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_recommendations_not_empty(self):
        result = self.scorer.assess({"architecture": "flat_vector"})
        assert len(result.recommendations) > 0


class TestArchitectureRiskOrdering:
    """Flat vector (no decay) should be riskier than episodic (with decay)."""

    def setup_method(self):
        self.scorer = PersistenceScorer()

    def test_flat_vector_highest_risk(self):
        flat = self.scorer.assess({"architecture": "flat_vector"})
        episodic = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
        })
        assert flat.risk_score >= episodic.risk_score

    def test_faster_decay_lower_risk(self):
        slow = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.999,
        })
        fast = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.9,
        })
        assert slow.risk_score >= fast.risk_score


class TestP0Values:
    def setup_method(self):
        self.scorer = PersistenceScorer()

    def test_flat_vector_very_high_p0(self):
        result = self.scorer.assess({"architecture": "flat_vector"})
        # flat_vector uses epsilon decay (1e-10), so P0 is very large but not inf
        assert result.p0 > 1e6

    def test_episodic_finite_p0(self):
        result = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
        })
        assert result.p0 != float("inf")
        assert result.p0 > 0

    def test_rag_alias(self):
        rag = self.scorer.assess({"architecture": "rag"})
        flat = self.scorer.assess({"architecture": "flat_vector"})
        assert rag.p0 == flat.p0


class TestParameterSensitivity:
    def setup_method(self):
        self.scorer = PersistenceScorer()

    def test_larger_memory_dilutes_poison(self):
        small = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
            "memory_size": 100,
        })
        large = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
            "memory_size": 10000,
        })
        assert large.risk_score <= small.risk_score

    def test_higher_threshold_reduces_risk(self):
        low = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
            "similarity_threshold": 0.0,
        })
        high = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
            "similarity_threshold": 0.9,
            "poison_similarity": 0.85,  # below threshold
        })
        assert high.risk_score <= low.risk_score


class TestConsolidationAmplification:
    def setup_method(self):
        self.scorer = PersistenceScorer()

    def test_consolidation_increases_risk(self):
        without = self.scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.995,
            "memory_size": 500,
        })
        with_consol = self.scorer.assess({
            "architecture": "multi_layer",
            "decay_rate": 0.995,
            "memory_size": 500,
            "has_consolidation": True,
        })
        assert with_consol.risk_score >= without.risk_score


class TestDetails:
    def test_details_contains_params(self):
        scorer = PersistenceScorer()
        result = scorer.assess({
            "architecture": "episodic",
            "decay_rate": 0.99,
            "memory_size": 500,
        })
        assert "architecture" in result.details
        assert "retrieval_probability" in result.details
        assert "effective_decay_rate" in result.details
        assert result.details["architecture"] == "episodic"
