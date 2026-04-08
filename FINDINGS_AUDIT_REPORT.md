# Findings Audit Report
Generated: 2026-04-08 05:55 UTC
Project: memory-poisoning-persistence

## Summary
- Claims found: 217
- Claims with JSON match: 162
- Claims without JSON match: 30 (REVIEW NEEDED)
- Close but not exact: 25 (CHECK ROUNDING)
- Claim strength tags: 5/217 claims tagged (2%)
- Seeds found: 0

## Unmatched Claims (review required)
| Line | Claim Text | Number | Status |
|------|-----------|--------|--------|
| 4 | <!-- created: **2026** -04-08 --> | 2026 | NO MATCH |
| 4 | <!-- created: 2026- **04** -08 --> | 04 | NO MATCH |
| 48 | exhibiting indefinite persistence and fast-decaying episodic memories purging... | 13 | NO MATCH |
| 78 | (decay=0.995): indefinite (5/5 seeds). Episodic (decay=0.99 in E2): halflife=... | 21.5 | NO MATCH |
| 78 | steps (mean +/- std, n=5 seeds). Episodic (decay=0.9): halflife=13.2 +/- **11... | 11.8 | NO MATCH |
| 92 | parameter sweep across 4 dimensions, the embedding similarity threshold expla... | 92 | NO MATCH |
| 102 | = 0.005 (between decay_rate=0.99 and 0.995). Below transition: halflife=380.2... | 21.5 | NO MATCH |
| 102 | 0.995). Below transition: halflife=380.2 +/- 21.5 (decay=0.99, n=5), 49.0 +/-... | 26.6 | NO MATCH |
| 102 | 21.5 (decay=0.99, n=5), 49.0 +/- 26.6 (decay=0.95, n=5), 13.2 +/- **11.8** (d... | 11.8 | NO MATCH |
| 105 | finite half-lives that decrease monotonically with decay rate. Above it, **10... | 100 | NO MATCH |
| 143 | threshold with sharp transition \| Transition exists and width < **200** steps... | 200 | NO MATCH |
| 144 | \| H-3: Similarity threshold strongest predictor \| R² >= **0.4** and highest a... | 0.4 | NO MATCH |
| 180 | similarity thresholds depend on the embedding model's output distribution. Ou... | 64 | NO MATCH |
| 204 | Your choice of memory architecture determines whether poisoned memories last ... | 13 | NO MATCH |
| 205 | \| One parameter — the embedding similarity threshold — explains **92%** of pe... | 92 | NO MATCH |
| 213 | "agent memory attack temporal dynamics," "formal persistence bounds." Covered... | 2024 | NO MATCH |
| 213 | memory attack temporal dynamics," "formal persistence bounds." Covered NeurIP... | 2025 | NO MATCH |
| 213 | dynamics," "formal persistence bounds." Covered NeurIPS 2024-2025, preprints ... | 2026 | NO MATCH |
| 216 | 1. MemoryGraft ( **2512.16962** ): attacks via experience retrieval — we form... | 2512.16962 | NO MATCH |
| 217 | 2. MINJA (2503.03704): **95%** ISR via query-only injection — we measure what... | 95 | NO MATCH |
| 217 | 2. MINJA ( **2503.03704** ): 95% ISR via query-only injection — we measure what | 2503.03704 | NO MATCH |
| 218 | 3. arXiv:260 **1.05504** : varies retrieval parameters, finds 40pp ASR variat... | 1.05504 | NO MATCH |
| 218 | 3. arXiv:2601.05504: varies retrieval parameters, finds **40pp** ASR variatio... | 40 | NO MATCH |
| 219 | 4. AgentPoison ( **2407.12784** ): RAG poisoning at <0.1% rate — we extend from | 2407.12784 | NO MATCH |
| 220 | 5. Torra ( **2603.20357** ): calls formalization "difficult" — we attempt and... | 2603.20357 | NO MATCH |
| 235 | magnitude:** ~50,000+ engineers building memory-augmented LLM agents. OWASP A... | 2026 | NO MATCH |
| 283 | (flat vector, episodic, multi-layer, recency), 5 seeds each, 500-step experim... | 64 | NO MATCH |
| 297 | < 0.1 \| threshold < 0.1 \| Persistence halflife > **400** steps \| Degrades — n... | 400 | NO MATCH |
| 326 | \| E3 parameter importance \| outputs/experiments/e3_parameter_importance.json ... | 77596 | NO MATCH |
| 336 | - [x] **100%** of quantitative claims tagged | 100 | NO MATCH |

## Close Matches (check rounding)
| Line | FINDINGS Value | JSON Value | JSON Path | Delta |
|------|---------------|-----------|-----------|-------|
| 48 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 78 | 28.8 | 29 | experiments/e2_p0_threshold.json::decay_sweep[2].seed_results[2].halflife | 0.200000 |
| 89 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 113 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 113 | 0.558 | 0.557699 | experiments/e4_cross_domain_transfer.json::h4_test.p_value | 0.000301 |
| 116 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 142 | 28.8 | 29 | experiments/e2_p0_threshold.json::decay_sweep[2].seed_results[2].halflife | 0.200000 |
| 144 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 144 | 0.921 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.000219 |
| 145 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 145 | 0.558 | 0.557699 | experiments/e4_cross_domain_transfer.json::h4_test.p_value | 0.000301 |
| 145 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 157 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 191 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 193 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 224 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 239 | 70 | 70.2 | experiments/e3_parameter_importance.json::sweeps.similarity_threshold.mean_halflives[4] | 0.200000 |
| 241 | 380 | 380.2 | experiments/e2_p0_threshold.json::decay_sweep[4].mean_halflife | 0.200000 |
| 272 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 272 | 0.304 | 0.304256 | experiments/e4_cross_domain_transfer.json::h4_test.spearman_rho | 0.000256 |
| 272 | 0.558 | 0.557699 | experiments/e4_cross_domain_transfer.json::h4_test.p_value | 0.000301 |
| 289 | 380 | 380.2 | experiments/e2_p0_threshold.json::decay_sweep[4].mean_halflife | 0.200000 |
| 301 | 0.92 | 0.921219 | experiments/e3_parameter_importance.json::r_squared.similarity_threshold | 0.001219 |
| 321 | 256 | 252.8 | experiments/e3_parameter_importance.json::sweeps.similarity_threshold.mean_halflives[2] | 3.200000 |
| 345 | 256 | 252.8 | experiments/e3_parameter_importance.json::sweeps.similarity_threshold.mean_halflives[2] | 3.200000 |

## Untagged Claims
| Line | Claim Text |
|------|-----------|
| 3 | <!-- version: 1.0 --> |
| 4 | <!-- created: 2026-04-08 --> |
| 41 | **Seeds:** 5 (42, 123, 456, 789, 1024) |
| 42 | **Claim tagging:** Per CLAIM_STRENGTH_SPEC v1.0 |
| 48 | Memory poisoning persistence varies by over 10x across memory architecture ty... |
| 58 | **Interpretation:** The binary rule ("decay or no decay") captures the coarse... |
| 78 | **Metric:** Flat vector store: indefinite persistence (halflife=None, all 5 s... |
| 81 | Using the same MINJA-style injection attack (5% poison rate, 0.85 similarity)... |
| 89 | **Metric:** similarity_threshold R²=0.92, decay_rate R²=0.85, poison_similari... |
| 92 | In a multivariate parameter sweep across 4 dimensions, the embedding similari... |
| 94 | **Important caveat:** The R²=0.00 for poison_similarity and context_window_k ... |
| 96 | ### Finding 3: Sharp phase transition at decay_rate ≈ 0.9925 |
| 102 | **Metric:** Transition width = 0.005 (between decay_rate=0.99 and 0.995). Bel... |
| 105 | A sharp phase transition separates decaying and indefinitely-persisting regim... |
| 113 | **Metric:** Spearman rho = 0.304 (p=0.558). Threshold for SUPPORTED was rho >... |
| 116 | The P0 model (persistence number derived from SIR epidemiology) does not accu... |
| 118 | 1. **Saturation:** Many architectures (flat_vector, episodic at 0.995/0.999, ... |
| 119 | 2. **Recency architecture breaks the model:** Recency has P0=125 but halflife... |
| 121 | **Assessment:** This is partially a design issue (saturation from too-slow de... |
| 123 | ### Finding 5: Consolidation does not amplify persistence at decay_rate=0.995 |
| 127 | **Qualifiers:** SYNTHETIC, SCOPED (to decay_rate=0.995 only) |
| 129 | **Metric:** Multi-layer/episodic halflife ratio = 1.0 across all 5 seeds (bot... |
| 132 | At decay_rate=0.995, both episodic and multi-layer architectures show indefin... |
| 134 | **Assessment:** This is entirely a design issue. At decay_rate=0.995, the epi... |
| 142 | \| H-1: Architecture varies persistence >=10x \| Max/min halflife ratio >= 10 \|... |
| 143 | \| H-2: P0 threshold with sharp transition \| Transition exists and width < 200... |
| 144 | \| H-3: Similarity threshold strongest predictor \| R² >= 0.4 and highest among... |
| 145 | \| H-4: SIR model predicts rank order (rho >= 0.8) \| Spearman rho >= 0.8 \| Spe... |
| 146 | \| H-5: Consolidation amplifies persistence >=2x \| Multi-layer halflife / epis... |
| 148 | > **Resolution change from experiment output:** H-5 was coded as REFUTED in t... |
| 156 | **What was expected:** P0 (retrieval_prob / effective_decay) would predict pe... |
| 157 | **What happened:** Spearman rho = 0.304. The recency architecture has P0=125 ... |
| 164 | **What happened:** R²=0.00 for both parameters in E3. |
| 165 | **Why this matters:** This is a ceiling effect, not a true null. At decay_rat... |
| 166 | **Implication:** Future parameter sweeps should use a decay rate in the discr... |
| 174 | 2. **Parameter sweep ceiling effects obscure secondary parameter importance.*... |
| 176 | 3. **Recency architecture breaks the P0 model.** The persistence number frame... |
| 178 | 4. **Consolidation hypothesis remains untested.** The multi-layer vs episodic... |
| 180 | 5. **Embedding model dependency.** Cosine similarity thresholds depend on the... |
| 191 | \| Finding 2 \| Similarity threshold is strongest persistence predictor (R²=0.9... |
| 192 | \| Finding 3 \| Sharp phase transition at decay_rate ≈ 0.9925 \| [DEMONSTRATED, ... |
| 193 | \| Finding 4 \| SIR model does not predict rank ordering (rho=0.304) \| [DEMONST... |
| 194 | \| Finding 5 \| Consolidation amplification untestable at decay=0.995 \| [DEMONS... |
| 196 | **How synthetic data may differ from production data:** Real memory architect... |
| 204 | \| Finding 1 \| Your choice of memory architecture determines whether poisoned ... |
| 205 | \| Finding 2 \| One parameter — the embedding similarity threshold — explains 9... |
| 206 | \| Finding 3 \| A decay rate of 0.99 vs 0.995 is the difference between finite ... |
| 213 | **Prior art search:** Searched arXiv, Google Scholar, Semantic Scholar, OpenR... |
| 216 | 1. MemoryGraft (2512.16962): attacks via experience retrieval — we formalize ... |
| 217 | 2. MINJA (2503.03704): 95% ISR via query-only injection — we measure what hap... |
| 218 | 3. arXiv:2601.05504: varies retrieval parameters, finds 40pp ASR variation — ... |
| 219 | 4. AgentPoison (2407.12784): RAG poisoning at <0.1% rate — we extend from sta... |
| 220 | 5. Torra (2603.20357): calls formalization "difficult" — we attempt and parti... |
| 224 | **What surprised us:** H-3 was the biggest surprise. We expected similarity t... |
| 226 | The H-4 refutation was also surprising — we expected the epidemiological anal... |
| 235 | **Problem magnitude:** ~50,000+ engineers building memory-augmented LLM agent... |
| 239 | 1. [DEMONSTRATED, SYNTHETIC] **Set embedding similarity threshold >= 0.5 for ... |
| 241 | 2. [DEMONSTRATED, SYNTHETIC] **Use decay_rate <= 0.99 if your threat model in... |
| 253 | **Baseline fairness statement (A4):** All architectures received identical at... |
| 272 | \| Epidemiology → memory security \| SIR-derived P0 predicts architecture persi... |
| 283 | **Scope:** 4 memory architecture types (flat vector, episodic, multi-layer, r... |
| 289 | \| Flat vector vs episodic \| Architecture type (no decay vs decay) \| Flat vect... |
| 291 | \| Decay rate 0.9 vs 0.999 \| Decay mechanism strength \| 13.2 vs indefinite hal... |
| 297 | \| Similarity threshold < 0.1 \| threshold < 0.1 \| Persistence halflife > 400 s... |
| 298 | \| Decay rate > 0.99 \| decay_rate > 0.99 \| Phase transition to indefinite pers... |
| 299 | \| Recency with large capacity \| capacity > 1000 \| Poison survives > 1000 inse... |
| 321 | \| Artifact \| Path \| SHA-256 \| Description \| |
| 324 | \| E1 architecture comparison \| outputs/experiments/e1_architecture_comparison... |
| 325 | \| E2 P0 threshold \| outputs/experiments/e2_p0_threshold.json \| 203bc966...5fa... |
| 326 | \| E3 parameter importance \| outputs/experiments/e3_parameter_importance.json ... |
| 328 | \| E5 consolidation \| outputs/experiments/e5_consolidation_amplification.json ... |
| 336 | - [x] 100% of quantitative claims tagged |
| 345 | - [x] Artifact Registry populated with SHA-256 hashes |

## Seed Analysis
Seeds found: *none detected*
Minimum required: 3
Status: FAIL
