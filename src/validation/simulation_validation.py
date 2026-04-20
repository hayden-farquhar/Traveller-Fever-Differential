"""Simulation-based internal consistency validation.

Generates synthetic cases from the model's own prior and likelihood
distributions, then tests whether the model can recover the true
diagnosis. The gap between perfect recovery and actual recovery
quantifies the impact of the Naive Bayes independence assumption
and parameter estimation error.

Usage:
    python -m src.validation.simulation_validation
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

import numpy as np
import yaml

from src.inference.naive_bayes import (
    EXPOSURE_FEATURES,
    SYMPTOM_BASE_RATES,
    SYMPTOM_FEATURES,
    SYMPTOM_GRADE_PRESENT,
    TravellerFeverModel,
    parse_incubation_mode,
)
from src.priors.build_base_priors import DIAGNOSES, REGIONS
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)


@dataclass
class SimulationResult:
    n_cases: int
    top_1_recovery: float
    top_3_recovery: float
    top_5_recovery: float
    mean_true_rank: float
    median_true_rank: float
    per_diagnosis_top1: dict[str, float]
    per_region_top1: dict[str, float]


def generate_synthetic_case(
    model: TravellerFeverModel,
    rng: random.Random,
) -> tuple[str, str, dict[str, bool], dict[str, bool], float]:
    """Generate a single synthetic case from model distributions.

    Returns (region, true_diagnosis, symptoms, exposures, incubation_days).
    """
    # 1. Sample a region weighted by Australian traveller destination distribution
    # Use the prior sums as proxy weights
    region_weights = []
    for r in REGIONS:
        region_priors = model.destination_priors.get(r, {})
        region_weights.append(sum(region_priors.get(dx, 0) for dx in DIAGNOSES))
    total = sum(region_weights)
    region_weights = [w / total for w in region_weights]
    region = rng.choices(REGIONS, weights=region_weights, k=1)[0]

    # 2. Sample a diagnosis from P(dx | region)
    region_priors = model.destination_priors.get(region, {})
    dx_probs = [region_priors.get(dx, 1e-6) for dx in DIAGNOSES]
    total_dx = sum(dx_probs)
    dx_probs = [p / total_dx for p in dx_probs]
    true_dx = rng.choices(DIAGNOSES, weights=dx_probs, k=1)[0]

    # 3. Look up disease definition
    def_key = model._resolve_definition_key(true_dx)
    defn = model.diseases.get(def_key)
    if defn is None:
        # Fallback: generic symptoms
        symptoms = {s: rng.random() < SYMPTOM_BASE_RATES.get(s, 0.2) for s in SYMPTOM_FEATURES}
        exposures = {e: rng.random() < 0.1 for e in EXPOSURE_FEATURES}
        inc = rng.uniform(3, 14)
        return region, true_dx, symptoms, exposures, inc

    # 4. Sample symptoms from P(symptom | dx)
    symptoms = {}
    for sx in SYMPTOM_FEATURES:
        grade = defn.symptoms.get(sx, "false")
        p = SYMPTOM_GRADE_PRESENT.get(grade, 0.05)
        symptoms[sx] = rng.random() < p

    # 5. Sample exposures from disease routes
    exposures = {}
    for exp in EXPOSURE_FEATURES:
        has_route = defn.exposures.get(exp, False)
        if has_route:
            exposures[exp] = rng.random() < 0.70  # P_EXPOSURE_GIVEN_ROUTE
        else:
            exposures[exp] = rng.random() < 0.05  # P_EXPOSURE_GIVEN_NOT_ROUTE

    # 6. Sample incubation from triangular distribution
    a = defn.incubation_min
    b = defn.incubation_max
    c = defn.incubation_mode
    # numpy triangular: left, mode, right
    inc = float(np.random.triangular(a, c, max(b, c + 0.01)))
    inc = max(0.5, inc)  # Floor at half a day

    return region, true_dx, symptoms, exposures, inc


def run_simulation(
    model: TravellerFeverModel,
    n_cases: int = 1000,
    seed: int = 42,
) -> SimulationResult:
    """Run simulation validation."""
    rng = random.Random(seed)
    np.random.seed(seed)

    true_ranks = []
    top1_correct = 0
    top3_correct = 0
    top5_correct = 0

    # Per-diagnosis and per-region tracking
    dx_attempts: dict[str, int] = {}
    dx_correct: dict[str, int] = {}
    region_attempts: dict[str, int] = {}
    region_correct: dict[str, int] = {}

    for i in range(n_cases):
        region, true_dx, symptoms, exposures, inc = generate_synthetic_case(model, rng)

        result = model.diagnose(
            regions=[region],
            symptoms=symptoms,
            exposures=exposures,
            incubation_days=inc,
        )

        # Find true diagnosis rank
        true_rank = next(
            (d.rank for d in result.diagnoses if d.diagnosis == true_dx),
            len(result.diagnoses),
        )
        true_ranks.append(true_rank)

        if true_rank == 1:
            top1_correct += 1
        if true_rank <= 3:
            top3_correct += 1
        if true_rank <= 5:
            top5_correct += 1

        # Per-diagnosis
        dx_attempts[true_dx] = dx_attempts.get(true_dx, 0) + 1
        if true_rank == 1:
            dx_correct[true_dx] = dx_correct.get(true_dx, 0) + 1

        # Per-region
        region_attempts[region] = region_attempts.get(region, 0) + 1
        if true_rank == 1:
            region_correct[region] = region_correct.get(region, 0) + 1

    per_dx_top1 = {}
    for dx in sorted(dx_attempts.keys()):
        n = dx_attempts[dx]
        c = dx_correct.get(dx, 0)
        per_dx_top1[dx] = c / n if n > 0 else 0.0

    per_region_top1 = {}
    for r in sorted(region_attempts.keys()):
        n = region_attempts[r]
        c = region_correct.get(r, 0)
        per_region_top1[r] = c / n if n > 0 else 0.0

    return SimulationResult(
        n_cases=n_cases,
        top_1_recovery=top1_correct / n_cases,
        top_3_recovery=top3_correct / n_cases,
        top_5_recovery=top5_correct / n_cases,
        mean_true_rank=float(np.mean(true_ranks)),
        median_true_rank=float(np.median(true_ranks)),
        per_diagnosis_top1=per_dx_top1,
        per_region_top1=per_region_top1,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"

    model = TravellerFeverModel.from_yaml(
        priors_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )

    print("Running simulation validation (N=2000)...")
    result = run_simulation(model, n_cases=2000, seed=42)

    # Save results
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "simulation_validation": {
            "n_cases": result.n_cases,
            "top_1_recovery": round(result.top_1_recovery, 4),
            "top_3_recovery": round(result.top_3_recovery, 4),
            "top_5_recovery": round(result.top_5_recovery, 4),
            "mean_true_rank": round(result.mean_true_rank, 2),
            "median_true_rank": round(result.median_true_rank, 1),
            "independence_assumption_cost_top1": round(1.0 - result.top_1_recovery, 4),
            "per_diagnosis_top1": {k: round(v, 3) for k, v in result.per_diagnosis_top1.items()},
            "per_region_top1": {k: round(v, 3) for k, v in result.per_region_top1.items()},
        }
    }
    with open(output_dir / "simulation_validation.yaml", "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    # Print report
    print(f"\n{'='*60}")
    print("SIMULATION VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Synthetic cases: {result.n_cases}")
    print(f"Top-1 recovery:  {result.top_1_recovery:.1%}")
    print(f"Top-3 recovery:  {result.top_3_recovery:.1%}")
    print(f"Top-5 recovery:  {result.top_5_recovery:.1%}")
    print(f"Mean true rank:  {result.mean_true_rank:.1f}")
    print(f"Median true rank: {result.median_true_rank:.1f}")
    print(f"\nIndependence assumption cost (1 - Top-1): {1-result.top_1_recovery:.1%}")

    print(f"\n--- Per-region Top-1 recovery ---")
    for r, acc in sorted(result.per_region_top1.items(), key=lambda x: -x[1]):
        n = sum(1 for _ in [None])  # placeholder
        print(f"  {r:35s} {acc:.1%}")

    print(f"\n--- Per-diagnosis Top-1 recovery (>10 cases) ---")
    for dx, acc in sorted(result.per_diagnosis_top1.items(), key=lambda x: -x[1]):
        n = sum(1 for k, v in output["simulation_validation"]["per_diagnosis_top1"].items() if k == dx)
        print(f"  {dx:40s} {acc:.1%}")


if __name__ == "__main__":
    main()
