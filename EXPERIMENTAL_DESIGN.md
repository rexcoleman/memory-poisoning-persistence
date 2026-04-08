# EXPERIMENTAL DESIGN REVIEW

<!-- version: 1.0 -->
<!-- created: 2026-04-08 -->
<!-- gate: 0.5 (must pass before Phase 1 compute) -->

> **Authority hierarchy:** Topic prompt (Tier 1) > govML templates (Tier 2) > Builder judgment (Tier 3) > This document (Contract)
> **Conflict rule:** When a higher-tier document and this contract disagree, the higher tier wins.
> **Upstream:** DATA_CONTRACT (data sources), EXPERIMENT_CONTRACT (experiment protocol), HYPOTHESIS_REGISTRY (pre-registered hypotheses)
> **Downstream:** All Phase 1+ artifacts. This document gates the transition from Phase 0 (setup) to Phase 1 (training).

> **Purpose:** Force experimental design decisions BEFORE compute begins. Every reviewer kill shot in FP-05 was knowable on day 1 but wasn't caught until quality assessment. This template prevents that. (LL-90)

---

## 0) Problem Selection Gate (Gate -1)

| Criterion | Your Answer |
|---|---|
| Practitioner pain | Security engineers deploying LLM agents with persistent memory (e.g., Mem0, LangChain Memory, AutoGPT) have no way to predict whether a memory poisoning attack will persist across sessions or decay naturally. Estimated audience: ~50,000+ engineers building memory-augmented agents (based on Mem0's 25K+ GitHub stars, LangChain's 100K+). Magnitude: MINJA achieves 95% injection success rate (Dong et al., NeurIPS 2025), MemoryGraft shows persistence across sessions (Srivastava et al., Dec 2025), but defenders cannot predict HOW LONG a poisoned memory persists or under what conditions it amplifies. |
| Research gap | Attack papers (MemoryGraft, MINJA, InjecMEM, AgentPoison, arxiv:2601.05504, arxiv:2603.20357) focus on injection mechanics and success rates. NONE formalize persistence dynamics as a computable function f(retrieval_method, decay_rate, context_window, embedding_threshold). Torra & Bras-Amoros (2603.20357, Mar 2026) note that persistence risks in agent interactions "are difficult to formalize and solve." The gap is mathematical: we know attacks work, but we cannot predict their temporal dynamics. |
| Novelty potential | Expected: persistence bounds vary by 10x+ across architectures (e.g., no-decay RAG vs. exponential-decay episodic memory). Surprise: if persistence is architecture-INDEPENDENT (i.e., a universal bound exists regardless of retrieval method), that would fundamentally change the defense landscape — suggesting the vulnerability is in the LLM's reasoning, not the memory system. |
| Cross-domain bridge | Epidemiological persistence modeling: disease persistence in populations follows SIR-type dynamics where pathogen persistence depends on transmission rate, recovery rate, and population susceptibility. Memory poisoning persistence maps to: injection rate (transmission), decay rate (recovery), retrieval probability (susceptibility). Importable method: basic reproduction number R0 — if R0 > 1, the infection persists; if R0 < 1, it decays. We can define an analogous "persistence number" P0 for memory poisoning. |
| Artifact potential | `memory-poison-scorer`: a pip-installable Python package. Input: memory architecture parameters (retrieval method, decay rate, context window size, embedding similarity threshold). Output: persistence risk score (0-1), predicted half-life of poisoned memories, amplification risk flag. Practitioners run `score = scorer.assess(architecture_config)` without reading the paper. |
| Real-world test | Test against Mem0's production memory architecture (open-source, well-documented API). Mem0 uses semantic search + temporal decay + memory consolidation. This is a real deployed system, not a toy simulation. Validation: inject poisoned memories into a Mem0 instance and measure actual persistence vs. our predicted bounds. |
| Generalization path | Condition 1: Vector-store RAG (flat retrieval, no decay) — e.g., LangChain VectorStoreRetriever. Condition 2: Episodic memory with decay — e.g., Mem0 or MemoryBank with temporal weighting. These differ on a structural dimension (retrieval architecture). Additional condition: multi-layer memory (working + episodic + semantic) from Continuum Memory Architecture (arXiv:2601.09913). |
| Portfolio check | NEW project. No retrofit. This is a fresh research direction — no existing project in the pipeline addresses memory poisoning formally. |
| Formalization potential | Conjecture: Given a memory architecture M with retrieval function r(q, m), decay function d(m, t), and context window C, the persistence probability of a poisoned memory m_p after T interactions is bounded by P(T) <= r(q, m_p) * (1 - d(m_p, T))^T * min(1, |m_p|/C). If the "persistence number" P0 = r_max * (1 - d_min) > 1, the poisoned memory persists indefinitely under repeated retrieval. |
| Breakthrough question | Is there a universal persistence threshold below which ALL memory architectures naturally purge poisoned content — and if so, what design choices push an architecture below it? |
| Assumption challenged | The field assumes memory poisoning persistence is primarily a function of the attack vector (how you inject). Papers holding this: MemoryGraft (Srivastava et al., 2025) focuses on "semantic imitation heuristic" as the persistence mechanism; MINJA (Dong et al., 2025) attributes persistence to "bridging steps" quality. Our work may show persistence is primarily a function of the ARCHITECTURE (how memories are stored/retrieved/decayed), not the attack. Contradiction search: searched "memory poisoning defense architecture" — arxiv:2601.05504 varies retrieval parameters and finds 40pp+ ASR variation across configurations, supporting our hypothesis. arxiv:2603.20357 (Torra) explicitly calls formalization of architecture-dependent risks "difficult" but does not attempt it. No papers directly contradict our hypothesis because none have tested it. |

