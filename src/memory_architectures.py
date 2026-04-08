"""Memory architecture simulations for persistence bound experiments.

Implements 4 structurally diverse memory architectures:
1. FlatVectorStore — cosine similarity retrieval, no decay
2. EpisodicMemory — cosine retrieval + exponential temporal decay
3. MultiLayerMemory — working + episodic + semantic with consolidation
4. RecencyMemory — recency-weighted retrieval, no embedding similarity

Each architecture stores memories as (embedding, content, metadata) tuples
and exposes a common interface: add(), retrieve(), step(), get_state().
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class Memory:
    """A single memory entry."""
    embedding: np.ndarray
    content: str
    is_poisoned: bool = False
    timestamp: int = 0
    retrieval_count: int = 0
    layer: str = "episodic"  # episodic | semantic | working


class MemoryArchitecture(Protocol):
    """Common interface for all memory architectures."""

    def add(self, memory: Memory) -> None: ...
    def retrieve(self, query_embedding: np.ndarray, k: int) -> list[Memory]: ...
    def step(self) -> None: ...
    def get_memories(self) -> list[Memory]: ...


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


@dataclass
class FlatVectorStore:
    """Architecture 1: Flat vector store with cosine similarity, no decay.

    Simplest architecture. Memories persist indefinitely.
    Retrieval is pure cosine similarity — top-k nearest neighbors.
    """
    memories: list[Memory] = field(default_factory=list)
    similarity_threshold: float = 0.0
    current_step: int = 0

    def add(self, memory: Memory) -> None:
        memory.timestamp = self.current_step
        self.memories.append(memory)

    def retrieve(self, query_embedding: np.ndarray, k: int) -> list[Memory]:
        scored = []
        for m in self.memories:
            sim = cosine_similarity(query_embedding, m.embedding)
            if sim >= self.similarity_threshold:
                scored.append((sim, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in scored[:k]]
        for m in results:
            m.retrieval_count += 1
        return results

    def step(self) -> None:
        self.current_step += 1

    def get_memories(self) -> list[Memory]:
        return list(self.memories)


@dataclass
class EpisodicMemory:
    """Architecture 2: Episodic memory with exponential temporal decay.

    Retrieval score = cosine_similarity * decay_factor^(age).
    Memories whose effective score drops below eviction_threshold are removed.
    """
    memories: list[Memory] = field(default_factory=list)
    decay_rate: float = 0.995  # per-step decay factor (from MemoryBank)
    similarity_threshold: float = 0.0
    eviction_threshold: float = 0.01
    current_step: int = 0

    def add(self, memory: Memory) -> None:
        memory.timestamp = self.current_step
        self.memories.append(memory)

    def _effective_score(self, memory: Memory, query_embedding: np.ndarray) -> float:
        sim = cosine_similarity(query_embedding, memory.embedding)
        age = self.current_step - memory.timestamp
        decay = self.decay_rate ** age
        return sim * decay

    def retrieve(self, query_embedding: np.ndarray, k: int) -> list[Memory]:
        scored = []
        for m in self.memories:
            eff = self._effective_score(m, query_embedding)
            if eff >= self.similarity_threshold:
                scored.append((eff, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in scored[:k]]
        for m in results:
            m.retrieval_count += 1
        return results

    def step(self) -> None:
        self.current_step += 1
        # Evict memories that have decayed below threshold
        surviving = []
        # Use a neutral query to check raw decay (embedding norm doesn't matter for eviction)
        for m in self.memories:
            age = self.current_step - m.timestamp
            decay = self.decay_rate ** age
            if decay >= self.eviction_threshold:
                surviving.append(m)
        self.memories = surviving

    def get_memories(self) -> list[Memory]:
        return list(self.memories)


@dataclass
class MultiLayerMemory:
    """Architecture 3: Multi-layer memory with consolidation.

    Three layers: working (recent, bounded), episodic (medium-term, decaying),
    semantic (long-term, consolidated from episodic).

    Consolidation: every `consolidation_interval` steps, episodic memories
    that have been retrieved >= `consolidation_threshold` times are promoted
    to semantic layer (no decay). This models how frequently-accessed memories
    become "knowledge."

    Key insight for poisoning: if a poisoned episodic memory gets retrieved
    enough times, it consolidates into semantic memory and persists indefinitely.
    """
    working: list[Memory] = field(default_factory=list)
    episodic: list[Memory] = field(default_factory=list)
    semantic: list[Memory] = field(default_factory=list)
    working_capacity: int = 10
    decay_rate: float = 0.995
    similarity_threshold: float = 0.0
    consolidation_interval: int = 50
    consolidation_threshold: int = 3  # retrievals needed for promotion
    eviction_threshold: float = 0.01
    current_step: int = 0

    def add(self, memory: Memory) -> None:
        memory.timestamp = self.current_step
        memory.layer = "working"
        self.working.append(memory)
        # Overflow: push oldest working memories to episodic
        while len(self.working) > self.working_capacity:
            evicted = self.working.pop(0)
            evicted.layer = "episodic"
            self.episodic.append(evicted)

    def retrieve(self, query_embedding: np.ndarray, k: int) -> list[Memory]:
        scored = []
        # Semantic memories: no decay, full similarity
        for m in self.semantic:
            sim = cosine_similarity(query_embedding, m.embedding)
            if sim >= self.similarity_threshold:
                scored.append((sim * 1.1, m))  # slight boost for semantic

        # Episodic memories: with decay
        for m in self.episodic:
            sim = cosine_similarity(query_embedding, m.embedding)
            age = self.current_step - m.timestamp
            decay = self.decay_rate ** age
            eff = sim * decay
            if eff >= self.similarity_threshold:
                scored.append((eff, m))

        # Working memories: no decay, full similarity
        for m in self.working:
            sim = cosine_similarity(query_embedding, m.embedding)
            if sim >= self.similarity_threshold:
                scored.append((sim, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in scored[:k]]
        for m in results:
            m.retrieval_count += 1
        return results

    def step(self) -> None:
        self.current_step += 1

        # Consolidation check
        if self.current_step % self.consolidation_interval == 0:
            promoted = []
            remaining = []
            for m in self.episodic:
                if m.retrieval_count >= self.consolidation_threshold:
                    m.layer = "semantic"
                    promoted.append(m)
                else:
                    remaining.append(m)
            self.semantic.extend(promoted)
            self.episodic = remaining

        # Evict decayed episodic memories
        surviving = []
        for m in self.episodic:
            age = self.current_step - m.timestamp
            decay = self.decay_rate ** age
            if decay >= self.eviction_threshold:
                surviving.append(m)
        self.episodic = surviving

    def get_memories(self) -> list[Memory]:
        return list(self.working) + list(self.episodic) + list(self.semantic)


@dataclass
class RecencyMemory:
    """Architecture 4: Recency-weighted retrieval, no embedding similarity.

    Retrieval is purely based on recency — most recent memories first.
    No semantic matching. Models architectures like simple chat history
    or FIFO buffers.

    Poisoned memories persist until pushed out by newer entries.
    Persistence = f(memory_capacity, insertion_rate).
    """
    memories: list[Memory] = field(default_factory=list)
    capacity: int = 100
    current_step: int = 0

    def add(self, memory: Memory) -> None:
        memory.timestamp = self.current_step
        self.memories.append(memory)
        # Evict oldest if over capacity
        while len(self.memories) > self.capacity:
            self.memories.pop(0)

    def retrieve(self, query_embedding: np.ndarray, k: int) -> list[Memory]:
        # Return k most recent memories (ignore query embedding)
        results = list(reversed(self.memories[-k:]))
        for m in results:
            m.retrieval_count += 1
        return results

    def step(self) -> None:
        self.current_step += 1

    def get_memories(self) -> list[Memory]:
        return list(self.memories)


def create_architecture(
    arch_type: str,
    similarity_threshold: float = 0.0,
    decay_rate: float = 0.995,
    capacity: int = 100,
    consolidation_interval: int = 50,
    consolidation_threshold: int = 3,
) -> MemoryArchitecture:
    """Factory for creating memory architectures by name."""
    if arch_type == "flat_vector":
        return FlatVectorStore(similarity_threshold=similarity_threshold)
    elif arch_type == "episodic":
        return EpisodicMemory(
            decay_rate=decay_rate,
            similarity_threshold=similarity_threshold,
        )
    elif arch_type == "multi_layer":
        return MultiLayerMemory(
            decay_rate=decay_rate,
            similarity_threshold=similarity_threshold,
            consolidation_interval=consolidation_interval,
            consolidation_threshold=consolidation_threshold,
        )
    elif arch_type == "recency":
        return RecencyMemory(capacity=capacity)
    else:
        raise ValueError(f"Unknown architecture type: {arch_type}")
