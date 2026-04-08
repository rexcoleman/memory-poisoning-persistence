# HYPOTHESIS REGISTRY

<!-- version: 1.0 -->
<!-- created: 2026-04-08 -->

> **Authority hierarchy:** Topic prompt (Tier 1) > govML templates (Tier 2) > Builder judgment (Tier 3) > This document (Contract)
> **Conflict rule:** When a higher-tier document and this contract disagree, the higher tier wins. Flag the conflict in the DECISION_LOG.
> **Upstream:** DATA_CONTRACT (data sources), METRICS_CONTRACT (metric definitions referenced in predictions)
> **Downstream:** EXPERIMENT_CONTRACT (experiment design grounded in hypotheses), REPORT_ASSEMBLY_PLAN (hypothesis statements and resolution templates), FINDINGS (hypothesis resolution narratives and evidence references)

## Pre-Registration Lock

**Lock commit:** TO BE SET
**Lock date:** 2026-04-08

> **Temporal gate (LL-74):** All hypotheses must be committed and locked before any experimental results are generated. Any experiment output with a git timestamp before the lock commit is invalid. Verify: `git log --oneline HYPOTHESIS_REGISTRY.md | tail -1` should predate all experiment outputs.

---

## 1) Pre-Registration Protocol

Hypotheses MUST be written **before** Phase 1 experiments begin.

**Gate:** >= 4 hypotheses registered and committed to version control before any experiment script is executed.

**Enforcement:**
- The hypothesis registry file MUST have a git commit timestamp earlier than any experiment output file.
- Adding hypotheses after seeing results is an academic integrity violation.
- Amendments to existing hypotheses (e.g., refining a threshold) MUST be tracked via `CONTRACT_CHANGE` commits with justification.

---

## 2) Hypothesis Format

Each hypothesis MUST include all fields in the following schema:

| Field | Description | Example |
|-------|-------------|---------|
| `hypothesis_id` | Sequential identifier | H-1, H-2, ... |
| `statement` | Clear, falsifiable statement | "Persistence varies by >10x across architectures" |
| `falsification_criterion` | What evidence would reject this hypothesis | "Max/min persistence ratio < 3x" |
| `metric` | Quantitative threshold for support/rejection | `max_persistence / min_persistence >= 10` |
| `resolution` | Final status | `SUPPORTED` / `REFUTED` / `INCONCLUSIVE` / `PENDING` |
| `evidence` | Reference to specific output file + metric value | `outputs/experiments/e1_architecture_comparison.json` |

---

## 3) Registry Table

| hypothesis_id | statement | falsification_criterion | metric | resolution | evidence |
|---------------|-----------|------------------------|--------|------------|----------|
| H-1 | Memory poisoning persistence varies by >= 10x across 4 architecture types (flat vector store, episodic with decay, multi-layer, recency-weighted) when the same attack vector (MINJA-style injection) is used. | Max/min persistence ratio across architectures < 3x with same attack | `max(persistence_halflife) / min(persistence_halflife) >= 10` | PENDING | -- |
| H-2 | For architectures with exponential decay (lambda), there exists a critical threshold P0 = retrieval_prob / decay_rate such that: when P0 > 1, poisoned memories persist beyond 1000 interactions with >90% probability; when P0 < 1, poisoned memories decay to <5% retrieval rate within 100 interactions. | No clear threshold separates persistent from decaying regimes, OR the transition is gradual (>200 interactions wide) rather than sharp. | `P0_threshold_exists == True AND transition_width < 200 interactions` | PENDING | -- |
| H-3 | Embedding similarity threshold is the single strongest predictor of persistence half-life across all architectures, explaining >= 40% of variance (R-squared >= 0.4) in a multivariate model including decay rate, context window, and retrieval method. | Embedding similarity threshold explains < 20% of variance (R-squared < 0.2), or another parameter explains more. | `R2_embedding_threshold >= 0.4 AND R2_embedding_threshold >= max(R2_other_params)` | PENDING | -- |
| H-4 | The epidemiological P0 model (SIR-derived persistence number) predicts architecture rank-ordering of persistence with Spearman rho >= 0.8, demonstrating that cross-domain transfer from epidemiology to memory security provides actionable predictions. | Spearman rho < 0.5 between SIR-predicted P0 rank order and observed persistence rank order. | `spearman_rho(predicted_rank, observed_rank) >= 0.8` | PENDING | -- |
| H-5 | Memory consolidation (multi-layer architectures that merge episodic into semantic memory) AMPLIFIES persistence: consolidated architectures show >= 2x longer persistence half-life than equivalent non-consolidating architectures with the same decay rate. | Consolidating architecture persistence half-life < 1.5x non-consolidating architecture. | `halflife_consolidating / halflife_non_consolidating >= 2.0` | PENDING | -- |

---

## 4) Resolution Protocol

After experiments complete, revisit **every** hypothesis and assign a resolution:

| Resolution | Criteria |
|------------|----------|
| **SUPPORTED** | Metric meets or exceeds the stated threshold across all specified conditions |
| **REFUTED** | Metric falls below the stated threshold |
| **INCONCLUSIVE** | Ambiguous results (e.g., supported on one condition but not another), insufficient data, or metric within noise margin (+/-1 std of threshold) |

**Resolution rules:**
- Every hypothesis MUST be resolved before Phase N+2 begins.
- The `evidence` field MUST reference a specific output file path and the exact metric value.
- INCONCLUSIVE resolutions MUST include a brief explanation of why the result is ambiguous.
- Resolutions are final once committed. A later experiment cannot retroactively change a resolution (register a new hypothesis instead).

---

## 5) Acceptance Criteria

- [x] >= 4 hypotheses registered before Phase 1
- [x] All hypotheses follow the required format (all 6 fields populated)
- [ ] All hypotheses resolved (no PENDING status at project end)
- [ ] Every resolution includes an evidence reference to a specific output file
- [ ] No hypothesis was added after experiment results were observed (verified by git timestamps)
- [ ] Resolution narrative for each hypothesis included in FINDINGS.md