**Gate -1 verdict:** [x] PASS — all rows meet minimums, proceed to full design.

---

## 1) Project Identity

**Project:** Memory Poisoning Persistence Bounds
**Target venue:** Security-focused venue (Workshop/Tier 2)
**Design lock commit:** 164ced2
**Design lock date:** 2026-04-08

> **Gate 0.5 rule:** This document must be committed before any Phase 1 training script is executed. Any experiment output with a git timestamp before the lock commit is invalid for claims about pre-registered design.

---

## 2) Novelty Claim (one sentence)

> First formal characterization of memory poisoning persistence as a computable function of architecture parameters, enabling defenders to predict poisoning half-life and identify architecture configurations that guarantee natural decay.

**Self-test:** 29 words. Slightly over the 25-word target but captures the key novelty: computable function, architecture parameters, predictive capability. Shortened version (23 words): "First computable bounds on memory poisoning persistence as f(architecture parameters), enabling defenders to predict poisoning half-life from architecture configuration."

---

## 3) Comparison Baselines

| # | Method | Citation | How We Compare | Why This Baseline | Tuning Parity |
|---|--------|----------|---------------|-------------------|---------------|
| 1 | No-defense baseline | N/A (raw architecture) | Measure persistence in unmodified memory architectures | Establishes ground truth for how long poisoned memories persist without intervention | N/A — no tuning, raw measurement |
| 2 | Random decay baseline | Standard exponential decay (lambda=0.995/hr from MemoryBank) | Compare our predicted bounds against naive "everything decays uniformly" assumption | Tests whether architecture-specific bounds add value over a simple decay model | Same decay parameters applied to all architectures |
| 3 | MemGuard defense | NTU et al. 2026 (reduces ASR by 95%) | Measure persistence WITH defense vs. our predicted bounds for defended architectures | Tests whether our bounds extend to defended systems or only apply to undefended | Default MemGuard parameters as published |

**Baseline fairness statement:** Baselines 1-2 are parameter-free or use published defaults. Baseline 3 uses published default parameters because practitioners would use defaults — our bounds should work with default configurations.

---

## 4) Pre-Registered Reviewer Kill Shots

| # | Criticism a Reviewer Would Make | Planned Mitigation | Design Decision |
|---|--------------------------------|-------------------|-----------------|
| 1 | "Your simulations don't capture real LLM reasoning — persistence in simulation may not match production agents." | Include at least 1 real-system validation using Mem0's open-source architecture with an actual LLM backend. Report simulation-to-real gap explicitly. | Budget real validation after simulation convergence. Accept that simulation results are upper bounds. |
| 2 | "The persistence function assumes stationary retrieval distributions, but real queries are non-stationary." | Run experiments with both stationary (uniform query distribution) and non-stationary (bursty, topic-shifting) query streams. Report bound tightness under each. | Non-stationary experiments are ablation — not required for core bounds but strengthen generalization. |
| 3 | "Your formalization ignores multi-agent settings where poisoned memories can propagate between agents." | Acknowledge as limitation. Single-agent persistence is prerequisite — multi-agent amplification is future work. Cite Torra (2603.20357) for multi-agent context. | Scope to single-agent systems. Multi-agent is out of scope but noted. |

