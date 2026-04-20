"""Prior ablation study — tests the value of Australian reweighting.

Compares model performance with three prior configurations:
1. Australian-weighted (shrunk) — current model
2. Raw GeoSentinel (no NNDSS reweighting, no shrinkage)
3. Uniform priors (no destination information)

Pre-registered secondary analysis.

Usage:
    python -m src.validation.prior_ablation
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from src.inference.naive_bayes import TravellerFeverModel
from src.priors.build_base_priors import DIAGNOSES, REGIONS
from src.validation.benchmark import (
    compute_metrics,
    evaluate_model,
    load_validation_cases,
    print_report,
)
from src.validation.replicate_kabisa import KABISAReplica
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)


def build_uniform_priors_yaml(output_path: Path) -> None:
    """Create a uniform priors file (equal probability for all diagnoses)."""
    n_dx = len(DIAGNOSES)
    uniform_p = round(1.0 / n_dx, 6)
    priors = {}
    for r in REGIONS:
        priors[r] = {dx: uniform_p for dx in DIAGNOSES}

    data = {
        "metadata": {"description": "Uniform priors (no destination weighting)"},
        "priors": priors,
    }
    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"
    val_path = PROCESSED_DIR / "validation_cases.yaml"

    if not val_path.exists():
        print("Run extract_case_series.py first")
        return

    cases = load_validation_cases(val_path)
    kabisa = KABISAReplica()

    # --- Config 1: Australian-weighted (shrunk) ---
    aus_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not aus_path.exists():
        aus_path = PROCESSED_DIR / "destination_priors.yaml"
    model_aus = TravellerFeverModel.from_yaml(
        aus_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )

    # --- Config 2: Raw GeoSentinel (no NNDSS reweighting) ---
    raw_path = PROCESSED_DIR / "destination_priors.yaml"
    model_raw = TravellerFeverModel.from_yaml(raw_path, defs_path)

    # --- Config 3: Uniform priors ---
    uniform_path = PROCESSED_DIR / "uniform_priors_temp.yaml"
    build_uniform_priors_yaml(uniform_path)
    model_uniform = TravellerFeverModel.from_yaml(uniform_path, defs_path)

    # Evaluate all three
    configs = [
        ("Australian-weighted (shrunk + live)", model_aus),
        ("Raw GeoSentinel (no AU reweight)", model_raw),
        ("Uniform priors (no destination)", model_uniform),
    ]

    all_metrics = {}
    for name, model in configs:
        results = evaluate_model(model, kabisa, cases)
        metrics = compute_metrics(results)
        all_metrics[name] = metrics

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "prior_ablation.yaml", "w") as f:
        yaml.dump({"prior_ablation": all_metrics}, f,
                  default_flow_style=False, sort_keys=False)

    # Print comparison
    print(f"\n{'='*70}")
    print("PRIOR ABLATION STUDY")
    print(f"{'='*70}")
    print(f"{'Configuration':<45s} {'Top-1':>7s} {'Top-5':>7s} {'Brier':>7s}")
    print("-" * 70)
    for name, m in all_metrics.items():
        print(f"{name:<45s} {m['model_top_1_accuracy']:>6.1%} {m['model_top_5_accuracy']:>6.1%} {m['model_brier_score']:>7.4f}")
    print("-" * 70)
    print(f"{'KABISA replication':<45s} {all_metrics[list(all_metrics.keys())[0]]['kabisa_top_1_accuracy']:>6.1%} {all_metrics[list(all_metrics.keys())[0]]['kabisa_top_5_accuracy']:>6.1%}")

    # Compute AU reweighting value
    aus_top5 = all_metrics[list(all_metrics.keys())[0]]["model_top_5_accuracy"]
    raw_top5 = all_metrics[list(all_metrics.keys())[1]]["model_top_5_accuracy"]
    uni_top5 = all_metrics[list(all_metrics.keys())[2]]["model_top_5_accuracy"]
    print(f"\nAustralian reweighting value (Top-5):")
    print(f"  AU-weighted vs raw GeoSentinel: {aus_top5 - raw_top5:+.1%}")
    print(f"  AU-weighted vs uniform:         {aus_top5 - uni_top5:+.1%}")
    print(f"  Raw GeoSentinel vs uniform:     {raw_top5 - uni_top5:+.1%}")

    # Clean up temp file
    uniform_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
