"""memory-poison-scorer: Persistence risk assessment for memory-augmented LLM agents.

Usage:
    from memory_poison_scorer import PersistenceScorer

    scorer = PersistenceScorer()
    result = scorer.assess({
        "architecture": "episodic",
        "decay_rate": 0.995,
        "similarity_threshold": 0.0,
        "memory_size": 1000,
        "retrieval_k": 5,
    })

    print(f"Persistence risk: {result.risk_score:.2f}")
    print(f"Predicted half-life: {result.predicted_halflife}")
    print(f"P0: {result.p0:.2f}")
"""

from memory_poison_scorer.scorer import PersistenceScorer, ScorerResult

__all__ = ["PersistenceScorer", "ScorerResult"]
__version__ = "0.1.0"