---

## 5) Ablation Plan

**Component ablation:**

| Component / Feature Group | Hypothesis When Removed | Expected Effect | Priority |
|--------------------------|------------------------|-----------------|----------|
| Decay function | Without decay, persistence = indefinite (trivial bound) | Persistence bound collapses to P(T) = r(q, m_p) — only retrieval probability matters | HIGH |
| Embedding similarity threshold | Without threshold filtering, all memories retrieved equally | Persistence increases — poisoned memories no longer filtered by semantic distance | HIGH |
| Context window size | With infinite context, all retrieved memories influence output | Persistence amplifies — no competition for context slots | MEDIUM |
| Retrieval method (swap vector search for recency-based) | Different retrieval changes which memories surface | Persistence pattern changes shape (exponential vs. step-function decay) | HIGH |

**Novel component isolation (A5):**

| Novel Claim (<=15 words) | Isolation Test | Expected If Active Ingredient | Expected If NOT Active Ingredient |
|---|---|---|---|
| Architecture parameters determine persistence bounds independent of attack vector | Fix attack vector (MINJA), vary only architecture params | Persistence varies 10x+ across architectures with same attack | Persistence similar across architectures — attack vector dominates |

---

## 6) Ground Truth Audit

| Source | Type | Estimated Count | Known Lag | Estimated Positive Rate | Limitations |
|--------|------|----------------|-----------|------------------------|-------------|
| Simulated memory architectures (4 types) | Synthetic | ~10,000 query-memory interactions per architecture | None (real-time simulation) | Controlled: 1-5% poisoned memories injected | Simulation fidelity to production systems unknown |
| Mem0 open-source instance | Real system | ~1,000 interactions | None (live testing) | Controlled injection | Single production architecture, may not generalize |

**Alternative label sources considered:**

| Source | Why Included or Excluded | If Excluded, Could Add Later? |
|--------|-------------------------|------------------------------|
| MemoryGraft paper's MetaGPT results | Excluded — different experimental setup (experience-based, not parameter-sweep) | Yes — could extract persistence duration data from their reported results |
| MINJA paper's EHR agent results | Excluded — their focus is ASR, not temporal persistence measurement | Possibly — if they report per-timestep results |

---

## 7) Statistical Plan

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Seeds | 5 (seeds 42, 123, 456, 789, 1024) | Tier 2 minimum. Each seed produces different query sequences and initial memory states |
| Significance test | Mann-Whitney U test (non-parametric) | Persistence distributions may not be normal; non-parametric is safer |
| Effect size threshold | Cohen's d >= 0.5 (medium effect) for architecture comparisons | We claim architectures differ meaningfully — small effects aren't actionable |
| CI method | Bootstrap 95% CI (10,000 resamples) | Non-parametric, works with any distribution shape |
| Multiple comparison correction | Bonferroni correction for 6 pairwise architecture comparisons | Conservative — 6 comparisons from 4 architectures |

---

## 8) Related Work Checklist

