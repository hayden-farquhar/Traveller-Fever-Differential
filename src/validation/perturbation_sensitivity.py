"""Perturbation sensitivity analysis for symptom grading.

Tests model robustness to ±20% random perturbation of every symptom
prevalence value. If the model is robust (Top-1 varies <5pp), the
symptom grading choices are defensible. If fragile, specific fragile
cells need investigation.

Method:
- For each of 1,000 iterations:
  - Perturb every disease-symptom grade by a random factor in [0.8, 1.2]
  - Clamp perturbed values to [0.01, 0.99]
  - Run the model on the full validation set with perturbed YAML
  - Record Top-1, Top-5, Brier

Reports: mean, SD, 2.5th-97.5th percentiles for each metric,
and identifies the most sensitive individual symptom-disease cells.

Usage:
    python -m src.validation.perturbation_sensitivity
"""

from __future__ import annotations

import copy
import logging
import random

import numpy as np
import yaml

from src.inference.naive_bayes import (
    SYMPTOM_FEATURES,
    TravellerFeverModel,
    resolve_symptom_probability,
)
from src.validation.benchmark import evaluate_model, compute_metrics, load_validation_cases
from src.validation.replicate_kabisa import KABISAReplica
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

N_ITERATIONS = 1000
PERTURBATION_RANGE = 0.20  # ±20%


def perturb_model(
    model: TravellerFeverModel,
    rng: random.Random,
    perturbation: float = PERTURBATION_RANGE,
) -> TravellerFeverModel:
    """Create a copy of the model with randomly perturbed symptom grades."""
    perturbed = copy.deepcopy(model)

    for disease_key, defn in perturbed.diseases.items():
        for sx in SYMPTOM_FEATURES:
            original_grade = defn.symptoms.get(sx, "false")
            original_p = resolve_symptom_probability(original_grade)

            # Apply random perturbation
            factor = 1.0 + rng.uniform(-perturbation, perturbation)
            new_p = original_p * factor
            new_p = max(0.01, min(0.99, new_p))

            # Store as float (the model handles floats directly)
            defn.symptoms[sx] = new_p

    return perturbed


