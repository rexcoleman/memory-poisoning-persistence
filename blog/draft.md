---
title: "Your Memory Architecture Is Your Security Posture: Persistence Bounds for Agent Memory Poisoning"
date: 2026-04-08
author: Rex Coleman
tags: ["ai-security", "llm-agents", "memory-poisoning", "persistence-bounds"]
categories: ["Security OF AI"]
---

# Your Memory Architecture Is Your Security Posture: Persistence Bounds for Agent Memory Poisoning

Memory poisoning is the sleeper threat in LLM agents. An attacker injects a malicious memory through a single interaction, and that memory surfaces again and again — steering the agent toward unsafe behavior every time a related query appears. MemoryGraft, MINJA, AgentPoison, and other attacks have demonstrated injection success rates above 90%. OWASP's ASI06 now lists memory poisoning as a top agentic AI risk for 2026.

But here's the question nobody was asking: **how long does the poison last?**

The attack papers tell you *how* to inject. They don't tell you whether the poisoned memory will still be there after 100 interactions, or 1,000, or forever. And that matters enormously for defenders, because the answer depends almost entirely on one thing: your memory architecture configuration.

## The Setup: Four Architectures, One Attack

We simulated four structurally different memory architectures, all subjected to the same MINJA-style poisoning attack (5% poison rate, 0.85 embedding similarity to target queries):

1. **Flat vector store** — cosine similarity retrieval, no decay. This is what most RAG systems use.
2. **Episodic memory with decay** — retrieval score decays exponentially over time. Similar to MemoryBank's Ebbinghaus forgetting curve.
3. **Multi-layer memory** — working + episodic + semantic layers with consolidation. Frequently-retrieved episodic memories promote to permanent semantic storage.
4. **Recency-weighted memory** — most recent memories retrieved first, oldest evicted. A simple FIFO buffer.

Each experiment ran for 500 interaction steps across 5 random seeds. We measured the *persistence* of poisoned memories: what fraction of retrieved results are poisoned at each timestep?

## Finding 1: Architecture Determines Persistence — Not the Attack

The same attack produces wildly different outcomes depending on architecture:

- **Flat vector store:** Indefinite persistence. Every seed, every run. The poison never leaves.
- **Episodic (decay=0.99):** Half-life of 380 steps (±21.5 std). The poison fades, but slowly.
- **Episodic (decay=0.9):** Half-life of 13 steps (±11.8 std). The poison is gone in minutes.
- **Recency:** Half-life of 0 steps. The poison is immediately displaced by new memories.

That is a **28x difference** in persistence half-life between decay rates of 0.99 and 0.9 within the *same architecture*. And the gap between flat vector stores (infinite) and fast-decaying episodic memory (13 steps) is not even measurable on the same scale.

This is the core finding: the attack vector matters less than the architecture. The same injection that creates permanent compromise in a flat vector store is a minor, self-healing blip in a properly configured episodic memory.

![Phase transition in persistence](../figures/fig1_p0_phase_transition.png)
*Figure 1: Sharp phase transition between decaying and indefinite persistence regimes at decay_rate ≈ 0.9925.*

## Finding 2: The 40x Defense You Already Have

We swept four parameters to determine which matters most for persistence:

| Parameter | R² (variance explained) |
|-----------|------------------------|
| Similarity threshold | **0.92** |
| Decay rate | 0.85 |
| Poison similarity | 0.00* |
| Context window (k) | 0.00* |

*\*Ceiling effect — see limitations below.*

The **embedding similarity threshold** — the minimum cosine similarity required for a memory to appear in retrieval results — explains 92% of the variance in persistence half-life. Increasing the threshold from 0.0 (default in most systems) to 0.7 reduces persistence half-life from 500+ steps to just 12.4 steps. That is a **40x reduction** from a single configuration change.

Most memory systems ship with a similarity threshold of 0.0, meaning every memory with any positive similarity can be retrieved. This is a security-relevant default. Raising the threshold to 0.5 or above dramatically reduces the window during which poisoned memories influence agent behavior.

![Parameter importance](../figures/fig2_parameter_importance.png)
*Figure 2: Embedding similarity threshold dominates persistence variance.*

![Similarity threshold sweep](../figures/fig3_similarity_threshold_sweep.png)
*Figure 3: Increasing the similarity threshold from 0.0 to 0.7 reduces persistence half-life by 40x.*

## Finding 3: The Phase Transition Practitioners Need to Know About

There is a sharp phase transition between "poison decays" and "poison persists indefinitely." The transition occurs at a decay rate of approximately 0.9925, with a width of only 0.005 decay-rate units.