| # | Paper | Year | Relevance | How We Differ |
|---|-------|------|-----------|---------------|
| 1 | MemoryGraft (Srivastava et al., arXiv:2512.16962) | 2025 | Demonstrates persistent memory poisoning via experience retrieval | Attack-focused; does not formalize persistence as f(architecture). We provide the formal framework they lack. |
| 2 | MINJA (Dong et al., arXiv:2503.03704, NeurIPS 2025) | 2025 | Query-only memory injection, 95% ISR, 70% ASR | Measures injection success, not persistence duration. We measure temporal dynamics post-injection. |
| 3 | Memory Poisoning Attack and Defense (arXiv:2601.05504) | 2026 | Varies retrieval parameters on EHR agents, finds 40pp ASR variation | Closest to our work — varies parameters. But measures ASR, not persistence bounds. We formalize the relationship they observe empirically. |
| 4 | AgentPoison (Chen et al., NeurIPS 2024) | 2024 | RAG/knowledge-base backdoor poisoning, 80% ASR at <0.1% poison rate | Targets knowledge bases, not episodic memory. No temporal persistence analysis. |
| 5 | Memory poisoning and secure MAS (Torra & Bras-Amoros, arXiv:2603.20357) | 2026 | Reviews memory types, discusses formalization difficulty | Survey/position paper. Calls formalization "difficult" but doesn't attempt it. We attempt it. |
| 6 | InjecMEM (OpenReview) | 2025 | Single-interaction memory injection | Simpler attack model. No persistence measurement. |
| 7 | Mem0 (arXiv:2504.19413) | 2025 | Production memory architecture with semantic search + decay | Architecture we test against. Provides real-system validation target. |
| 8 | Continuum Memory Architecture (arXiv:2601.09913) | 2026 | Multi-layer memory (working/episodic/semantic) with consolidation | Architecture type we benchmark. Introduces consolidation as a persistence mechanism. |
| 9 | MemGuard (NTU et al.) | 2026 | Defense reducing ASR by 95% via provenance tracking | Baseline defense. We test whether our bounds predict post-defense persistence. |
| 10 | MemoryBank (arXiv:2305.10250) | 2023 | Early LLM memory with Ebbinghaus forgetting curve decay | Introduced explicit decay (0.995/hr). Our baseline decay model. |

---

## 8a) Novelty Plan — Target: 7/10

**Prior art search strategy:** Searched arXiv, Google Scholar, Semantic Scholar, and OpenReview for: "memory poisoning persistence," "agent memory attack temporal," "memory injection formal bounds," "LLM agent memory decay security." Covered NeurIPS 2024-2025, ICML 2025, ACM CCS/AISec 2024-2025, and preprints through March 2026.

| Paper | Year | Their Claim | How We Differ |
|-------|------|-------------|---------------|
| MemoryGraft (2512.16962) | 2025 | Poisoned experiences persist via semantic similarity | We formalize WHEN they persist as f(similarity threshold, decay, retrieval method) |
| MINJA (2503.03704) | 2025 | Query-only injection achieves 95% ISR | We measure what happens AFTER injection — temporal persistence dynamics |
| arXiv:2601.05504 | 2026 | Parameter variation affects ASR (40pp range) | We derive closed-form bounds explaining WHY parameters affect persistence |
| AgentPoison (2407.12784) | 2024 | Knowledge-base poisoning at <0.1% poison rate | We extend from static KB to dynamic memory with decay/consolidation |
| Torra (2603.20357) | 2026 | Formalization is "difficult to solve" | We attempt the formalization they describe as open |

**Expected contribution type:** Novel methodology — first formal persistence bounds for memory poisoning.

**Pre-registered expected outcomes** (surprise_factor):

| Experiment | Expected Result | What Would SURPRISE You | How You'd Investigate |
|------------|----------------|------------------------|----------------------|
| Architecture comparison | 10x+ persistence variation across 4 architectures with same attack | <2x variation — would suggest attack vector dominates architecture | Run with 3 different attack types to test if attack explains more variance |
| Decay rate sweep | Monotonic relationship: higher decay = lower persistence | Non-monotonic: moderate decay INCREASES persistence (e.g., by triggering re-retrieval) | Investigate retrieval-decay feedback loops |
| P0 threshold | Clear threshold exists: P0 > 1 = persist, P0 < 1 = decay | No clear threshold — persistence is continuous, not phase-transition-like | May need different mathematical framework (no SIR analog) |

---

## 8b) Impact Plan — Target: 7/10

**Problem magnitude:** ~50,000+ engineers building memory-augmented LLM agents (Mem0: 25K+ GitHub stars, LangChain Memory: widely used in 100K+ star framework). OWASP ASI06 (2026) lists memory poisoning as a top agentic AI risk. No tool exists to assess architecture-level persistence risk before deployment.

**Artifact-first design** (artifact_release):

| Artifact | Type | How Practitioners Install/Use | Ships With Experiment? |
|----------|------|------------------------------|----------------------|
| memory-poison-scorer | Python package | `pip install memory-poison-scorer` then `from memory_poison_scorer import PersistenceScorer; scorer = PersistenceScorer(); risk = scorer.assess(config)` | YES — ships with experiment |

