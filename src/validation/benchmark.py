"""Benchmarking pipeline for the traveller fever differential model.

Computes:
- Top-1 accuracy (proportion where highest-ranked diagnosis is correct)
- Top-5 accuracy (proportion where true diagnosis is in top-5)
- Calibration (reliability diagram + Brier score)
- Abstention rate and appropriateness
- KABISA replication comparison

Usage:
    python -m src.validation.benchmark
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from src.inference.naive_bayes import TravellerFeverModel
from src.validation.extract_case_series import ValidationCase
from src.validation.replicate_kabisa import KABISAReplica
from src.utils import CLINICAL_DIR, PROCESSED_DIR, OUTPUTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)


@dataclass
class CaseResult:
    """Result of evaluating a single case."""
    case_id: str
    true_diagnosis: str
    model_top_1: str
    model_top_5: list[str]
    model_top_1_prob: float
    top_1_correct: bool
    top_5_correct: bool
    abstained: bool
    kabisa_top_1: str
    kabisa_top_5: list[str]
    kabisa_top_1_correct: bool
    kabisa_top_5_correct: bool


def load_validation_cases(path: Path) -> list[ValidationCase]:
    """Load validation cases from YAML."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    cases = []
    for c in raw["cases"]:
        cases.append(ValidationCase(**c))
    return cases


def evaluate_model(
    model: TravellerFeverModel,
    kabisa: KABISAReplica,
    cases: list[ValidationCase],
) -> list[CaseResult]:
    """Evaluate both models on the validation case series."""
    results = []

    for case in cases:
        # Run our model
        model_result = model.diagnose(
            regions=case.regions,
            symptoms=case.symptoms,
            exposures=case.exposures,
            incubation_days=case.incubation_days,
        )

        model_top_1 = model_result.diagnoses[0].diagnosis
        model_top_5 = [d.diagnosis for d in model_result.top_n(5)]
        model_top_1_prob = model_result.diagnoses[0].posterior

        # Run KABISA replication
        region = case.regions[0] if case.regions else ""
        kabisa_result = kabisa.diagnose(region, case.symptoms)

        results.append(CaseResult(
            case_id=case.case_id,
            true_diagnosis=case.final_diagnosis,
            model_top_1=model_top_1,
            model_top_5=model_top_5,
            model_top_1_prob=model_top_1_prob,
            top_1_correct=(model_top_1 == case.final_diagnosis),
            top_5_correct=(case.final_diagnosis in model_top_5),
            abstained=model_result.abstain,
            kabisa_top_1=kabisa_result.top_1,
            kabisa_top_5=kabisa_result.top_5,
            kabisa_top_1_correct=(kabisa_result.top_1 == case.final_diagnosis),
            kabisa_top_5_correct=(case.final_diagnosis in kabisa_result.top_5),
        ))

    return results


def compute_metrics(results: list[CaseResult]) -> dict[str, float]:
    """Compute aggregate benchmark metrics."""
    n = len(results)
    if n == 0:
        return {}

    # Our model
    top_1_acc = sum(r.top_1_correct for r in results) / n
    top_5_acc = sum(r.top_5_correct for r in results) / n
    abstention_rate = sum(r.abstained for r in results) / n

    # Abstention appropriateness: among abstained cases, what fraction
    # had a true diagnosis NOT in the model's top-5?
    abstained_cases = [r for r in results if r.abstained]
    if abstained_cases:
        abstention_appropriate = sum(
            not r.top_5_correct for r in abstained_cases
        ) / len(abstained_cases)
    else:
        abstention_appropriate = float("nan")

    # Brier score (for top-1 probability calibration)
    brier = sum(
        (r.model_top_1_prob - (1.0 if r.top_1_correct else 0.0)) ** 2
        for r in results
    ) / n

    # KABISA replication
    kabisa_top_1 = sum(r.kabisa_top_1_correct for r in results) / n
    kabisa_top_5 = sum(r.kabisa_top_5_correct for r in results) / n

    return {
        "n_cases": n,
        "model_top_1_accuracy": round(top_1_acc, 4),
        "model_top_5_accuracy": round(top_5_acc, 4),
        "model_abstention_rate": round(abstention_rate, 4),
        "model_abstention_appropriateness": round(abstention_appropriate, 4)
            if not np.isnan(abstention_appropriate) else None,
        "model_brier_score": round(brier, 4),
        "kabisa_top_1_accuracy": round(kabisa_top_1, 4),
        "kabisa_top_5_accuracy": round(kabisa_top_5, 4),
    }


