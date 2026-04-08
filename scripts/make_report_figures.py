#!/usr/bin/env python3
"""Generate publication-quality figures for Memory Poisoning Persistence Bounds.

Produces:
1. Architecture comparison — bar chart of half-lives across 4 architectures
2. P0 phase transition — decay rate vs persistence proportion
3. Parameter importance — R-squared comparison
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUTPUT_DIR = Path(__file__).parent.parent / "figures"
DATA_DIR = Path(__file__).parent.parent / "outputs" / "experiments"


def fig1_p0_phase_transition():
    """Figure 1: Phase transition at decay_rate ≈ 0.9925."""
    with open(DATA_DIR / "e2_p0_threshold.json") as f:
        e2 = json.load(f)

    decay_rates = []
    halflives = []
    prop_indef = []

    for d in e2["decay_sweep"]:
        dr = d["decay_rate"]
        if dr == 0.0:
            continue  # skip zero for log-friendly plotting
        decay_rates.append(dr)
        hl = d["mean_halflife"]
        halflives.append(hl if hl is not None else 600)
        prop_indef.append(d["proportion_indefinite"])

    fig, ax1 = plt.subplots(figsize=(8, 5), dpi=300)

    color1 = "#2563eb"
    color2 = "#dc2626"

    ax1.set_xlabel("Decay Rate", fontsize=12)
    ax1.set_ylabel("Mean Half-life (steps)", fontsize=12, color=color1)
    ax1.plot(decay_rates, halflives, "o-", color=color1, linewidth=2, markersize=8, label="Half-life")
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(-20, 650)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Proportion Indefinite", fontsize=12, color=color2)
    ax2.bar(decay_rates, prop_indef, width=0.015, alpha=0.3, color=color2, label="Prop. indefinite")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(-0.05, 1.1)

    # Mark transition
    ax1.axvline(x=0.9925, color="gray", linestyle="--", alpha=0.7)
    ax1.annotate("Phase transition\n(decay ≈ 0.9925)",
                 xy=(0.9925, 400), fontsize=9, ha="center",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray"))

    ax1.set_title("P0 Phase Transition: Decay Rate vs Persistence", fontsize=14)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig1_p0_phase_transition.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / 'fig1_p0_phase_transition.png'}")


def fig2_parameter_importance():
    """Figure 2: R-squared comparison across parameters."""
    with open(DATA_DIR / "e3_parameter_importance.json") as f:
        e3 = json.load(f)

    params = list(e3["r_squared"].keys())
    r2_values = [e3["r_squared"][p] for p in params]

    # Clean up names
    labels = {
        "similarity_threshold": "Similarity\nThreshold",
        "decay_rate": "Decay\nRate",
        "poison_similarity": "Poison\nSimilarity",
        "context_window_k": "Context\nWindow (k)",
    }

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    colors = ["#2563eb" if r > 0.4 else "#94a3b8" for r in r2_values]
    bars = ax.bar([labels.get(p, p) for p in params], r2_values, color=colors, edgecolor="white", linewidth=1.5)

    for bar, val in zip(bars, r2_values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                f"R²={val:.2f}", ha="center", fontsize=10, fontweight="bold")

    ax.axhline(y=0.4, color="red", linestyle="--", alpha=0.5, label="H-3 threshold (R²=0.4)")
    ax.set_ylabel("R² (variance explained)", fontsize=12)
    ax.set_title("Parameter Importance for Persistence Half-life", fontsize=14)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig2_parameter_importance.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / 'fig2_parameter_importance.png'}")


def fig3_similarity_threshold_sweep():
    """Figure 3: Similarity threshold vs half-life."""
    with open(DATA_DIR / "e3_parameter_importance.json") as f:
        e3 = json.load(f)

    sweep = e3["sweeps"]["similarity_threshold"]
    thresholds = sweep["values"]
    halflives = sweep["mean_halflives"]

    fig, ax = plt.subplots(figsize=(7, 5), dpi=300)
    ax.plot(thresholds, halflives, "o-", color="#2563eb", linewidth=2, markersize=10)
    ax.fill_between(thresholds, halflives, alpha=0.1, color="#2563eb")

    ax.set_xlabel("Similarity Threshold", fontsize=12)
    ax.set_ylabel("Mean Half-life (steps)", fontsize=12)
    ax.set_title("40x Defense: Similarity Threshold vs Persistence", fontsize=14)

    ax.annotate(f"40x reduction\n({halflives[0]:.0f} → {halflives[-1]:.0f} steps)",
                xy=(0.5, 100), fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="gray"))

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "fig3_similarity_threshold_sweep.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {OUTPUT_DIR / 'fig3_similarity_threshold_sweep.png'}")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating figures...")
    fig1_p0_phase_transition()
    fig2_parameter_importance()
    fig3_similarity_threshold_sweep()
    print("Done.")