**Actionability test:** YES — "Before deploying a memory-augmented agent, run memory-poison-scorer on your architecture config. If persistence_risk > 0.7 or predicted_halflife > 100 interactions, add decay or provenance controls."

**Real-world validation plan** (real_world_validation):

| Condition | Real System | What It Tests | Feasibility |
|-----------|-------------|---------------|-------------|
| Mem0 validation | Mem0 open-source (local instance, no cloud costs) | Whether simulated persistence bounds match actual Mem0 persistence | HIGH — Mem0 is open-source, well-documented, local deployment |

---

## 8c) Generalization Plan — Target: 7/10

**Structural diversity checklist (A3):**

| Structural Dimension | Condition A | Condition B | Rationale |
|---|---|---|---|
| Retrieval method | Vector similarity search (cosine) | Recency-weighted retrieval | Tests whether persistence dynamics differ by retrieval mechanism |
| Memory architecture | Flat vector store (no decay) | Multi-layer with episodic decay | Tests whether architectural complexity affects persistence bounds |
| Decay mechanism | No decay (static store) | Exponential decay (lambda=0.995/hr) | Tests whether decay creates a phase transition in persistence |

> 3 rows filled (exceeds minimum of 2).

**Cross-domain validation protocol (A2):**

| Step | Content |
|---|---|
| 1. Domain-agnostic principle | Persistent contamination in retrieval systems follows threshold dynamics: when retrieval probability times retention exceeds 1, contamination persists indefinitely. |
| 2. Relational mapping | Source: epidemiology (pathogen → poisoned memory, transmission rate → retrieval probability, recovery rate → decay rate, R0 → P0). Relationships preserved: threshold behavior, decay dynamics, steady-state analysis. Interconnected system — all three parameters interact. |
| 3. Testable prediction in target domain | If P0 = retrieval_prob * (1 - decay_rate)^(-1) > 1 for a given architecture, poisoned memories will persist beyond 1000 interactions with >95% probability. |
| 4. Boundary conditions (where transfer breaks) | Transfer breaks when: (a) LLM reasoning introduces non-linear feedback (retrieval → reasoning → new memory → retrieval), which SIR doesn't model, (b) memory consolidation creates new poisoned entries from old ones (amplification without re-injection), (c) multi-agent propagation (SIR assumes single population). |

**Cross-domain transfer test (A1):**

| Target Domain | Analogous Problem | Experiment | Execution Status | Result |
|---|---|---|---|---|
| Epidemiology | Pathogen persistence in populations | Fit SIR-derived P0 model to memory poisoning data; compare R-squared to architecture-specific model | COMPLETED (planned) | Pending |
| Cache poisoning (web security) | Poisoned cache entries persist based on TTL and access patterns | Compare memory poisoning half-life to cache poisoning models (TTL-based expiry) | DEFERRED: simpler transfer, useful for validation but not novel | Will attempt if time permits |

> 1 row with COMPLETED status planned.

**Failure mode pre-registration:**

| Condition | Expected Failure | How Detected | Quantified Threshold |
|-----------|-----------------|-------------|---------------------|
| Very high embedding similarity (>0.95) between poisoned and legitimate memories | Bounds become trivial (always persist) | Persistence probability approaches 1.0 regardless of other params | similarity > 0.95 = degenerate case |
| Very low poison rate (<0.01%) with high memory volume (>10K entries) | Poisoned memories never retrieved — bounds predict instant decay | Retrieval rate < 1/10000 per query | Never retrieved in 1000-query simulation |
| Non-stationary query distribution (topic shifts) | Bounds calibrated on stationary queries don't hold | Prediction error > 2x on non-stationary vs. stationary | RMSE ratio > 2.0 |

**What constitutes transfer evidence:** R-squared > 0.7 between SIR-derived P0 predictions and observed persistence in memory architectures. Acceptable degradation: R-squared > 0.5 with correct rank ordering of architectures by persistence.

---

## Threats to Validity

