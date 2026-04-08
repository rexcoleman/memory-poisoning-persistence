"""Poisoning injection and persistence measurement.

Implements:
- MINJA-style memory injection (query-only, crafted embeddings)
- Persistence measurement over time (retrieval probability of poisoned memories)
- Half-life computation for poisoned memory decay
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.memory_architectures import Memory, MemoryArchitecture, cosine_similarity


@dataclass
class PoisonConfig:
    """Configuration for a poisoning attack."""
    poison_rate: float = 0.05  # fraction of memories that are poisoned
    poison_similarity: float = 0.85  # cosine similarity of poison to target queries
    embedding_dim: int = 64


def generate_clean_memories(
    n: int,
    embedding_dim: int,
    rng: np.random.Generator,
) -> list[Memory]:
    """Generate n clean (non-poisoned) memories with random embeddings."""
    memories = []
    for i in range(n):
        emb = rng.standard_normal(embedding_dim)
        emb = emb / np.linalg.norm(emb)
        memories.append(Memory(
            embedding=emb,
            content=f"clean_memory_{i}",
            is_poisoned=False,
        ))
    return memories


def generate_poisoned_memories(
    n: int,
    target_query: np.ndarray,
    similarity: float,
    embedding_dim: int,
    rng: np.random.Generator,
) -> list[Memory]:
    """Generate n poisoned memories with controlled similarity to target query.

    Creates embeddings that have approximately `similarity` cosine similarity
    to the target query embedding. This models MINJA-style attacks where
    the attacker crafts memories to be retrieved for specific queries.
    """
    memories = []
    target_norm = target_query / np.linalg.norm(target_query)
    for i in range(n):
        # Generate embedding with controlled similarity to target
        noise = rng.standard_normal(embedding_dim)
        noise = noise / np.linalg.norm(noise)
        # Blend target direction with random noise to achieve desired similarity
        emb = similarity * target_norm + math.sqrt(1 - similarity**2) * noise
        emb = emb / np.linalg.norm(emb)
        memories.append(Memory(
            embedding=emb,
            content=f"poisoned_memory_{i}",
            is_poisoned=True,
        ))
    return memories


import math


def inject_poison(
    arch: MemoryArchitecture,
    n_clean: int,
    n_poison: int,
    target_query: np.ndarray,
    poison_similarity: float,
    embedding_dim: int,
    rng: np.random.Generator,
) -> None:
    """Inject clean and poisoned memories into an architecture.

    Interleaves clean and poisoned memories to simulate realistic injection
    (attacker can't control injection order in query-only attacks).
    """
    clean = generate_clean_memories(n_clean, embedding_dim, rng)
    poisoned = generate_poisoned_memories(
        n_poison, target_query, poison_similarity, embedding_dim, rng
    )

    # Interleave: insert poisoned memories at random positions
    all_memories = clean + poisoned
    indices = list(range(len(all_memories)))
    rng.shuffle(indices)
    for idx in indices:
        arch.add(all_memories[idx])
        arch.step()


def measure_persistence(
    arch: MemoryArchitecture,
    target_query: np.ndarray,
    k: int,
    n_steps: int,
    queries_per_step: int = 1,
    rng: np.random.Generator | None = None,
    embedding_dim: int = 64,
) -> list[float]:
    """Measure poisoned memory retrieval probability over time.

    At each step:
    1. Issue `queries_per_step` queries (mix of target and random)
    2. Record fraction of retrieved memories that are poisoned
    3. Advance the architecture one step (applies decay, eviction, etc.)

    Returns a list of persistence values (one per step).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    persistence_trace = []

    for step in range(n_steps):
        # Query with target embedding
        retrieved = arch.retrieve(target_query, k)
        if len(retrieved) > 0:
            poison_fraction = sum(1 for m in retrieved if m.is_poisoned) / len(retrieved)
        else:
            poison_fraction = 0.0

        # Also issue random queries (simulates normal agent usage)
        for _ in range(queries_per_step - 1):
            random_query = rng.standard_normal(embedding_dim)
            random_query = random_query / np.linalg.norm(random_query)
            arch.retrieve(random_query, k)

        persistence_trace.append(poison_fraction)
        arch.step()

    return persistence_trace


def compute_halflife(persistence_trace: list[float], initial_threshold: float = 0.5) -> float | None:
    """Compute the half-life of poisoned memory persistence.

    Half-life = number of steps until persistence drops to half of initial value.
    Returns None if persistence never drops below half (indefinite persistence).
    """
    if len(persistence_trace) == 0:
        return None

    initial = persistence_trace[0]
    if initial <= 0:
        return 0.0

    target = initial * initial_threshold
    for i, p in enumerate(persistence_trace):
        if p <= target:
            return float(i)

    return None  # Never decayed to half — indefinite persistence
