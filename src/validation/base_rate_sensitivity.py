"""Base-rate sensitivity analysis for O'Brien 2001 symptom denominators.

Tests model robustness to perturbation of the per-symptom base rates
(P(symptom | febrile returned traveller)) used as denominators in the
likelihood-ratio framework. The base rates are derived from O'Brien 2001
(Clin Infect Dis 33:603-9, N=232 Royal Melbourne Hospital, 1997-1999),
which is now ~25 years old. The Australian destination mix has shifted
since then, so the overall mix of symptoms among febrile returned travellers
may have changed (even if disease-specific symptom frequencies are stable).

This analysis quantifies how much performance depends on the exact O'Brien
values vs how much is structural.

Method:
- For each of 1,000 iterations:
  - Perturb every base rate by a random factor in [1-pct, 1+pct]
  - Clamp to [0.01, 0.99]
  - Run the full validation set evaluation with perturbed base rates
  - Record Top-1, Top-5, Brier
- Tested at three perturbation magnitudes: ±20%, ±40%, ±50%
- ±50% covers a plausible upper-bound shift in symptom-mix prevalence
  given travel-pattern changes between 1997-1999 and 2024.

Usage:
    python -m src.validation.base_rate_sensitivity
"""

from __future__ import annotations

import copy
import logging
import random

import numpy as np
import yaml

from src.inference import naive_bayes as nb
from src.inference.naive_bayes import (
    SYMPTOM_BASE_RATES,
    TravellerFeverModel,
)
from src.validation.benchmark import compute_metrics, evaluate_model, load_validation_cases
from src.validation.replicate_kabisa import KABISAReplica
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

N_ITERATIONS = 1000
PERTURBATION_RANGES = [0.20, 0.40, 0.50]  # ±20%, ±40%, ±50%


def perturb_base_rates(
    rng: random.Random,
    original: dict[str, float],
    perturbation: float,
) -> dict[str, float]:
    """Return a perturbed copy of the symptom base rates."""
    perturbed = {}
    for symptom, rate in original.items():
        factor = 1.0 + rng.uniform(-perturbation, perturbation)
        new_rate = rate * factor
        new_rate = max(0.01, min(0.99, new_rate))
        perturbed[symptom] = new_rate
    return perturbed


def run_base_rate_perturbation(
    model: TravellerFeverModel,
    cases: list,
    kabisa: KABISAReplica,
    perturbation: float,
    n_iter: int = N_ITERATIONS,
    seed: int = 1234,
) -> dict:
    """Run base-rate perturbation analysis at a single magnitude."""
    rng = random.Random(seed)
    original = copy.deepcopy(SYMPTOM_BASE_RATES)

    top1_scores = []
    top5_scores = []
    brier_scores = []

    try:
        for i in range(n_iter):
            if (i + 1) % 100 == 0:
                logger.info(f"  ±{perturbation*100:.0f}%: iteration {i+1}/{n_iter}")

            # Patch module-level dict in place
            perturbed = perturb_base_rates(rng, original, perturbation)
            nb.SYMPTOM_BASE_RATES.clear()
            nb.SYMPTOM_BASE_RATES.update(perturbed)

            results = evaluate_model(model, kabisa, cases)
            metrics = compute_metrics(results)

            top1_scores.append(metrics["model_top_1_accuracy"])
            top5_scores.append(metrics["model_top_5_accuracy"])
            brier_scores.append(metrics["model_brier_score"])
    finally:
        # Always restore original base rates
        nb.SYMPTOM_BASE_RATES.clear()
        nb.SYMPTOM_BASE_RATES.update(original)

    return {
        "perturbation_range": f"+/-{perturbation*100:.0f}%",
        "perturbation_pct": perturbation,
        "n_iterations": n_iter,
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
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

    # Baseline metrics (with original O'Brien base rates)
    baseline_results = evaluate_model(model, kabisa, cases)
    baseline = compute_metrics(baseline_results)

    print(f"\n{'='*70}")
    print("BASE-RATE SENSITIVITY ANALYSIS (O'Brien 2001 denominators)")
    print(f"{'='*70}")
    print(f"Validation set: N={len(cases)}")
    print(f"Iterations per perturbation: {N_ITERATIONS}")
    print(f"\nBaseline (O'Brien 2001 base rates, unperturbed):")
    print(f"  Top-1: {baseline['model_top_1_accuracy']:.1%}")
    print(f"  Top-5: {baseline['model_top_5_accuracy']:.1%}")
    print(f"  Brier: {baseline['model_brier_score']:.4f}")

    all_results = {
        "baseline": {
            "top_1": round(float(baseline['model_top_1_accuracy']), 4),
            "top_5": round(float(baseline['model_top_5_accuracy']), 4),
            "brier": round(float(baseline['model_brier_score']), 4),
            "obrien_2001_base_rates": dict(SYMPTOM_BASE_RATES),
        },
        "perturbations": [],
    }

    for pct in PERTURBATION_RANGES:
        print(f"\n--- Running ±{pct*100:.0f}% base-rate perturbation, {N_ITERATIONS} iterations ---")
        result = run_base_rate_perturbation(model, cases, kabisa, pct, N_ITERATIONS)
        all_results["perturbations"].append(result)

        print(f"  Top-1: {result['top_1']['mean']:.1%} +/- {result['top_1']['std']:.1%}")
        print(f"    95% range: {result['top_1']['ci_2_5']:.1%} - {result['top_1']['ci_97_5']:.1%}")
        print(f"    Min-Max:   {result['top_1']['min']:.1%} - {result['top_1']['max']:.1%}")
        print(f"    Delta from baseline: {result['top_1']['mean'] - baseline['model_top_1_accuracy']:+.1%}")
        print(f"  Top-5: {result['top_5']['mean']:.1%} +/- {result['top_5']['std']:.1%}")
        print(f"    95% range: {result['top_5']['ci_2_5']:.1%} - {result['top_5']['ci_97_5']:.1%}")
        print(f"    Min-Max:   {result['top_5']['min']:.1%} - {result['top_5']['max']:.1%}")

        top1_range = result['top_1']['ci_97_5'] - result['top_1']['ci_2_5']
        top5_range = result['top_5']['ci_97_5'] - result['top_5']['ci_2_5']
        print(f"\n  Robustness verdict at +/-{pct*100:.0f}%:")
        if top1_range < 0.10:
            print(f"    Top-1 95% range = {top1_range:.1%} -> ROBUST (< 10pp)")
        elif top1_range < 0.15:
            print(f"    Top-1 95% range = {top1_range:.1%} -> MODERATE (10-15pp)")
        else:
            print(f"    Top-1 95% range = {top1_range:.1%} -> FRAGILE (> 15pp)")
        if result['top_5']['min'] >= 0.70:
            print(f"    Top-5 minimum {result['top_5']['min']:.1%} >= 70% -> hypothesis ROBUST")
        else:
            print(f"    Top-5 minimum {result['top_5']['min']:.1%} < 70% -> hypothesis FRAGILE")

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "base_rate_sensitivity.yaml"
    with open(out_path, "w") as f:
        yaml.safe_dump(all_results, f, sort_keys=False, default_flow_style=False)
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