def save_results(
    results: list[CaseResult],
    metrics: dict[str, float],
    output_dir: Path,
) -> None:
    """Save benchmark results to CSV and metrics to YAML."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Per-case CSV
    csv_path = output_dir / "benchmark_results.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "case_id", "true_diagnosis",
            "model_top1", "model_top1_prob", "model_top1_correct",
            "model_top5", "model_top5_correct",
            "model_abstained",
            "kabisa_top1", "kabisa_top1_correct",
            "kabisa_top5", "kabisa_top5_correct",
        ])
        for r in results:
            writer.writerow([
                r.case_id, r.true_diagnosis,
                r.model_top_1, f"{r.model_top_1_prob:.4f}", r.top_1_correct,
                "|".join(r.model_top_5), r.top_5_correct,
                r.abstained,
                r.kabisa_top_1, r.kabisa_top_1_correct,
                "|".join(r.kabisa_top_5), r.kabisa_top_5_correct,
            ])

    # Aggregate metrics YAML
    metrics_path = output_dir / "benchmark_metrics.yaml"
    with open(metrics_path, "w") as f:
        yaml.dump({"benchmark_metrics": metrics}, f,
                  default_flow_style=False, sort_keys=False)

    logger.info("Saved results to %s", csv_path)
    logger.info("Saved metrics to %s", metrics_path)


def print_report(results: list[CaseResult], metrics: dict) -> None:
    """Print a formatted benchmark report."""
    print("\n" + "=" * 70)
    print("BENCHMARK REPORT")
    print("=" * 70)

    print(f"\nCases evaluated: {metrics['n_cases']}")

    print("\n--- Model Performance ---")
    print(f"  Top-1 accuracy: {metrics['model_top_1_accuracy']:.1%}")
    print(f"  Top-5 accuracy: {metrics['model_top_5_accuracy']:.1%}")
    print(f"  Abstention rate: {metrics['model_abstention_rate']:.1%}")
    if metrics.get("model_abstention_appropriateness") is not None:
        print(f"  Abstention appropriateness: "
              f"{metrics['model_abstention_appropriateness']:.1%}")
    print(f"  Brier score: {metrics['model_brier_score']:.4f}")

    print("\n--- KABISA Replication ---")
    print(f"  Top-1 accuracy: {metrics['kabisa_top_1_accuracy']:.1%}")
    print(f"  Top-5 accuracy: {metrics['kabisa_top_5_accuracy']:.1%}")

    print("\n--- Head-to-Head (Top-1) ---")
    model_wins = sum(r.top_1_correct and not r.kabisa_top_1_correct
                     for r in results)
    kabisa_wins = sum(r.kabisa_top_1_correct and not r.top_1_correct
                      for r in results)
    both_correct = sum(r.top_1_correct and r.kabisa_top_1_correct
                       for r in results)
    both_wrong = sum(not r.top_1_correct and not r.kabisa_top_1_correct
                     for r in results)
    print(f"  Both correct: {both_correct}")
    print(f"  Model only correct: {model_wins}")
    print(f"  KABISA only correct: {kabisa_wins}")
    print(f"  Both wrong: {both_wrong}")

    # Per-case details
    print("\n--- Per-Case Results ---")
    for r in results:
        model_mark = "+" if r.top_1_correct else ("-" if r.top_5_correct else "X")
        kabisa_mark = "+" if r.kabisa_top_1_correct else (
            "-" if r.kabisa_top_5_correct else "X")
        print(f"  {r.case_id:12s}  true={r.true_diagnosis:30s}  "
              f"model={r.model_top_1:30s} [{model_mark}]  "
              f"kabisa={r.kabisa_top_1:20s} [{kabisa_mark}]")

    print("\n  Legend: + = Top-1 correct, - = Top-5 correct, X = missed")
    print("=" * 70)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    # Load model
    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"

    model = TravellerFeverModel.from_yaml(
        priors_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )

    # Load KABISA replication
    kabisa = KABISAReplica()

    # Load validation cases
    val_path = PROCESSED_DIR / "validation_cases.yaml"
    if not val_path.exists():
        print("Run extract_case_series.py first")
        return

    cases = load_validation_cases(val_path)
    logger.info("Loaded %d validation cases", len(cases))

    # Evaluate
    results = evaluate_model(model, kabisa, cases)
    metrics = compute_metrics(results)

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    save_results(results, metrics, output_dir)

    # Report
    print_report(results, metrics)


if __name__ == "__main__":
    main()
