"""Tests for src/persistence_model.py — P0 framework validation."""

import math

import numpy as np
import pytest

from src.persistence_model import (
    compute_p0,
    compute_persistence_bound,
    estimate_effective_decay,
    estimate_retrieval_probability,
    fit_persistence_model,
    predict_halflife,
    predict_persistence_trace,
)


class TestRetrievalProbability:
    def test_no_poison(self):
        assert estimate_retrieval_probability(0, 100, 0.9, 5) == 0.0

    def test_no_memories(self):
        assert estimate_retrieval_probability(5, 0, 0.9, 5) == 0.0

    def test_below_threshold(self):
        assert estimate_retrieval_probability(5, 100, 0.3, 5, similarity_threshold=0.5) == 0.0

    def test_proportional_to_poison_rate(self):
        p1 = estimate_retrieval_probability(5, 100, 0.9, 5)
        p2 = estimate_retrieval_probability(10, 100, 0.9, 5)
        assert p2 > p1

    def test_bounded_by_one(self):
        p = estimate_retrieval_probability(1000, 100, 0.99, 50)
        assert p <= 1.0


class TestEffectiveDecay:
    def test_flat_vector_no_decay(self):
        d = estimate_effective_decay(0.0, "flat_vector")
        assert d < 1e-9

    def test_episodic_decay(self):
        d = estimate_effective_decay(0.995, "episodic")
        assert d == pytest.approx(0.005)

    def test_multi_layer_reduced_by_consolidation(self):
        d_ep = estimate_effective_decay(0.995, "episodic")
        d_ml = estimate_effective_decay(0.995, "multi_layer", consolidation_prob=0.1)
        assert d_ml < d_ep  # consolidation reduces effective decay


class TestP0:
    def test_infinite_when_no_decay(self):
        p0 = compute_p0(0.5, 1e-11)
        assert p0 == float("inf")

    def test_zero_when_no_retrieval(self):
        p0 = compute_p0(0.0, 0.01)
        assert p0 == 0.0

    def test_threshold_behavior(self):
        p0_above = compute_p0(0.1, 0.05)
        p0_below = compute_p0(0.01, 0.05)
        assert p0_above > 1.0
        assert p0_below < 1.0


class TestPredictHalflife:
    def test_indefinite_when_p0_above_1(self):
        assert predict_halflife(1.5, 0.01) is None

    def test_finite_when_p0_below_1(self):
        hl = predict_halflife(0.5, 0.01)
        assert hl is not None
        assert hl > 0

    def test_shorter_with_higher_decay(self):
        hl1 = predict_halflife(0.5, 0.01)
        hl2 = predict_halflife(0.5, 0.1)
        assert hl2 < hl1


class TestPredictTrace:
    def test_constant_when_p0_above_1(self):
        trace = predict_persistence_trace(1.5, 0.5, 100, 0.01)
        assert all(v == 0.5 for v in trace)

    def test_decays_when_p0_below_1(self):
        trace = predict_persistence_trace(0.5, 0.5, 100, 0.01)
        assert trace[-1] < trace[0]

    def test_monotonic_decay(self):
        trace = predict_persistence_trace(0.3, 0.8, 200, 0.02)
        for i in range(len(trace) - 1):
            assert trace[i] >= trace[i + 1]


class TestFitModel:
    def test_constant_trace(self):
        trace = [0.5] * 100
        a, b, c = fit_persistence_model(trace)
        assert c == pytest.approx(0.5, abs=0.1)

    def test_decaying_trace(self):
        trace = [0.8 * math.exp(-0.02 * t) + 0.1 for t in range(200)]
        a, b, c = fit_persistence_model(trace)
        assert a > 0
        assert b > 0
        assert c == pytest.approx(0.1, abs=0.05)


class TestComputeBound:
    def test_flat_vector_very_high_p0(self):
        bound = compute_persistence_bound(
            "flat_vector", n_poison=25, n_total=500,
            similarity=0.85, k=5,
        )
        # flat_vector uses epsilon decay (1e-10), so P0 is very large but not inf
        assert bound.p0 > 1e6
        assert bound.predicted_halflife is None
        assert bound.persistence_probability_1000 == 1.0

    def test_episodic_finite_p0(self):
        bound = compute_persistence_bound(
            "episodic", n_poison=25, n_total=500,
            similarity=0.85, k=5, decay_rate=0.99,
        )
        assert np.isfinite(bound.p0)
        assert bound.effective_decay_rate > 0

    def test_recency_capacity_matters(self):
        b1 = compute_persistence_bound(
            "recency", n_poison=25, n_total=500,
            similarity=0.85, k=5, capacity=100,
        )
        b2 = compute_persistence_bound(
            "recency", n_poison=25, n_total=500,
            similarity=0.85, k=5, capacity=1000,
        )
        # Larger capacity = lower eviction rate = higher P0
        assert b2.p0 > b1.p0
