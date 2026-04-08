"""Formal persistence bound model — the P0 framework.

Implements the core theoretical contribution: persistence as a computable
function of architecture parameters, with an epidemiological analog (P0)
that predicts whether poisoned memories persist or decay.

P0 = retrieval_probability / effective_decay_rate

- P0 > 1: poisoned memories persist (retrieved faster than they decay)
- P0 < 1: poisoned memories decay (decay outpaces retrieval reinforcement)
- P0 = 1: critical threshold (marginal persistence)

The model maps from the SIR epidemiological framework:
- Transmission rate (beta) → retrieval probability of poisoned memory
- Recovery rate (gamma) → effective decay rate
- R0 = beta/gamma → P0 = retrieval_prob / decay_rate
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import curve_fit


@dataclass
class PersistenceBound:
    """Computed persistence bound for an architecture configuration."""
    p0: float  # persistence number
    predicted_halflife: float | None  # None = indefinite
    persistence_probability_1000: float  # P(persist > 1000 steps)
    retrieval_probability: float
    effective_decay_rate: float
    architecture_type: str
    parameters: dict[str, Any]


def estimate_retrieval_probability(
    n_poison: int,
    n_total: int,
    similarity: float,
    k: int,
    similarity_threshold: float = 0.0,
) -> float:
    """Estimate probability that a poisoned memory appears in top-k retrieval.

    For flat vector stores: approximate as the fraction of poisoned memories
    that exceed the similarity threshold, weighted by their relative similarity.

    For a poison memory with similarity `s` to the query, in a store of `n_total`
    memories where random memories have expected similarity ~0 (high-dimensional),
    the probability of being in top-k is approximately:

    P(retrieved) ≈ min(1, k * n_poison / n_total) when s >> random similarity

    This is a simplification. The actual probability depends on the full
    similarity distribution, but in high dimensions (d >= 32), random vectors
    have near-zero cosine similarity, so poison memories with s > 0.5 dominate.
    """
    if n_total == 0 or n_poison == 0:
        return 0.0

    if similarity < similarity_threshold:
        return 0.0

    # In high dimensions, random vectors have near-zero similarity
    # Poisoned memories with controlled similarity dominate retrieval
    base_prob = min(1.0, k * n_poison / n_total)

    # Adjust for similarity threshold (memories below threshold are filtered)
    # Higher threshold = fewer random memories compete = higher poison retrieval prob
    threshold_boost = 1.0 + similarity_threshold  # rough approximation
    return min(1.0, base_prob * threshold_boost)


def estimate_effective_decay(
    decay_rate: float,
    arch_type: str,
    consolidation_prob: float = 0.0,
) -> float:
    """Estimate effective per-step decay rate for an architecture.

    For flat vector stores: 0 (no decay)
    For episodic memory: 1 - decay_rate (per-step probability of becoming irrelevant)
    For multi-layer: weighted by consolidation probability
      - If consolidated into semantic: 0 decay (persists indefinitely)
      - If still episodic: 1 - decay_rate
      - Effective = (1 - consolidation_prob) * (1 - decay_rate)
    For recency: 1/capacity (eviction probability per step)
    """
    if arch_type == "flat_vector":
        return 1e-10  # effectively zero — memories persist indefinitely

    elif arch_type == "episodic":
        return 1.0 - decay_rate

    elif arch_type == "multi_layer":
        episodic_decay = 1.0 - decay_rate
        # Consolidation reduces effective decay
        return (1.0 - consolidation_prob) * episodic_decay

    elif arch_type == "recency":
        # Not directly decay-based, but we can model eviction probability
        # This is set by the caller based on capacity and insertion rate
        return decay_rate  # repurposed: caller passes eviction_prob

    else:
        return 1.0 - decay_rate  # default


def compute_p0(retrieval_probability: float, effective_decay: float) -> float:
    """Compute the persistence number P0.

    P0 = retrieval_probability / effective_decay

    Analogous to R0 in epidemiology:
    - P0 > 1: poison persists (retrieval reinforcement > decay)
    - P0 < 1: poison decays (decay > retrieval reinforcement)
    """
    if effective_decay < 1e-10:
        return float("inf") if retrieval_probability > 0 else 0.0
    return retrieval_probability / effective_decay


def predict_persistence_trace(
    p0: float,
    initial_fraction: float,
    n_steps: int,
    effective_decay: float,
) -> list[float]:
    """Predict persistence trace from P0 model.

    Simple exponential model:
    P(t) = initial_fraction * exp(-effective_decay * (1 - min(p0, 1)) * t)

    When P0 >= 1: persistence is constant (no net decay)
    When P0 < 1: exponential decay with rate proportional to (1 - P0)
    """
    trace = []
    for t in range(n_steps):
        if p0 >= 1.0:
            # Persist indefinitely
            trace.append(initial_fraction)
        else:
            net_decay = effective_decay * (1.0 - p0)
            trace.append(initial_fraction * np.exp(-net_decay * t))
    return trace


def predict_halflife(p0: float, effective_decay: float) -> float | None:
    """Predict half-life from P0 model.

    halflife = ln(2) / (effective_decay * (1 - P0))

    Returns None if P0 >= 1 (indefinite persistence).
    """
    if p0 >= 1.0:
        return None  # indefinite

    net_decay = effective_decay * (1.0 - p0)
    if net_decay < 1e-10:
        return None  # effectively indefinite

    return np.log(2) / net_decay


def fit_persistence_model(
    observed_trace: list[float],
) -> tuple[float, float, float]:
    """Fit exponential decay model to observed persistence trace.

    Fits: P(t) = a * exp(-b * t) + c

    Returns (amplitude, decay_constant, offset).
    Offset captures any persistent baseline (consolidated memories).
    """
    t = np.arange(len(observed_trace))
    y = np.array(observed_trace)

    if len(y) < 3 or np.all(y == y[0]):
        # Not enough data or constant trace
        return (y[0] if len(y) > 0 else 0.0, 0.0, y[-1] if len(y) > 0 else 0.0)

    try:
        # Initial guesses
        a0 = y[0] - y[-1]
        b0 = 0.01
        c0 = y[-1]

        def exp_decay(t, a, b, c):
            return a * np.exp(-b * t) + c

        popt, _ = curve_fit(
            exp_decay, t, y,
            p0=[a0, b0, c0],
            bounds=([0, 0, 0], [1, 1, 1]),
            maxfev=5000,
        )
        return tuple(popt)
    except (RuntimeError, ValueError):
        # Curve fit failed — return simple estimates
        return (y[0] - y[-1], 0.0, y[-1])


def compute_persistence_bound(
    arch_type: str,
    n_poison: int,
    n_total: int,
    similarity: float,
    k: int,
    decay_rate: float = 0.995,
    similarity_threshold: float = 0.0,
    capacity: int = 100,
    consolidation_prob: float = 0.0,
) -> PersistenceBound:
    """Compute full persistence bound for an architecture configuration.

    This is the main entry point for the formal model.
    """
    retrieval_prob = estimate_retrieval_probability(
        n_poison, n_total, similarity, k, similarity_threshold
    )

    if arch_type == "recency":
        # For recency, effective_decay is eviction probability
        # Approximation: each new memory has 1/capacity chance of evicting poison
        effective_decay = 1.0 / capacity
    else:
        effective_decay = estimate_effective_decay(
            decay_rate, arch_type, consolidation_prob
        )

    p0 = compute_p0(retrieval_prob, effective_decay)
    halflife = predict_halflife(p0, effective_decay)

    # Persistence probability at 1000 steps
    if p0 >= 1.0:
        persistence_1000 = 1.0
    else:
        net_decay = effective_decay * (1.0 - p0)
        persistence_1000 = float(np.exp(-net_decay * 1000))

    return PersistenceBound(
        p0=p0,
        predicted_halflife=halflife,
        persistence_probability_1000=persistence_1000,
        retrieval_probability=retrieval_prob,
        effective_decay_rate=effective_decay,
        architecture_type=arch_type,
        parameters={
            "n_poison": n_poison,
            "n_total": n_total,
            "similarity": similarity,
            "k": k,
            "decay_rate": decay_rate,
            "similarity_threshold": similarity_threshold,
            "capacity": capacity,
            "consolidation_prob": consolidation_prob,
        },
    )
