"""Generate manuscript figures for BEACON.

Figures:
1. Reliability diagram (calibration plot)
2. Evidence decomposition waterfall for sample cases
3. Per-destination-group accuracy bar chart

Usage:
    python -m src.validation.generate_figures
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from src.inference.naive_bayes import TravellerFeverModel
from src.validation.benchmark import evaluate_model, load_validation_cases
from src.validation.replicate_kabisa import KABISAReplica
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Use non-interactive backend for headless rendering
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def fig_reliability_diagram(results: list, output_path: Path) -> None:
    """Figure 1: Reliability diagram (calibration plot)."""
    # Bin predicted probabilities and compute observed frequency
    probs = [r.model_top_1_prob for r in results]
    correct = [1.0 if r.top_1_correct else 0.0 for r in results]

    n_bins = 10
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_centers = []
    observed_freqs = []
    bin_counts = []

    for i in range(n_bins):
        mask = [(bin_edges[i] <= p < bin_edges[i + 1]) for p in probs]
        n_in_bin = sum(mask)
        if n_in_bin >= 2:
            bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
            obs = np.mean([c for c, m in zip(correct, mask) if m])
            observed_freqs.append(obs)
            bin_counts.append(n_in_bin)

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect calibration")
    ax.scatter(bin_centers, observed_freqs, s=[n * 8 for n in bin_counts],
               alpha=0.7, color="#2196F3", edgecolors="black", linewidths=0.5,
               label="BEACON")
    ax.set_xlabel("Predicted probability (top-1 diagnosis)", fontsize=12)
    ax.set_ylabel("Observed frequency of correct diagnosis", fontsize=12)
    ax.set_title("Reliability Diagram", fontsize=14)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(loc="lower right")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved reliability diagram to {output_path}")


def fig_evidence_decomposition(model: TravellerFeverModel, output_path: Path) -> None:
    """Figure 2: Evidence decomposition waterfall for a sample case."""
    # Case: febrile traveller from SE Asia with rash + retro-orbital pain + mosquito
    result = model.diagnose(
        regions=["southeast_asia"],
        symptoms={
            "fever": True, "rash": True, "arthralgia_myalgia": True,
            "jaundice": False, "haemorrhagic_signs": False,
            "gi_symptoms": False, "respiratory_symptoms": False,
            "neurological_symptoms": False, "productive_cough": False,
            "retro_orbital_pain": True, "small_joint_polyarthralgia": False,
        },
        exposures={"mosquito": True},
        incubation_days=6,
    )

    top5 = result.diagnoses[:5]
    dx_names = [d.diagnosis.replace("_", " ").title()[:25] for d in top5]
    priors = [d.log_prior for d in top5]
    symptoms = [d.log_symptom_likelihood for d in top5]
    exposures = [d.log_exposure_likelihood for d in top5]
    incubations = [d.log_incubation_likelihood for d in top5]

    x = np.arange(len(dx_names))
    width = 0.2

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    ax.bar(x - 1.5 * width, priors, width, label="Prior", color="#4CAF50", alpha=0.8)
    ax.bar(x - 0.5 * width, symptoms, width, label="Symptoms", color="#2196F3", alpha=0.8)
    ax.bar(x + 0.5 * width, exposures, width, label="Exposures", color="#FF9800", alpha=0.8)
    ax.bar(x + 1.5 * width, incubations, width, label="Incubation", color="#9C27B0", alpha=0.8)

    ax.set_xlabel("Diagnosis", fontsize=12)
    ax.set_ylabel("Log-evidence contribution", fontsize=12)
    ax.set_title("Evidence Decomposition — SE Asia, fever + rash + retro-orbital pain + mosquito, 6d", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(dx_names, rotation=20, ha="right", fontsize=9)
    ax.legend(loc="upper right")
    ax.axhline(y=0, color="black", linewidth=0.5)

    # Add posterior probabilities as text
    for i, d in enumerate(top5):
        ax.text(i, max(priors[i], symptoms[i], exposures[i], incubations[i]) + 0.3,
                f"P={d.posterior:.1%}", ha="center", fontsize=8, fontweight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved evidence decomposition to {output_path}")


def fig_destination_accuracy(results: list, cases: list, output_path: Path) -> None:
    """Figure 3: Per-destination-group Top-1 and Top-5 accuracy."""
    region_data: dict[str, dict] = {}
    for r, c in zip(results, cases):
        for reg in c.regions:
            if reg not in region_data:
                region_data[reg] = {"top1": [], "top5": []}
            region_data[reg]["top1"].append(r.top_1_correct)
            region_data[reg]["top5"].append(r.top_5_correct)

    # Sort by N descending
    sorted_regions = sorted(region_data.keys(), key=lambda r: -len(region_data[r]["top1"]))
    # Filter to regions with >=3 cases
    sorted_regions = [r for r in sorted_regions if len(region_data[r]["top1"]) >= 3]

    names = [r.replace("_", " ").title()[:20] for r in sorted_regions]
    top1_vals = [np.mean(region_data[r]["top1"]) for r in sorted_regions]
    top5_vals = [np.mean(region_data[r]["top5"]) for r in sorted_regions]
    ns = [len(region_data[r]["top1"]) for r in sorted_regions]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    bars1 = ax.bar(x - width / 2, [v * 100 for v in top1_vals], width,
                   label="Top-1", color="#2196F3", alpha=0.8)
    bars2 = ax.bar(x + width / 2, [v * 100 for v in top5_vals], width,
                   label="Top-5", color="#4CAF50", alpha=0.8)

    ax.set_xlabel("Destination region", fontsize=12)
    ax.set_ylabel("Accuracy (%)", fontsize=12)
    ax.set_title("BEACON Accuracy by Destination Region", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\n(n={ns[i]})" for i, n in enumerate(names)],
                       rotation=30, ha="right", fontsize=9)
    ax.set_ylim(0, 105)
    ax.axhline(y=70, color="red", linewidth=1, linestyle="--", alpha=0.5, label="70% threshold")
    ax.legend(loc="lower right")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved destination accuracy to {output_path}")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"

    model = TravellerFeverModel.from_yaml(
        priors_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )
    kabisa = KABISAReplica()

    val_path = PROCESSED_DIR / "validation_cases_combined.yaml"
    cases = load_validation_cases(val_path)
    results = evaluate_model(model, kabisa, cases)

    fig_dir = OUTPUTS_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("Generating manuscript figures...")
    fig_reliability_diagram(results, fig_dir / "fig1_reliability_diagram.png")
    fig_evidence_decomposition(model, fig_dir / "fig2_evidence_decomposition.png")
    fig_destination_accuracy(results, cases, fig_dir / "fig3_destination_accuracy.png")
    print("Done.")


if __name__ == "__main__":
    main()
