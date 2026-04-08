# DECISION LOG — Memory Poisoning Persistence Bounds

> **R52 (Autonomous Research Quality Loop) iteration tracking.**
> Each iteration records: score before, gaps found, fixes applied, score after.
> STRUCTURAL gaps escalate to human. FIXABLE gaps are resolved by agent.

---

## Pre-Template Predictions (Builder Protocol: predict before analyzing)

**Date:** 2026-04-08

| Prediction | Value | Rationale |
|---|---|---|
| EXPERIMENTAL_DESIGN sections | ~11 (sections 0-10) | Based on prompt mentioning §0-§10 |
| Hardest section to fill | §8a Novelty Plan | Formalizing persistence bounds as f(architecture params) is the novel contribution — articulating what's new vs. 6+ attack papers requires careful differentiation |
| Hypotheses to pre-register | 4-5 | One per major architecture parameter: retrieval method, decay rate, context window, embedding threshold, plus interaction |
| Gate 0 flags | WARNs on missing FINDINGS.md, missing outputs/, possibly governance.yaml field mismatches | Gate 0 checks structure; research artifacts don't exist yet |

**Actuals (filled after Phase 1):**

| Prediction | Actual | Delta | Learning |
|---|---|---|---|
| ED sections | 14 (§0-§13) | +3 sections | Template includes Phase 1 exit checkpoint, E0 sanity design, Phase 3 writing checklist beyond the §0-§10 referenced in prompt |
| Hardest section | §8c Generalization (A2 cross-domain protocol) | Wrong — predicted §8a Novelty | Novelty was straightforward once related work was gathered. The 4-step Gentner mapping (SIR to memory poisoning) required careful relational analysis. |
| Hypotheses | 5 | Correct (predicted 4-5) | One per major parameter plus consolidation amplification |
| Gate 0 flags | 6 FAIL + 4 WARN (1 design-doc FAIL fixed, 5 expected pre-code FAILs) | More FAILs than expected — predicted WARNs only | Gate script checks downstream artifacts (tests, reproduce.sh, figures, FINDINGS) as FAILs not WARNs |

---

## D-1: Project Structure — 2026-04-08

**Decision:** Separate experiment code (src/) from pip-installable artifact (memory_poison_scorer/).

**Rationale:** The prompt specifies separate directories. Experiment code simulates memory architectures and runs poisoning benchmarks. The scorer package is the practitioner-facing artifact — it takes architecture parameters and outputs persistence risk scores. Clean separation means the artifact doesn't depend on experiment infrastructure.

**Alternatives considered:** Single package with experiment extras. Rejected because it would make the scorer heavier than needed for practitioners.

## D-2: Governance Profile — 2026-04-08

**Decision:** Use `contract-track` profile with `venue-security` target venue.

**Rationale:** The prompt specifies contract-track. venue-security is appropriate because this is security research (agent memory poisoning). Computational research type since we're running simulations and building models.

---

## Iteration 0 — Initial — 2026-04-08

- **Score:** TBD/10 | check_all_gates: TBD PASS, TBD FAIL, TBD WARN
- **Gaps found:**
  - STRUCTURAL: TBD
  - FIXABLE: TBD
- **Fixes applied:** TBD
- **Score after:** TBD/10
- **Action:** TBD
- **API cost:** ~$0 (no LLM API calls yet)

## Kill Condition Tracking

| Condition | Status | Notes |
|-----------|--------|-------|
| 3 iterations < 1pt improvement | NOT_TRIGGERED | |
| API budget exceeded | NOT_TRIGGERED | Budget: $5 |
| STRUCTURAL gap found | NO | |
| E0 fails on realistic data | NOT_TRIGGERED | |
| Score regression | NOT_TRIGGERED | |
