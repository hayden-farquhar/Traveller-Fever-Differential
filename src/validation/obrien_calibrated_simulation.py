"""O'Brien-calibrated population-level simulation.

Generates synthetic cases matching the O'Brien 2001 Australian
proportionate morbidity distribution (Royal Melbourne Hospital,
232 febrile returned travellers) and tests whether the model
recovers the correct diagnosis distribution at population level.

This tests calibration (does the model's output distribution match
the expected Australian disease distribution?) rather than
case-level accuracy.

Usage:
    python -m src.validation.obrien_calibrated_simulation
"""

from __future__ import annotations

import logging
import random

import numpy as np
import yaml

from src.inference.naive_bayes import (
    SYMPTOM_FEATURES,
    SYMPTOM_GRADE_PRESENT,
    EXPOSURE_FEATURES,
    TravellerFeverModel,
    resolve_symptom_probability,
)
from src.priors.build_base_priors import REGIONS
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# O'Brien 2001 Australian proportionate morbidity
# Mapped to our diagnosis keys. Diseases not in our model are excluded
# and proportions renormalised.
OBRIEN_DISTRIBUTION = {
    "malaria_vivax": 0.16,
    "malaria_falciparum": 0.06,
    "dengue": 0.08,
    "enteric_fever": 0.035,
    "hepatitis_a": 0.03,
    "rickettsial_infection": 0.02,
    "acute_bacterial_gastroenteritis": 0.14,
    "influenza": 0.05,
    "community_acquired_pneumonia": 0.06,
    "viral_urti": 0.12,
    "undifferentiated_viral_syndrome": 0.09,
    "uti_pyelonephritis": 0.01,
    "amoebiasis": 0.01,
    "infectious_mononucleosis": 0.005,
    "melioidosis": 0.005,
    "acute_hiv_seroconversion": 0.005,
    "tuberculosis": 0.005,
}

# O'Brien Australian destination distribution
OBRIEN_REGIONS = {
    "southeast_asia": 0.47,       # Asia dominant (47% of 232)
    "oceania": 0.26,              # Pacific (26%)
    "sub_saharan_africa": 0.20,   # Africa (20%)
    "south_central_asia": 0.04,   # small
    "latin_america_caribbean": 0.03,
}


def run_obrien_simulation(
    model: TravellerFeverModel,
    n_cases: int = 500,
    seed: int = 123,
) -> dict:
    """Run O'Brien-calibrated population simulation."""
    rng = random.Random(seed)
    np.random.seed(seed)

    # Normalise distributions
    dx_list = list(OBRIEN_DISTRIBUTION.keys())
    dx_weights = [OBRIEN_DISTRIBUTION[dx] for dx in dx_list]
    total_w = sum(dx_weights)
    dx_weights = [w / total_w for w in dx_weights]

    region_list = list(OBRIEN_REGIONS.keys())
    region_weights = list(OBRIEN_REGIONS.values())

    # Track model predictions
    true_counts: dict[str, int] = {}
    predicted_counts: dict[str, int] = {}
    top1_correct = 0
    top5_correct = 0

    for i in range(n_cases):
        # Sample true diagnosis from O'Brien distribution
        true_dx = rng.choices(dx_list, weights=dx_weights, k=1)[0]
        true_counts[true_dx] = true_counts.get(true_dx, 0) + 1

        # Sample region from O'Brien destination distribution
        region = rng.choices(region_list, weights=region_weights, k=1)[0]

        # Generate symptoms from disease definition
        def_key = model._resolve_definition_key(true_dx)
        defn = model.diseases.get(def_key)

        if defn:
            symptoms = {}
            for sx in SYMPTOM_FEATURES:
                grade = defn.symptoms.get(sx, "false")
                p = resolve_symptom_probability(grade)
                symptoms[sx] = rng.random() < p

            exposures = {}
            for exp in EXPOSURE_FEATURES:
                has_route = defn.exposures.get(exp, False)
                exposures[exp] = rng.random() < (0.70 if has_route else 0.05)

            inc = float(np.random.triangular(
                defn.incubation_min, defn.incubation_mode,
                max(defn.incubation_max, defn.incubation_mode + 0.01)
            ))
        else:
            symptoms = {sx: rng.random() < 0.2 for sx in SYMPTOM_FEATURES}
            exposures = {exp: rng.random() < 0.1 for exp in EXPOSURE_FEATURES}
            inc = rng.uniform(3, 14)

        # Run model
        result = model.diagnose(
            regions=[region], symptoms=symptoms,
            exposures=exposures, incubation_days=inc,
        )

        pred_dx = result.diagnoses[0].diagnosis
        predicted_counts[pred_dx] = predicted_counts.get(pred_dx, 0) + 1

        if pred_dx == true_dx:
            top1_correct += 1
        top5_names = [d.diagnosis for d in result.diagnoses[:5]]
        if true_dx in top5_names:
            top5_correct += 1

    # Compare distributions
    all_dx = sorted(set(list(true_counts.keys()) + list(predicted_counts.keys())))

    return {
        "n_cases": n_cases,
        "top_1_accuracy": round(top1_correct / n_cases, 4),
        "top_5_accuracy": round(top5_correct / n_cases, 4),
        "true_distribution": {dx: true_counts.get(dx, 0) for dx in all_dx},
        "predicted_distribution": {dx: predicted_counts.get(dx, 0) for dx in all_dx},
    }


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

    print("Running O'Brien-calibrated population simulation (N=500)...")
    result = run_obrien_simulation(model, n_cases=500, seed=123)

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "obrien_calibrated_simulation.yaml", "w") as f:
        yaml.dump({"obrien_simulation": result}, f,
                  default_flow_style=False, sort_keys=False)

    print(f"\n{'='*70}")
    print("O'BRIEN-CALIBRATED POPULATION SIMULATION")
    print(f"{'='*70}")
    print(f"Cases: {result['n_cases']}")
    print(f"Top-1 accuracy: {result['top_1_accuracy']:.1%}")
    print(f"Top-5 accuracy: {result['top_5_accuracy']:.1%}")

    print(f"\n{'Diagnosis':<40s} {'True N':>7s} {'Predicted N':>12s} {'Diff':>6s}")
    print("-" * 70)
    for dx in sorted(result["true_distribution"].keys(),
                     key=lambda x: -result["true_distribution"].get(x, 0)):
        t = result["true_distribution"].get(dx, 0)
        p = result["predicted_distribution"].get(dx, 0)
        diff = p - t
        flag = " ✗" if abs(diff) > t * 0.5 and t > 5 else ""
        print(f"{dx:<40s} {t:>7d} {p:>12d} {diff:>+6d}{flag}")

    # Diseases predicted but never true
    phantom = {dx: n for dx, n in result["predicted_distribution"].items()
               if result["true_distribution"].get(dx, 0) == 0 and n > 0}
    if phantom:
        print(f"\nPhantom predictions (predicted but never true):")
        for dx, n in sorted(phantom.items(), key=lambda x: -x[1]):
            print(f"  {dx}: {n}")


if __name__ == "__main__":
    main()