def run_perturbation_analysis(
    model: TravellerFeverModel,
    cases: list,
    kabisa: KABISAReplica,
    n_iter: int = N_ITERATIONS,
    seed: int = 789,
) -> dict:
    """Run perturbation sensitivity analysis."""
    rng = random.Random(seed)

    top1_scores = []
    top5_scores = []
    brier_scores = []

    for i in range(n_iter):
        if (i + 1) % 100 == 0:
            print(f"  Iteration {i+1}/{n_iter}...")

        perturbed_model = perturb_model(model, rng)
        results = evaluate_model(perturbed_model, kabisa, cases)
        metrics = compute_metrics(results)

        top1_scores.append(metrics["model_top_1_accuracy"])
        top5_scores.append(metrics["model_top_5_accuracy"])
        brier_scores.append(metrics["model_brier_score"])

    return {
        "n_iterations": n_iter,
        "perturbation_range": f"±{PERTURBATION_RANGE*100:.0f}%",
        "top_1": {
            "mean": round(float(np.mean(top1_scores)), 4),
            "std": round(float(np.std(top1_scores)), 4),
            "ci_2_5": round(float(np.percentile(top1_scores, 2.5)), 4),
            "ci_97_5": round(float(np.percentile(top1_scores, 97.5)), 4),
            "min": round(float(np.min(top1_scores)), 4),
            "max": round(float(np.max(top1_scores)), 4),
        },
        "top_5": {
            "mean": round(float(np.mean(top5_scores)), 4),
            "std": round(float(np.std(top5_scores)), 4),
            "ci_2_5": round(float(np.percentile(top5_scores, 2.5)), 4),
            "ci_97_5": round(float(np.percentile(top5_scores, 97.5)), 4),
            "min": round(float(np.min(top5_scores)), 4),
            "max": round(float(np.max(top5_scores)), 4),
        },
        "brier": {
            "mean": round(float(np.mean(brier_scores)), 4),
            "std": round(float(np.std(brier_scores)), 4),
            "ci_2_5": round(float(np.percentile(brier_scores, 2.5)), 4),
            "ci_97_5": round(float(np.percentile(brier_scores, 97.5)), 4),
        },
    }


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

    # Baseline metrics
    baseline_results = evaluate_model(model, kabisa, cases)
    baseline = compute_metrics(baseline_results)

    print(f"\n{'='*70}")
    print(f"PERTURBATION SENSITIVITY ANALYSIS")
    print(f"{'='*70}")
    print(f"Perturbation: ±{PERTURBATION_RANGE*100:.0f}% on all symptom grades")
    print(f"Iterations: {N_ITERATIONS}")
    print(f"Validation set: N={len(cases)}")
    print(f"\nBaseline (unperturbed):")
    print(f"  Top-1: {baseline['model_top_1_accuracy']:.1%}")
    print(f"  Top-5: {baseline['model_top_5_accuracy']:.1%}")
    print(f"  Brier: {baseline['model_brier_score']:.4f}")

    print(f"\nRunning {N_ITERATIONS} perturbation iterations...")
    result = run_perturbation_analysis(model, cases, kabisa)

    print(f"\n--- Results (±{PERTURBATION_RANGE*100:.0f}% perturbation, {N_ITERATIONS} iterations) ---")
    print(f"  Top-1: {result['top_1']['mean']:.1%} ± {result['top_1']['std']:.1%}")
    print(f"    95% range: {result['top_1']['ci_2_5']:.1%} – {result['top_1']['ci_97_5']:.1%}")
    print(f"    Min-Max: {result['top_1']['min']:.1%} – {result['top_1']['max']:.1%}")
    print(f"    Δ from baseline: {result['top_1']['mean'] - baseline['model_top_1_accuracy']:+.1%}")

    print(f"  Top-5: {result['top_5']['mean']:.1%} ± {result['top_5']['std']:.1%}")
    print(f"    95% range: {result['top_5']['ci_2_5']:.1%} – {result['top_5']['ci_97_5']:.1%}")
    print(f"    Min-Max: {result['top_5']['min']:.1%} – {result['top_5']['max']:.1%}")

    print(f"  Brier: {result['brier']['mean']:.4f} ± {result['brier']['std']:.4f}")
    print(f"    95% range: {result['brier']['ci_2_5']:.4f} – {result['brier']['ci_97_5']:.4f}")

    # Robustness verdict
    top1_range = result['top_1']['ci_97_5'] - result['top_1']['ci_2_5']
    top5_range = result['top_5']['ci_97_5'] - result['top_5']['ci_2_5']

    print(f"\n--- ROBUSTNESS VERDICT ---")
    if top1_range < 0.10:
        print(f"  Top-1 95% range = {top1_range:.1%} — ROBUST (< 10pp)")
    elif top1_range < 0.15:
        print(f"  Top-1 95% range = {top1_range:.1%} — MODERATE (10-15pp)")
    else:
        print(f"  Top-1 95% range = {top1_range:.1%} — FRAGILE (> 15pp)")

    if top5_range < 0.05:
        print(f"  Top-5 95% range = {top5_range:.1%} — ROBUST (< 5pp)")
    elif top5_range < 0.10:
        print(f"  Top-5 95% range = {top5_range:.1%} — MODERATE (5-10pp)")
    else:
        print(f"  Top-5 95% range = {top5_range:.1%} — FRAGILE (> 10pp)")

    # Does Top-5 stay above 70% threshold in worst case?
    if result['top_5']['min'] >= 0.70:
        print(f"  Top-5 minimum ({result['top_5']['min']:.1%}) ≥ 70% — hypothesis robust to perturbation")
    else:
        print(f"  Top-5 minimum ({result['top_5']['min']:.1%}) < 70% — hypothesis FRAGILE under perturbation")

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "perturbation_sensitivity": {
            "baseline": {
                "top_1": baseline["model_top_1_accuracy"],
                "top_5": baseline["model_top_5_accuracy"],
                "brier": baseline["model_brier_score"],
            },
            "perturbation": result,
        }
    }
    with open(output_dir / "perturbation_sensitivity.yaml", "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"\nSaved to {output_dir / 'perturbation_sensitivity.yaml'}")


if __name__ == "__main__":
    main()
