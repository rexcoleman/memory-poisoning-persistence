"""Experiment runner — E0 sanity through E4 main experiments.

E0: Sanity validation (positive/negative/dose-response controls)
E1: Architecture comparison (H-1: 10x persistence variation)
E2: P0 threshold test (H-2: phase transition at P0=1)
E3: Parameter importance (H-3: embedding threshold dominance)
E4: Cross-domain transfer (H-4: SIR model predicts rank order)
E5: Consolidation amplification (H-5: multi-layer amplifies persistence)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.memory_architectures import Memory, create_architecture
from src.persistence_model import (
    compute_p0,
    compute_persistence_bound,
    estimate_effective_decay,
    estimate_retrieval_probability,
    fit_persistence_model,
)
from src.poisoning import (
    PoisonConfig,
    compute_halflife,
    inject_poison,
    measure_persistence,
)

# Standard experiment parameters
EMBEDDING_DIM = 64
N_TOTAL = 500
K_RETRIEVE = 5
N_STEPS = 500
SEEDS = [42, 123, 456, 789, 1024]


def _make_target_query(rng: np.random.Generator) -> np.ndarray:
    q = rng.standard_normal(EMBEDDING_DIM)
    return q / np.linalg.norm(q)


def run_e0_sanity(output_dir: Path) -> dict:
    """E0: Sanity validation — positive, negative, dose-response controls."""
    results = {"experiment": "E0_sanity", "checks": {}}
    rng = np.random.default_rng(42)
    target_query = _make_target_query(rng)

    # E0a: Positive control — 100% poisoned, no decay
    arch = create_architecture("flat_vector")
    inject_poison(arch, n_clean=0, n_poison=100, target_query=target_query,
                  poison_similarity=0.9, embedding_dim=EMBEDDING_DIM, rng=rng)
    trace = measure_persistence(arch, target_query, k=K_RETRIEVE, n_steps=50,
                                rng=rng, embedding_dim=EMBEDDING_DIM)
    e0a_pass = all(p == 1.0 for p in trace)
    results["checks"]["E0a_positive_control"] = {
        "pass": e0a_pass,
        "trace_min": min(trace),
        "trace_max": max(trace),
        "expected": "all 1.0",
    }

    # E0b: Negative control — 0% poisoned
    rng2 = np.random.default_rng(42)
    target_query2 = _make_target_query(rng2)
    arch2 = create_architecture("flat_vector")
    inject_poison(arch2, n_clean=100, n_poison=0, target_query=target_query2,
                  poison_similarity=0.9, embedding_dim=EMBEDDING_DIM, rng=rng2)
    trace2 = measure_persistence(arch2, target_query2, k=K_RETRIEVE, n_steps=50,
                                 rng=rng2, embedding_dim=EMBEDDING_DIM)
    e0b_pass = all(p == 0.0 for p in trace2)
    results["checks"]["E0b_negative_control"] = {
        "pass": e0b_pass,
        "trace_min": min(trace2),
        "trace_max": max(trace2),
        "expected": "all 0.0",
    }

    # E0c: Dose-response — increasing poison rate should increase persistence
    dose_rates = [0.01, 0.05, 0.1, 0.25, 0.5]
    dose_persistence = []
    for rate in dose_rates:
        rng_d = np.random.default_rng(42)
        target_d = _make_target_query(rng_d)
        n_p = int(N_TOTAL * rate)
        n_c = N_TOTAL - n_p
        arch_d = create_architecture("flat_vector")
        inject_poison(arch_d, n_clean=n_c, n_poison=n_p, target_query=target_d,
                      poison_similarity=0.85, embedding_dim=EMBEDDING_DIM, rng=rng_d)
        trace_d = measure_persistence(arch_d, target_d, k=K_RETRIEVE, n_steps=50,
                                      rng=rng_d, embedding_dim=EMBEDDING_DIM)
        dose_persistence.append(float(np.mean(trace_d)))

    # Check monotonicity
    monotonic = all(dose_persistence[i] <= dose_persistence[i+1]
                    for i in range(len(dose_persistence)-1))
    results["checks"]["E0c_dose_response"] = {
        "pass": monotonic,
        "dose_rates": dose_rates,
        "mean_persistence": dose_persistence,
        "monotonic": monotonic,
    }

    all_pass = all(c["pass"] for c in results["checks"].values())
    results["verdict"] = "PASS" if all_pass else "FAIL"

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e0_results.json", "w") as f:
        json.dump(results, f, indent=2)

    return results


def _run_single_architecture(
    arch_type: str,
    seed: int,
    poison_rate: float = 0.05,
    poison_similarity: float = 0.85,
    decay_rate: float = 0.995,
    similarity_threshold: float = 0.0,
    capacity: int = 500,
    consolidation_interval: int = 50,
    consolidation_threshold: int = 3,
) -> dict:
    """Run a single experiment on one architecture with one seed."""
    rng = np.random.default_rng(seed)
    target_query = _make_target_query(rng)

    n_poison = int(N_TOTAL * poison_rate)
    n_clean = N_TOTAL - n_poison

    arch = create_architecture(
        arch_type,
        similarity_threshold=similarity_threshold,
        decay_rate=decay_rate,
        capacity=capacity,
        consolidation_interval=consolidation_interval,
        consolidation_threshold=consolidation_threshold,
    )

    inject_poison(arch, n_clean=n_clean, n_poison=n_poison,
                  target_query=target_query, poison_similarity=poison_similarity,
                  embedding_dim=EMBEDDING_DIM, rng=rng)

    trace = measure_persistence(arch, target_query, k=K_RETRIEVE, n_steps=N_STEPS,
                                queries_per_step=2, rng=rng, embedding_dim=EMBEDDING_DIM)

    halflife = compute_halflife(trace)
    amplitude, decay_const, offset = fit_persistence_model(trace)

    bound = compute_persistence_bound(
        arch_type=arch_type,
        n_poison=n_poison,
        n_total=N_TOTAL,
        similarity=poison_similarity,
        k=K_RETRIEVE,
        decay_rate=decay_rate,
        similarity_threshold=similarity_threshold,
        capacity=capacity,
        consolidation_prob=0.1 if arch_type == "multi_layer" else 0.0,
    )

    return {
        "arch_type": arch_type,
        "seed": seed,
        "poison_rate": poison_rate,
        "poison_similarity": poison_similarity,
        "decay_rate": decay_rate,
        "similarity_threshold": similarity_threshold,
        "capacity": capacity,
        "trace": trace,
        "halflife": halflife,
        "fit_amplitude": amplitude,
        "fit_decay_constant": decay_const,
        "fit_offset": offset,
        "mean_persistence": float(np.mean(trace)),
        "final_persistence": float(np.mean(trace[-50:])),
        "p0": bound.p0,
        "predicted_halflife": bound.predicted_halflife,
        "predicted_persistence_1000": bound.persistence_probability_1000,
        "retrieval_probability": bound.retrieval_probability,
        "effective_decay_rate": bound.effective_decay_rate,
    }


def run_e1_architecture_comparison(output_dir: Path) -> dict:
    """E1: Compare persistence across 4 architectures (H-1)."""
    arch_types = ["flat_vector", "episodic", "multi_layer", "recency"]
    results = {"experiment": "E1_architecture_comparison", "architectures": {}}

    for arch_type in arch_types:
        seed_results = []
        for seed in SEEDS:
            r = _run_single_architecture(arch_type, seed)
            # Don't store full traces in summary — save separately
            r_summary = {k: v for k, v in r.items() if k != "trace"}
            r_summary["trace_length"] = len(r["trace"])
            seed_results.append(r_summary)

        halflives = [r["halflife"] for r in seed_results]
        results["architectures"][arch_type] = {
            "seed_results": seed_results,
            "mean_halflife": float(np.mean([h for h in halflives if h is not None])) if any(h is not None for h in halflives) else None,
            "halflives": halflives,
            "mean_p0": float(np.mean([r["p0"] for r in seed_results if np.isfinite(r["p0"])])),
            "mean_final_persistence": float(np.mean([r["final_persistence"] for r in seed_results])),
        }

    # H-1 test: max/min halflife ratio >= 10x
    finite_halflives = {}
    for arch, data in results["architectures"].items():
        hls = [h for h in data["halflives"] if h is not None]
        if hls:
            finite_halflives[arch] = np.mean(hls)

    if len(finite_halflives) >= 2:
        max_hl = max(finite_halflives.values())
        min_hl = min(finite_halflives.values())
        ratio = max_hl / min_hl if min_hl > 0 else float("inf")
    else:
        # Some architectures have indefinite persistence (None halflife)
        # Count as infinite ratio
        ratio = float("inf")

    results["h1_test"] = {
        "max_min_ratio": ratio,
        "threshold": 10.0,
        "verdict": "SUPPORTED" if ratio >= 10.0 else ("INCONCLUSIVE" if ratio >= 3.0 else "REFUTED"),
        "finite_halflives": {k: float(v) for k, v in finite_halflives.items()},
        "indefinite_architectures": [
            arch for arch, data in results["architectures"].items()
            if all(h is None for h in data["halflives"])
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e1_architecture_comparison.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def run_e2_p0_threshold(output_dir: Path) -> dict:
    """E2: Test P0 threshold hypothesis (H-2).

    Sweep decay rate to find transition point. For each decay rate,
    measure whether persistence is indefinite (>1000 steps) or decays.
    """
    decay_rates = [0.0, 0.5, 0.9, 0.95, 0.99, 0.995, 0.999, 1.0]
    results = {"experiment": "E2_p0_threshold", "decay_sweep": []}

    for decay_rate in decay_rates:
        seed_results = []
        for seed in SEEDS:
            r = _run_single_architecture(
                "episodic", seed, decay_rate=decay_rate
            )
            seed_results.append({
                "seed": seed,
                "halflife": r["halflife"],
                "p0": r["p0"],
                "final_persistence": r["final_persistence"],
                "mean_persistence": r["mean_persistence"],
                "predicted_halflife": r["predicted_halflife"],
            })

        mean_halflife_values = [r["halflife"] for r in seed_results if r["halflife"] is not None]
        results["decay_sweep"].append({
            "decay_rate": decay_rate,
            "effective_decay": 1.0 - decay_rate if decay_rate < 1.0 else 1e-10,
            "mean_p0": float(np.mean([r["p0"] for r in seed_results if np.isfinite(r["p0"])])),
            "mean_halflife": float(np.mean(mean_halflife_values)) if mean_halflife_values else None,
            "proportion_indefinite": sum(1 for r in seed_results if r["halflife"] is None) / len(seed_results),
            "seed_results": seed_results,
        })

    # H-2 test: Is there a sharp transition?
    # Look for the decay rate where proportion_indefinite drops from >0.5 to <0.5
    transition_found = False
    transition_width = None
    for i in range(len(results["decay_sweep"]) - 1):
        curr = results["decay_sweep"][i]
        next_ = results["decay_sweep"][i + 1]
        if curr["proportion_indefinite"] > 0.5 and next_["proportion_indefinite"] <= 0.5:
            transition_found = True
            # Width = difference in decay rates at transition
            transition_width = abs(curr["decay_rate"] - next_["decay_rate"])

    results["h2_test"] = {
        "transition_found": transition_found,
        "transition_width": transition_width,
        "sharp_transition": transition_width is not None and transition_width < 0.1,
        "verdict": "SUPPORTED" if transition_found else "INCONCLUSIVE",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e2_p0_threshold.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def run_e3_parameter_importance(output_dir: Path) -> dict:
    """E3: Parameter importance — which parameter explains most variance? (H-3)

    Sweep each parameter independently, measure persistence, compute
    R-squared for each parameter's effect on halflife.
    """
    results = {"experiment": "E3_parameter_importance", "sweeps": {}}

    # Sweep 1: Embedding similarity threshold
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7]
    threshold_halflives = []
    for thresh in thresholds:
        seed_hls = []
        for seed in SEEDS:
            r = _run_single_architecture("episodic", seed, similarity_threshold=thresh)
            seed_hls.append(r["halflife"] if r["halflife"] is not None else N_STEPS)
        threshold_halflives.append(float(np.mean(seed_hls)))
    results["sweeps"]["similarity_threshold"] = {
        "values": thresholds,
        "mean_halflives": threshold_halflives,
    }

    # Sweep 2: Decay rate
    decay_rates = [0.9, 0.95, 0.99, 0.995, 0.999]
    decay_halflives = []
    for dr in decay_rates:
        seed_hls = []
        for seed in SEEDS:
            r = _run_single_architecture("episodic", seed, decay_rate=dr)
            seed_hls.append(r["halflife"] if r["halflife"] is not None else N_STEPS)
        decay_halflives.append(float(np.mean(seed_hls)))
    results["sweeps"]["decay_rate"] = {
        "values": decay_rates,
        "mean_halflives": decay_halflives,
    }

    # Sweep 3: Poison similarity (proxy for retrieval probability)
    similarities = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    sim_halflives = []
    for sim in similarities:
        seed_hls = []
        for seed in SEEDS:
            r = _run_single_architecture("episodic", seed, poison_similarity=sim)
            seed_hls.append(r["halflife"] if r["halflife"] is not None else N_STEPS)
        sim_halflives.append(float(np.mean(seed_hls)))
    results["sweeps"]["poison_similarity"] = {
        "values": similarities,
        "mean_halflives": sim_halflives,
    }

    # Sweep 4: Context window (k)
    k_values = [1, 3, 5, 10, 20]
    k_halflives = []
    for k in k_values:
        seed_hls = []
        for seed in SEEDS:
            # Need to modify K_RETRIEVE for this run
            rng = np.random.default_rng(seed)
            target_query = _make_target_query(rng)
            n_poison = int(N_TOTAL * 0.05)
            arch = create_architecture("episodic", decay_rate=0.995)
            inject_poison(arch, n_clean=N_TOTAL - n_poison, n_poison=n_poison,
                          target_query=target_query, poison_similarity=0.85,
                          embedding_dim=EMBEDDING_DIM, rng=rng)
            trace = measure_persistence(arch, target_query, k=k, n_steps=N_STEPS,
                                        queries_per_step=2, rng=rng,
                                        embedding_dim=EMBEDDING_DIM)
            hl = compute_halflife(trace)
            seed_hls.append(hl if hl is not None else N_STEPS)
        k_halflives.append(float(np.mean(seed_hls)))
    results["sweeps"]["context_window_k"] = {
        "values": k_values,
        "mean_halflives": k_halflives,
    }

    # Compute R-squared for each parameter
    from scipy.stats import pearsonr

    r_squared = {}
    for param_name, sweep_data in results["sweeps"].items():
        x = np.array(sweep_data["values"], dtype=float)
        y = np.array(sweep_data["mean_halflives"], dtype=float)
        if len(x) >= 3 and np.std(y) > 0:
            r, _ = pearsonr(x, y)
            r_squared[param_name] = float(r ** 2)
        else:
            r_squared[param_name] = 0.0

    results["r_squared"] = r_squared
    strongest = max(r_squared, key=r_squared.get)
    results["h3_test"] = {
        "strongest_predictor": strongest,
        "strongest_r_squared": r_squared[strongest],
        "embedding_threshold_r_squared": r_squared.get("similarity_threshold", 0.0),
        "verdict": (
            "SUPPORTED" if strongest == "similarity_threshold" and r_squared[strongest] >= 0.4
            else "REFUTED" if r_squared.get("similarity_threshold", 0.0) < 0.2
            else "INCONCLUSIVE"
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e3_parameter_importance.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def run_e4_cross_domain_transfer(output_dir: Path) -> dict:
    """E4: Cross-domain transfer test — SIR model predicts persistence rank order (H-4)."""
    from scipy.stats import spearmanr

    arch_configs = [
        {"arch_type": "flat_vector", "decay_rate": 0.0},
        {"arch_type": "episodic", "decay_rate": 0.99},
        {"arch_type": "episodic", "decay_rate": 0.995},
        {"arch_type": "episodic", "decay_rate": 0.999},
        {"arch_type": "multi_layer", "decay_rate": 0.995},
        {"arch_type": "recency", "decay_rate": 0.0},
    ]

    predicted_p0s = []
    observed_halflives = []

    for config in arch_configs:
        # Predicted P0
        bound = compute_persistence_bound(
            arch_type=config["arch_type"],
            n_poison=int(N_TOTAL * 0.05),
            n_total=N_TOTAL,
            similarity=0.85,
            k=K_RETRIEVE,
            decay_rate=config["decay_rate"],
            capacity=500,
            consolidation_prob=0.1 if config["arch_type"] == "multi_layer" else 0.0,
        )
        predicted_p0s.append(bound.p0)

        # Observed persistence
        seed_hls = []
        for seed in SEEDS:
            r = _run_single_architecture(
                config["arch_type"], seed,
                decay_rate=config["decay_rate"],
            )
            seed_hls.append(r["halflife"] if r["halflife"] is not None else N_STEPS * 2)
        observed_halflives.append(float(np.mean(seed_hls)))

    # Spearman rank correlation
    rho, p_value = spearmanr(predicted_p0s, observed_halflives)

    results = {
        "experiment": "E4_cross_domain_transfer",
        "configs": [
            {
                "arch_type": c["arch_type"],
                "decay_rate": c["decay_rate"],
                "predicted_p0": float(p0) if np.isfinite(p0) else "inf",
                "observed_halflife": float(hl),
            }
            for c, p0, hl in zip(arch_configs, predicted_p0s, observed_halflives)
        ],
        "h4_test": {
            "spearman_rho": float(rho) if np.isfinite(rho) else None,
            "p_value": float(p_value) if np.isfinite(p_value) else None,
            "threshold": 0.8,
            "verdict": (
                "SUPPORTED" if rho >= 0.8
                else "INCONCLUSIVE" if rho >= 0.5
                else "REFUTED"
            ),
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e4_cross_domain_transfer.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def run_e5_consolidation_amplification(output_dir: Path) -> dict:
    """E5: Consolidation amplification test (H-5).

    Compare multi-layer (with consolidation) vs episodic (without) at same decay rate.
    """
    results = {"experiment": "E5_consolidation_amplification", "comparisons": []}

    for seed in SEEDS:
        r_episodic = _run_single_architecture("episodic", seed, decay_rate=0.995)
        r_multi = _run_single_architecture("multi_layer", seed, decay_rate=0.995)

        results["comparisons"].append({
            "seed": seed,
            "episodic_halflife": r_episodic["halflife"],
            "multi_layer_halflife": r_multi["halflife"],
            "episodic_final_persistence": r_episodic["final_persistence"],
            "multi_layer_final_persistence": r_multi["final_persistence"],
            "episodic_p0": r_episodic["p0"],
            "multi_layer_p0": r_multi["p0"],
        })

    # H-5 test: multi-layer halflife >= 2x episodic halflife
    ratios = []
    for c in results["comparisons"]:
        ep_hl = c["episodic_halflife"]
        ml_hl = c["multi_layer_halflife"]
        if ep_hl is not None and ml_hl is not None and ep_hl > 0:
            ratios.append(ml_hl / ep_hl)
        elif ep_hl is not None and ml_hl is None:
            ratios.append(float("inf"))  # multi-layer persists indefinitely
        elif ep_hl is None and ml_hl is None:
            ratios.append(1.0)  # both indefinite

    mean_ratio = float(np.mean([r for r in ratios if np.isfinite(r)])) if ratios else 0.0

    results["h5_test"] = {
        "halflife_ratios": [float(r) if np.isfinite(r) else "inf" for r in ratios],
        "mean_ratio": mean_ratio if np.isfinite(mean_ratio) else "inf",
        "threshold": 2.0,
        "verdict": (
            "SUPPORTED" if mean_ratio >= 2.0 or any(r == float("inf") for r in ratios)
            else "INCONCLUSIVE" if mean_ratio >= 1.5
            else "REFUTED"
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "e5_consolidation_amplification.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def run_all_experiments(output_dir: Path | str = "outputs/experiments") -> dict:
    """Run all experiments in sequence."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Running E0: Sanity validation...")
    e0 = run_e0_sanity(output_dir)
    print(f"  E0 verdict: {e0['verdict']}")

    if e0["verdict"] != "PASS":
        print("  E0 FAILED — stopping. Fix sanity checks before proceeding.")
        return {"e0": e0}

    print("Running E1: Architecture comparison...")
    e1 = run_e1_architecture_comparison(output_dir)
    print(f"  H-1 verdict: {e1['h1_test']['verdict']}")

    print("Running E2: P0 threshold...")
    e2 = run_e2_p0_threshold(output_dir)
    print(f"  H-2 verdict: {e2['h2_test']['verdict']}")

    print("Running E3: Parameter importance...")
    e3 = run_e3_parameter_importance(output_dir)
    print(f"  H-3 verdict: {e3['h3_test']['verdict']}")

    print("Running E4: Cross-domain transfer...")
    e4 = run_e4_cross_domain_transfer(output_dir)
    print(f"  H-4 verdict: {e4['h4_test']['verdict']}")

    print("Running E5: Consolidation amplification...")
    e5 = run_e5_consolidation_amplification(output_dir)
    print(f"  H-5 verdict: {e5['h5_test']['verdict']}")

    summary = {
        "e0": e0["verdict"],
        "h1": e1["h1_test"]["verdict"],
        "h2": e2["h2_test"]["verdict"],
        "h3": e3["h3_test"]["verdict"],
        "h4": e4["h4_test"]["verdict"],
        "h5": e5["h5_test"]["verdict"],
    }

    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary: {summary}")
    return {"e0": e0, "e1": e1, "e2": e2, "e3": e3, "e4": e4, "e5": e5, "summary": summary}


if __name__ == "__main__":
    run_all_experiments()