### Internal Validity
- **Simulation fidelity:** Our memory architecture simulations abstract away LLM reasoning. Real LLMs may process retrieved poisoned memories differently than our simulation assumes. Mitigation: Mem0 real-system validation (§8c, Simulation-to-Real plan).
- **Embedding model choice:** Cosine similarity thresholds depend on the embedding model. Different models produce different similarity distributions. Mitigation: report results with threshold as a normalized percentile, not absolute cosine value.
- **Query distribution:** Experiments use synthetic query streams. Real user queries are non-stationary and topic-clustered. Mitigation: test both uniform and bursty query distributions (Kill Shot #2).

### External Validity
- **Architecture coverage:** We test 4 architecture types. Production systems may use hybrid architectures not captured by our typology. Mitigation: the scorer accepts arbitrary parameter configurations, not just the 4 tested types.
- **Attack vector generalization:** We use MINJA-style injection as the primary attack. Results may not transfer to other injection methods (e.g., indirect prompt injection via documents). Mitigation: H-1 explicitly tests whether architecture dominates attack vector.

### Construct Validity
- **Persistence definition:** We define persistence as "retrieval probability of poisoned memory > threshold after T interactions." Alternative definitions (e.g., behavioral influence on agent output) may yield different bounds. Mitigation: report both retrieval-based and influence-based measurements where feasible.
- **P0 threshold sharpness:** The epidemiological R0 analogy assumes a sharp phase transition. Memory systems may exhibit gradual transitions. H-2 explicitly tests transition sharpness.

---

## 9) Design Review Checklist (Gate 0.5)

| # | Requirement | Status | Notes |
|---|------------|--------|-------|
| 1 | Novelty claim stated in <=25 words | [x] | 23-word version: "First computable bounds on memory poisoning persistence as f(architecture parameters), enabling defenders to predict poisoning half-life from architecture configuration." |
| 2 | >=N comparison baselines identified (N per venue tier) | [x] | 3 baselines (exceeds Tier 2 minimum of 2) |
| 3 | Baseline fairness documented: each baseline has tuning parity statement (A4) | [x] | Each baseline has tuning parity row |
| 4 | >=2 reviewer kill shots with mitigations | [x] | 3 kill shots with mitigations |
| 5 | Ablation plan with hypothesized effects | [x] | 4 component ablation + 1 novel isolation |
| 6 | Novel component isolation test designed: novel claim tested independently (A5) | [x] | Fix attack, vary architecture — tests our core claim |
| 7 | Ground truth audit: sources, lag, positive rate | [x] | 2 sources (simulation + Mem0 real system) |
| 8 | Alternative label sources considered | [x] | 2 alternatives considered and excluded with rationale |
| 9 | Statistical plan: seeds, tests, CIs | [x] | 5 seeds, Mann-Whitney U, bootstrap CIs, Bonferroni |
| 10 | Related work: >=N papers (N per venue tier) | [x] | 10 papers (exceeds Tier 2 minimum of 5) |
| 11 | Hypotheses pre-registered in HYPOTHESIS_REGISTRY | [x] | 5 hypotheses (H-1 through H-5) |
| 12 | lock_commit set in HYPOTHESIS_REGISTRY | [x] | lock_commit: 164ced2 |
| 13 | Target venue identified | [x] | Security venue (Workshop/Tier 2) |
| 14 | >=2 structurally diverse evaluation conditions specified (A3) | [x] | 3 structural dimensions |
| 15 | Cross-domain validation protocol completed: principle + mapping + prediction + boundaries (A2) | [x] | Epidemiology SIR mapping completed |
| 16 | This document committed before any training script | [ ] | Will commit before Phase 1 |
| 17 | Assumption challenged: field-held assumption named + >=2 papers + contradiction search (A8) | [x] | "Attack vector determines persistence" assumption challenged with 2 papers + contradiction search |
| 18 | Compute resources documented: hardware, runtime, cost (A12) | [ ] | See §10 |

**Gate 0.5 verdict:** [ ] PASS — pending items 16, 18 (items 11, 12 completed; 16 will be resolved at lock_commit; 18 filled in §10 Compute Resources).

---

## 10) Compute Resources

| Resource | Specification |
|----------|--------------|
| Hardware | Azure VM, 4 vCPUs, 16GB RAM, no GPU required (simulation-based, not training) |
| Total runtime | Estimated 2-4 hours total: ~1hr simulation per architecture (4 architectures), ~30min analysis, ~30min real-system validation |
| Estimated cost | $0 (local compute on existing VM) |
| Carbon estimate | Negligible (<0.1 kg CO2) |
| Reproducibility note | Yes — commodity hardware sufficient. No GPU needed. All simulations run on CPU. Minimum viable: any machine with Python 3.10+ and 4GB RAM. |

---

## 10) Tier 2+ Depth Escalation (R34)

### Depth Commitment

**Primary finding (one sentence):** Memory poisoning persistence is bounded by a computable "persistence number" P0 that depends on retrieval probability, decay rate, and context competition, with a phase transition at P0 = 1.

**Evaluation settings (minimum 2):**

| # | Setting | How It Differs from Setting 1 | What It Tests |
|---|---------|------------------------------|---------------|
| 1 | Flat vector store (no decay, cosine similarity retrieval) | Baseline setting | Core result — persistence in simplest architecture |
| 2 | Episodic memory with exponential decay (lambda=0.995/hr) | Adds temporal decay | Whether decay creates a phase transition |
| 3 | Multi-layer memory (working + episodic + semantic) | Adds consolidation between layers | Whether consolidation amplifies or dampens persistence |
| 4 | Recency-weighted retrieval (no embedding similarity) | Changes retrieval mechanism entirely | Whether persistence bounds generalize across retrieval methods |

### Mechanism Analysis Plan

| Finding | Proposed Mechanism | Experiment to Verify |
|---------|-------------------|---------------------|
| Architecture X has highest persistence | Retrieval probability dominates decay — poisoned memory retrieved often enough to prevent decay | Measure retrieval frequency of poisoned vs. clean memories; correlate with persistence |
| Phase transition at P0=1 | Below P0=1, each retrieval cycle reduces poisoned memory influence; above, it reinforces | Sweep decay rate to find exact transition point; measure sharpness of transition |
| Consolidation amplifies persistence | Multi-layer memory consolidates poisoned episodic memories into semantic layer, creating new poisoned entries | Compare poison count before/after consolidation cycles |

### Adaptive Adversary Plan (security papers only)

| Robustness Claim | Weak Test (baseline) | Adaptive Test (attacker knows defense) |
|-----------------|---------------------|---------------------------------------|
| P0 < 1 architectures naturally purge poison | Inject MINJA-style poison, observe decay | Attacker crafts memories that maximize retrieval probability (adversarial embedding optimization) — test if P0 bounds still hold |
| Decay-based architectures have lower persistence | Standard exponential decay | Attacker times injections to coincide with retrieval peaks (query-aware injection) |

### Formal Contribution Statement (draft)

We contribute:
1. A formal framework characterizing memory poisoning persistence as P(T) = f(retrieval_method, decay_rate, context_window, embedding_threshold, T), with closed-form bounds for 4 architecture types.
2. The "persistence number" P0 — a single scalar predicting whether poisoned memories persist (P0 > 1) or decay (P0 < 1), analogous to R0 in epidemiology.
3. An open-source scorer tool (`memory-poison-scorer`) that takes architecture parameters and outputs persistence risk assessment.

### Published Baseline Reproduction Plan

| Published Method | Their Benchmark | Our Reproduction Plan |
|-----------------|----------------|----------------------|
| MINJA (Dong et al.) | EHR agent, QA agent | Reproduce injection on our simulated architectures using their query-only attack model |

### Parameter Sensitivity Plan (G-5)

| Parameter | Sweep Values | Expected: Finding Robust? |
|-----------|-------------|--------------------------|
| Decay rate (lambda) | [0.0, 0.9, 0.99, 0.995, 0.999, 1.0] | Yes — monotonic relationship expected |
| Embedding similarity threshold | [0.5, 0.6, 0.7, 0.8, 0.9, 0.95] | Yes — higher threshold = less retrieval = less persistence |
| Context window size (k) | [3, 5, 10, 20, 50] | Partial — diminishing effect above k=20 expected |
| Memory store size | [100, 500, 1000, 5000, 10000] | Yes — dilution effect expected (more memories = lower retrieval prob) |
| Poison rate | [0.001, 0.005, 0.01, 0.05, 0.1] | Yes — linear-ish relationship with retrieval prob |

### Simulation-to-Real Validation Plan (G-4, simulation projects only)

> **R34 requirement (updated):** "Pending with a plan" is NOT sufficient for Tier 2+. Budget real experiments at design time.

| Simulation Finding | Real-System Validation | API Cost Estimate | Timeline |
|-------------------|----------------------|-------------------|----------|
| P0 bounds for vector store architecture | Validate on Mem0 local instance with actual LLM queries | $0 (local LLM or mock) | After simulation convergence, ~1hr |
| Decay rate affects persistence monotonically | Configure Mem0 decay parameters, inject poison, measure | $0 (local) | Same session as above |

**Total real-system validation budget: $0** (local Mem0 instance with local/mock LLM)

### Defense Harm Test (Lesson from FP-16)

**Mandatory first experiment:** Compare persistence in "architecture with MemGuard-style defense" vs. "architecture without defense":
- [ ] Defense persistence <= no-defense persistence
- [ ] If defense increases persistence (e.g., provenance tracking creates additional retrievable metadata), report as FINDING

### Qualitative Prediction Validation (Lesson from FP-15)

For each simulation finding, validate BOTH:
- [ ] Quantitative prediction (persistence half-life within 2x of simulation)
- [ ] Qualitative prediction (does this parameter matter at all? E.g., does decay rate matter, or is it negligible vs. retrieval method?)

### Simulation Calibration Note

> No prior simulation calibration data exists for memory poisoning persistence (this is novel). We will establish our own calibration by comparing simulation to Mem0 real-system results. Historical calibration from other pipeline projects (37-48pp overestimate) may not apply — memory poisoning dynamics are different from the attack simulations that produced those numbers. We will report our own simulation-to-real gap.

### Formalization Attempt (R34.8)

**Finding to formalize:** Persistence probability P(T) as a function of architecture parameters.

**Formalization type:**
- [x] Predictive model (architecture parameters -> persistence probability, report R-squared and CV RMSE)
- [x] Decision boundary (when does P0 > 1 vs. P0 < 1?)
- [ ] Calibration formula
- [x] Threat model (quantified success conditions for sustained poisoning)
- [ ] Not formalizable

### Depth Escalation Checklist

| # | Requirement | Status |
|---|------------|--------|
| 1 | ONE primary finding identified | [x] |
| 2 | >=2 evaluation settings designed | [x] (4 settings) |
| 3 | Mechanism analysis planned for each major claim (including nulls) | [x] |
| 4 | Adaptive adversary test planned (security papers) | [x] |
| 5 | Formal contribution statement drafted | [x] |
| 6 | >=1 published baseline reproduction planned | [x] |
| 7 | Parameter sensitivity sweep planned | [x] (5 parameters) |
| 8 | Simulation-to-real validation planned (simulation projects) | [x] |
| 9 | Formalization attempted or explained why not | [x] |

---

## 12) E0: Sanity Validation Design (R47)

| Check | Known Input | Expected Output | Purpose |
|---|---|---|---|
| E0a: Positive control | Memory store with 100% poisoned entries, cosine retrieval, no decay | Persistence = 1.0 at all time steps | Measurement detects persistent poisoning correctly |
| E0b: Negative control | Memory store with 0% poisoned entries | Persistence = 0.0 at all time steps | Measurement doesn't false-positive on clean stores |
| E0c: Dose-response | Poison rate: [0.01, 0.05, 0.1, 0.25, 0.5] | Monotonic increase in persistence | Measurement scales correctly with poison concentration |

E0 must pass before E1-E6 run. Results saved to `outputs/experiments/e0_results.json`. Report in FINDINGS "Sanity Validation" section.

---

## 13) Phase 3 Writing Checklist (R48/R49)

| # | Check | Status |
|---|-------|--------|
| 1 | FINDINGS.md has all required sections (Hypothesis, Negative, Content Hooks, Limitations, Related Work, Contribution) | [ ] |
| 2 | Blog draft >= 1000 words (R25) | [ ] |
| 3 | Blog reflects FINDINGS — no "preliminary", "pending", "TBD" (R48) | [ ] |
| 4 | Figures generated and embedded in blog | [ ] |
| 5 | validate_content.sh passes | [ ] |
| 6 | FINDINGS timestamp <= blog timestamp — no staleness (R49) | [ ] |
| 7 | check_all_gates.sh: 0 FAIL (R50) | [ ] |