What this means in practice:
- **decay_rate = 0.99**: Half-life of 380 steps. The poison fades within a workday of normal agent usage.
- **decay_rate = 0.995**: Indefinite persistence. The poison never fades. All 5 seeds, every run.

The difference between "self-healing in hours" and "permanently compromised" is a configuration change of 0.005. If you're building a memory system with decay, you need to know which side of this transition you're on.

We formalized this as the **persistence number P₀**, analogous to R₀ in epidemiology:

> P₀ = retrieval_probability / effective_decay_rate

When P₀ > 1, poisoned memories are retrieved faster than they decay — persistence is indefinite. When P₀ < 1, decay outpaces retrieval — the poison fades. The transition is sharp, not gradual.

## What Didn't Work: The SIR Model

We hypothesized that the epidemiological SIR (Susceptible-Infected-Recovered) framework would predict persistence rank ordering across architectures. It didn't. Spearman correlation between predicted P₀ and observed half-life was 0.304 — essentially random.

Why? Two reasons:

1. **Saturation.** At the default decay rate of 0.995, most architectures show indefinite persistence. You can't rank-order things that are all infinite.
2. **Eviction ≠ decay.** The recency architecture evicts memories by displacement (FIFO), not by decay. The SIR model assumes recovery through decay — it has no mechanism for "you got pushed out by something newer." The model predicted P₀ = 125 (high persistence) for recency, but observed half-life was 0 (immediate eviction).

This is a genuine limitation: the cross-domain transfer from epidemiology works for decay-based architectures but fundamentally breaks for eviction-based ones. A more general framework is needed.

## What We Couldn't Test

The consolidation amplification hypothesis (H-5) predicted that multi-layer memory would amplify persistence by promoting frequently-retrieved poisoned memories to the permanent semantic layer. We tested this at a decay rate of 0.995 — and both architectures showed indefinite persistence regardless. The test was non-discriminating. The hypothesis remains open. A proper test would use decay rates in the 0.95-0.99 range where episodic memories decay but consolidation might rescue them.

Two parameters (poison similarity and context window size) showed R² = 0.00 in our sweep, but this is a ceiling effect: at the default decay rate, everything persists, so no parameter variation is visible. These parameters likely matter at faster decay rates.

## Practical Recommendations

1. **Set your similarity threshold to >= 0.5.** This is the single highest-leverage defense. It reduces persistence half-life by 7x or more and is a configuration change, not a code change.

2. **Use a decay rate of 0.99 or faster.** This puts your architecture on the "self-healing" side of the phase transition. The default 0.995 rate used by many systems (derived from MemoryBank's Ebbinghaus curve) is above the transition — it provides almost no protection.

3. **Know your P₀.** If P₀ > 1, poisoned memories persist indefinitely in your architecture. Run the persistence scorer on your configuration to find out: `pip install -e .` from the repository, then `from memory_poison_scorer import PersistenceScorer`.

## The Tool

We released `memory-poison-scorer`, an open-source Python package that takes your memory architecture parameters and outputs:

- **Persistence risk score** (0.0 to 1.0)
- **Predicted half-life** of poisoned memories
- **P₀ number** — above 1 means indefinite persistence
- **Actionable recommendations** specific to your architecture type

```python
from memory_poison_scorer import PersistenceScorer

scorer = PersistenceScorer()
result = scorer.assess({
    "architecture": "episodic",
    "decay_rate": 0.995,
    "similarity_threshold": 0.0,
    "memory_size": 1000,
    "retrieval_k": 5,
})
print(f"Risk: {result.risk_level}")  # CRITICAL
print(f"P0: {result.p0:.1f}")        # 50.0
print(f"Half-life: {result.predicted_halflife}")  # None (indefinite)
```

Change `decay_rate` to 0.99 and `similarity_threshold` to 0.5 and watch the risk drop from CRITICAL to LOW.

## Limitations

All results are from simulated memory architectures with random embeddings, not real LLM agents. The phase transition location and quantitative half-lives are specific to our simulation parameters. Real-system validation against Mem0 or similar production architectures is the necessary next step. The qualitative findings — that architecture matters more than attack vector, that similarity threshold is the key control, that a sharp phase transition exists — are more likely to transfer than specific numbers.

## What's Next

The breakthrough question from this research: **are most deployed memory architectures above or below the phase transition?** A survey of default configurations in LangChain, Mem0, AutoGPT, and other frameworks would reveal whether the default memory landscape is inherently persistent to poisoning. If most defaults land above the transition, a simple configuration recommendation could protect the majority of deployed agents.

---

*Code and data: [memory-poisoning-persistence](https://github.com/rexcoleman/memory-poisoning-persistence)*

*Cite: See CITATION.cff in the repository.*
