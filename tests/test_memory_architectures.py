"""Tests for src/memory_architectures.py — covers all 4 architecture types."""

import numpy as np
import pytest

from src.memory_architectures import (
    EpisodicMemory,
    FlatVectorStore,
    Memory,
    MultiLayerMemory,
    RecencyMemory,
    cosine_similarity,
    create_architecture,
)


def _make_embedding(dim: int = 64, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(dim)
    return v / np.linalg.norm(v)


class TestCosinesimilarity:
    def test_identical_vectors(self):
        v = _make_embedding()
        assert cosine_similarity(v, v) == pytest.approx(1.0, abs=1e-7)

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert cosine_similarity(v1, v2) == pytest.approx(0.0, abs=1e-7)

    def test_zero_vector(self):
        v = _make_embedding()
        zero = np.zeros_like(v)
        assert cosine_similarity(v, zero) == 0.0


class TestFlatVectorStore:
    def test_add_and_retrieve(self):
        store = FlatVectorStore()
        emb = _make_embedding()
        store.add(Memory(embedding=emb, content="test"))
        results = store.retrieve(emb, k=1)
        assert len(results) == 1
        assert results[0].content == "test"

    def test_top_k_ordering(self):
        store = FlatVectorStore()
        query = _make_embedding(seed=0)
        # Add similar and dissimilar memories
        store.add(Memory(embedding=query.copy(), content="closest"))
        store.add(Memory(embedding=_make_embedding(seed=99), content="far"))
        results = store.retrieve(query, k=1)
        assert results[0].content == "closest"

    def test_no_decay(self):
        store = FlatVectorStore()
        emb = _make_embedding()
        store.add(Memory(embedding=emb, content="test"))
        for _ in range(1000):
            store.step()
        results = store.retrieve(emb, k=1)
        assert len(results) == 1

    def test_similarity_threshold(self):
        store = FlatVectorStore(similarity_threshold=0.99)
        query = _make_embedding(seed=0)
        store.add(Memory(embedding=_make_embedding(seed=99), content="dissimilar"))
        results = store.retrieve(query, k=5)
        # Dissimilar memory should be filtered
        assert len(results) == 0


class TestEpisodicMemory:
    def test_decay_reduces_retrieval(self):
        mem = EpisodicMemory(decay_rate=0.9, eviction_threshold=0.01)
        emb = _make_embedding()
        mem.add(Memory(embedding=emb, content="test"))
        # Before decay
        r1 = mem.retrieve(emb, k=1)
        assert len(r1) == 1
        # After many steps, memory should be evicted
        for _ in range(100):
            mem.step()
        r2 = mem.retrieve(emb, k=1)
        assert len(r2) == 0

    def test_fast_decay_evicts_quickly(self):
        mem = EpisodicMemory(decay_rate=0.5, eviction_threshold=0.1)
        emb = _make_embedding()
        mem.add(Memory(embedding=emb, content="test"))
        for _ in range(10):
            mem.step()
        assert len(mem.get_memories()) == 0

    def test_slow_decay_persists(self):
        mem = EpisodicMemory(decay_rate=0.999, eviction_threshold=0.01)
        emb = _make_embedding()
        mem.add(Memory(embedding=emb, content="test"))
        for _ in range(100):
            mem.step()
        assert len(mem.get_memories()) == 1


class TestMultiLayerMemory:
    def test_working_to_episodic_overflow(self):
        mem = MultiLayerMemory(working_capacity=2)
        for i in range(5):
            mem.add(Memory(embedding=_make_embedding(seed=i), content=f"m{i}"))
        assert len(mem.working) == 2
        assert len(mem.episodic) == 3

    def test_consolidation_promotes_to_semantic(self):
        mem = MultiLayerMemory(
            working_capacity=2,
            consolidation_interval=5,
            consolidation_threshold=2,
            decay_rate=0.999,
        )
        emb = _make_embedding()
        mem.add(Memory(embedding=emb, content="test"))
        # Push to episodic
        for i in range(3):
            mem.add(Memory(embedding=_make_embedding(seed=i+10), content=f"filler{i}"))
        # Retrieve enough times to meet consolidation threshold
        for _ in range(3):
            mem.retrieve(emb, k=5)
        # Trigger consolidation
        mem.current_step = 4
        mem.step()  # step 5 = consolidation interval
        assert any(m.layer == "semantic" and m.content == "test" for m in mem.semantic)

    def test_semantic_no_decay(self):
        mem = MultiLayerMemory(
            working_capacity=2,
            consolidation_interval=5,
            consolidation_threshold=1,
            decay_rate=0.5,  # fast decay for episodic
        )
        emb = _make_embedding()
        mem.add(Memory(embedding=emb, content="promoted"))
        # Push to episodic
        for i in range(3):
            mem.add(Memory(embedding=_make_embedding(seed=i+10), content=f"f{i}"))
        # Retrieve to promote
        mem.retrieve(emb, k=5)
        mem.current_step = 4
        mem.step()
        # Now run many steps — semantic should persist
        for _ in range(500):
            mem.step()
        semantic_contents = [m.content for m in mem.semantic]
        assert "promoted" in semantic_contents


class TestRecencyMemory:
    def test_fifo_eviction(self):
        mem = RecencyMemory(capacity=3)
        for i in range(5):
            mem.add(Memory(embedding=_make_embedding(seed=i), content=f"m{i}"))
        assert len(mem.get_memories()) == 3
        contents = [m.content for m in mem.get_memories()]
        assert "m0" not in contents
        assert "m4" in contents

    def test_recency_retrieval(self):
        mem = RecencyMemory(capacity=10)
        for i in range(5):
            mem.add(Memory(embedding=_make_embedding(seed=i), content=f"m{i}"))
        results = mem.retrieve(_make_embedding(), k=2)
        assert results[0].content == "m4"  # most recent first
        assert results[1].content == "m3"


class TestFactory:
    def test_all_types(self):
        for t in ["flat_vector", "episodic", "multi_layer", "recency"]:
            arch = create_architecture(t)
            assert arch is not None

    def test_unknown_type(self):
        with pytest.raises(ValueError):
            create_architecture("unknown")
