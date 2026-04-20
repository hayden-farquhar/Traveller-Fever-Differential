"""Decision curve analysis for key diagnoses.

Computes net clinical benefit at varying threshold probabilities.
For each disease, compares:
- Model: test if posterior > threshold
- Test-all: always test (sensitivity = 1, FP cost)
- Test-none: never test (sensitivity = 0, no FP cost)

Net benefit = (TP/N) - (FP/N) × (threshold / (1 - threshold))

For malaria (high miss cost), even low thresholds are clinically useful.
For URTI (low miss cost), higher thresholds are appropriate.

Usage:
    python -m src.validation.decision_curve
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml

from src.inference.naive_bayes import TravellerFeverModel
from src.validation.extract_case_series import ValidationCase
from src.validation.benchmark import load_validation_cases
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Diseases to analyse (clinically important for decision-making)
TARGET_DISEASES = [
    "malaria_falciparum",
    "malaria_vivax",
    "dengue",
    "enteric_fever",
    "chikungunya",
    "rickettsial_infection",
    "measles",
    "leptospirosis",
]

# Threshold grid
THRESHOLDS = np.arange(0.01, 0.95, 0.01)


def compute_net_benefit(
    model: TravellerFeverModel,
    cases: list[ValidationCase],
    target_dx: str,
    threshold: float,
) -> tuple[float, float, float]:
    """Compute net benefit at a given threshold for a target diagnosis.

    Returns (model_nb, test_all_nb, test_none_nb).
    """
    n = len(cases)
    if n == 0:
        return 0.0, 0.0, 0.0

    # Count true positives and true disease prevalence
    n_positive = sum(1 for c in cases if c.final_diagnosis == target_dx)
    prevalence = n_positive / n

    # Model predictions
    tp = 0
    fp = 0
    for case in cases:
        result = model.diagnose(
            regions=case.regions,
            symptoms=case.symptoms,
            exposures=case.exposures,
            incubation_days=case.incubation_days,
        )
        # Find posterior for target diagnosis
        target_posterior = 0.0
        for d in result.diagnoses:
            if d.diagnosis == target_dx:
                target_posterior = d.posterior
                break

        predicted_positive = target_posterior >= threshold
        actually_positive = case.final_diagnosis == target_dx

        if predicted_positive and actually_positive:
            tp += 1
        elif predicted_positive and not actually_positive:
            fp += 1

    # Net benefit for model
    weight = threshold / (1 - threshold) if threshold < 1 else float("inf")
    model_nb = (tp / n) - (fp / n) * weight

    # Test-all: every case is "positive" → TP = n_positive, FP = n - n_positive
    test_all_nb = prevalence - (1 - prevalence) * weight

    # Test-none: 0
    test_none_nb = 0.0

    return model_nb, test_all_nb, test_none_nb


def run_decision_curve(
    model: TravellerFeverModel,
    cases: list[ValidationCase],
) -> dict[str, list[dict]]:
    """Run DCA for all target diseases."""
    results = {}

    for dx in TARGET_DISEASES:
        n_positive = sum(1 for c in cases if c.final_diagnosis == dx)
        if n_positive == 0:
            logger.info("Skipping %s (no positive cases in validation set)", dx)
            continue

        curves = []
        for t in THRESHOLDS:
            model_nb, test_all_nb, test_none_nb = compute_net_benefit(
                model, cases, dx, float(t)
            )
            curves.append({
                "threshold": round(float(t), 3),
                "model_net_benefit": round(model_nb, 4),
                "test_all_net_benefit": round(test_all_nb, 4),
                "test_none_net_benefit": 0.0,
            })
        results[dx] = curves

    return results


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"
    val_path = PROCESSED_DIR / "validation_cases.yaml"

    if not val_path.exists():
        print("Run extract_case_series.py first")
        return

    model = TravellerFeverModel.from_yaml(
        priors_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )
    cases = load_validation_cases(val_path)

    print("Running decision curve analysis...")
    results = run_decision_curve(model, cases)

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "decision_curve.yaml", "w") as f:
        yaml.dump({"decision_curve_analysis": results}, f,
                  default_flow_style=False, sort_keys=False)

    # Print summary: for each disease, the threshold range where model beats test-all
    print(f"\n{'='*70}")
    print("DECISION CURVE ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print(f"{'Disease':<30s} {'Cases':>6s} {'Model useful range':>25s} {'Peak NB':>10s}")
    print("-" * 70)

    for dx, curve in results.items():
        n_pos = sum(1 for c in cases if c.final_diagnosis == dx)

        # Find threshold range where model NB > max(test-all, 0)
        useful_thresholds = []
        peak_nb = -999
        for point in curve:
            best_default = max(point["test_all_net_benefit"], 0)
            if point["model_net_benefit"] > best_default:
                useful_thresholds.append(point["threshold"])
            if point["model_net_benefit"] > peak_nb:
                peak_nb = point["model_net_benefit"]

        if useful_thresholds:
            range_str = f"{min(useful_thresholds):.0%}–{max(useful_thresholds):.0%}"
        else:
            range_str = "none"

        print(f"{dx:<30s} {n_pos:>6d} {range_str:>25s} {peak_nb:>10.3f}")

    print("-" * 70)
    print("'Model useful range': thresholds where model NB > test-all and test-none")
    print(f"\nSaved to {output_dir / 'decision_curve.yaml'}")


if __name__ == "__main__":
    main()
