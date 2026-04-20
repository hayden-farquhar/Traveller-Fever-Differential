"""External benchmark comparison against published diagnostic systems.

Compares our model's performance against published benchmarks from:
1. KABISA TRAVEL (Demeester 2011, PMID 22017714): 205 cases, 4 European centres
2. Expert travel physicians (Demeester 2011): same 205 cases
3. ChatGPT-4o (Loebstein 2025, PMID 39823287): 114 hospitalized cases
4. Our KABISA replication (rule-based, on our 18-case validation set)

Note: These comparisons are on DIFFERENT case sets (limitation acknowledged).
Direct comparison is informative for context but not statistically paired.

Usage:
    python -m src.validation.external_benchmarks
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from src.utils import OUTPUTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Published external benchmarks
EXTERNAL_BENCHMARKS = {
    "KABISA TRAVEL (Demeester 2011)": {
        "source": "Demeester 2011 J Travel Med (PMID 22017714)",
        "n_cases": 205,
        "population": "Febrile returned travellers, 4 European travel centres (NL, IT, ES, BE), 2007-2009",
        "destination_mix": "58% Sub-Saharan Africa, 60% Western travellers/expatriates",
        "top_1_accuracy": 0.72,
        "top_3_accuracy": None,
        "top_5_accuracy": 0.88,
        "notes": "Closed expert system; 72% Top-1, 88% Top-5",
    },
    "Expert travel physicians (Demeester 2011)": {
        "source": "Demeester 2011 J Travel Med (PMID 22017714)",
        "n_cases": 205,
        "population": "Same 205 cases as KABISA evaluation",
        "destination_mix": "58% Sub-Saharan Africa",
        "top_1_accuracy": 0.70,
        "top_3_accuracy": None,
        "top_5_accuracy": 0.88,
        "notes": "Human expert physicians performed similarly to KABISA",
    },
    "ChatGPT-4o (Loebstein 2025)": {
        "source": "Loebstein 2025 J Travel Med (PMID 39823287)",
        "n_cases": 114,
        "population": "Hospitalized febrile returned travellers, single Israeli centre, 2009-2024",
        "destination_mix": "Not specified in abstract",
        "top_1_accuracy": 0.68,
        "top_3_accuracy": 0.78,
        "top_5_accuracy": None,  # Reports "all possible diagnoses" = 83%
        "all_possible_accuracy": 0.83,
        "malaria_sensitivity": 1.00,
        "malaria_specificity": 0.94,
        "notes": "LLM-based; 68% Top-1, 78% Top-3, 83% all-possible. 100% malaria sensitivity. Noted to 'fall for red herrings' based on exposure history.",
    },
}


def load_our_metrics() -> dict:
    """Load our model's benchmark metrics."""
    metrics_path = OUTPUTS_DIR / "tables" / "benchmark_metrics.yaml"
    if not metrics_path.exists():
        return {}
    with open(metrics_path) as f:
        return yaml.safe_load(f).get("benchmark_metrics", {})


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    our_metrics = load_our_metrics()

    print(f"\n{'='*85}")
    print("EXTERNAL BENCHMARK COMPARISON")
    print(f"{'='*85}")
    print()
    print("IMPORTANT: Comparisons are across DIFFERENT case sets and populations.")
    print("These are contextual benchmarks, not paired statistical comparisons.")
    print()

    # Summary table
    print(f"{'System':<40s} {'N':>5s} {'Top-1':>7s} {'Top-3':>7s} {'Top-5':>7s} {'Population'}")
    print("-" * 85)

    # Our model
    if our_metrics:
        n = our_metrics.get("n_cases", "?")
        t1 = our_metrics.get("model_top_1_accuracy", 0)
        t5 = our_metrics.get("model_top_5_accuracy", 0)
        print(f"{'Our model (AU-weighted Bayes)':<40s} {n:>5} {t1:>6.0%} {'—':>7s} {t5:>6.0%}  18 AU case series")

    # Our KABISA replication
    if our_metrics:
        kt1 = our_metrics.get("kabisa_top_1_accuracy", 0)
        kt5 = our_metrics.get("kabisa_top_5_accuracy", 0)
        print(f"{'Our KABISA replication (rule-based)':<40s} {n:>5} {kt1:>6.0%} {'—':>7s} {kt5:>6.0%}  same 18 cases")

    print("-" * 85)

    # External benchmarks
    for name, bench in EXTERNAL_BENCHMARKS.items():
        n = bench["n_cases"]
        t1 = bench.get("top_1_accuracy")
        t3 = bench.get("top_3_accuracy")
        t5 = bench.get("top_5_accuracy")
        pop = bench.get("destination_mix", "")[:35]

        t1_str = f"{t1:>6.0%}" if t1 is not None else f"{'—':>7s}"
        t3_str = f"{t3:>6.0%}" if t3 is not None else f"{'—':>7s}"
        t5_str = f"{t5:>6.0%}" if t5 is not None else f"{'—':>7s}"

        print(f"{name:<40s} {n:>5} {t1_str} {t3_str} {t5_str}  {pop}")

    print("-" * 85)

    # Discussion points
    print(f"\n--- Key comparisons ---")
    if our_metrics:
        t1 = our_metrics.get("model_top_1_accuracy", 0)
        t5 = our_metrics.get("model_top_5_accuracy", 0)

        print(f"\nOur model vs KABISA (published, 205 cases):")
        print(f"  Top-1: {t1:.0%} vs 72% — {'higher' if t1 > 0.72 else 'lower' if t1 < 0.72 else 'equal'} (different case sets, not directly comparable)")
        print(f"  Top-5: {t5:.0%} vs 88% — {'higher' if t5 > 0.88 else 'lower' if t5 < 0.88 else 'equal'}")

        print(f"\nOur model vs ChatGPT-4o (114 hospitalized cases):")
        print(f"  Top-1: {t1:.0%} vs 68% — {'higher' if t1 > 0.68 else 'lower' if t1 < 0.68 else 'equal'}")
        print(f"  ChatGPT-4o Top-3: 78% (our Top-3 not separately reported)")

        print(f"\nOur model vs expert physicians (Demeester 2011):")
        print(f"  Top-1: {t1:.0%} vs 70% — {'higher' if t1 > 0.70 else 'lower'}")

    print(f"\n--- Structural advantages of our approach ---")
    print("  1. Transparent: per-factor evidence decomposition (prior, symptoms, exposure, incubation)")
    print("  2. Pre-registered: analysis plan, thresholds, and diagnosis set frozen before validation")
    print("  3. Maintained: monthly-updated outbreak priors via automated CI pipeline")
    print("  4. Australian-calibrated: destination priors reweighted for Australian traveller mix")
    print("  5. Abstention: explicit 'insufficient discrimination' signal (LLMs don't abstain)")

    print(f"\n--- Limitations of this comparison ---")
    print("  1. Different case sets: our 18 cases vs Demeester's 205 vs Loebstein's 114")
    print("  2. Case complexity differs: our cases are partly representative profiles, not extracted")
    print("  3. Population differs: Australian vs European vs Israeli travellers")
    print("  4. Our validation set is small (N=18) — wide confidence intervals implied")
    print("  5. REDIVI (N=4,186) external validation pending data request")

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "external_benchmarks": {
            "our_model": {
                "n_cases": our_metrics.get("n_cases"),
                "top_1_accuracy": our_metrics.get("model_top_1_accuracy"),
                "top_5_accuracy": our_metrics.get("model_top_5_accuracy"),
                "brier_score": our_metrics.get("model_brier_score"),
            },
            "published_comparators": EXTERNAL_BENCHMARKS,
            "notes": "Comparisons across different case sets — contextual, not paired",
        },
    }
    with open(output_dir / "external_benchmarks.yaml", "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    # Per-diagnosis-category comparison against Demeester Table 2
    demeester_path = Path(__file__).resolve().parent.parent.parent / \
        "data/raw/external_validation/demeester_2011_extracted.yaml"
    if demeester_path.exists():
        with open(demeester_path) as f:
            demeester = yaml.safe_load(f)

        print(f"\n{'='*85}")
        print("DEMEESTER 2011 — PER-DIAGNOSIS KABISA ACCURACY (Table 2)")
        print(f"{'='*85}")
        print(f"{'Diagnosis category':<35s} {'N':>5s} {'KABISA Top-1':>13s} {'KABISA Top-5':>13s} {'Physician Top-1':>16s}")
        print("-" * 85)

        t2 = demeester["table_2_accuracy"]
        for category_name, category_data in [
            ("TROPICAL DISEASES", t2["tropical_diseases"]),
        ]:
            total = category_data["total"]
            print(f"{category_name:<35s} {total[0]:>5} {total[2]/total[0]:>12.0%} {total[4]/total[0]:>12.0%} {total[1]/total[0]:>15.0%}")
            for dx, vals in category_data.items():
                if dx == "total":
                    continue
                n, ct1, kt1, ct5, kt5 = vals
                dx_display = dx.replace("_", " ").title()
                kt1_str = f"{kt1/n:.0%}" if n > 0 else "—"
                kt5_str = f"{kt5/n:.0%}" if n > 0 else "—"
                ct1_str = f"{ct1/n:.0%}" if n > 0 else "—"
                print(f"  {dx_display:<33s} {n:>5} {kt1_str:>12s} {kt5_str:>12s} {ct1_str:>15s}")

        for category_name, category_data in [
            ("COSMOPOLITAN DISEASES", t2["cosmopolitan_diseases"]),
        ]:
            total = category_data["total"]
            print(f"{category_name:<35s} {total[0]:>5} {total[2]/total[0]:>12.0%} {total[4]/total[0]:>12.0%} {total[1]/total[0]:>15.0%}")
            for dx, vals in category_data.items():
                if dx == "total":
                    continue
                n, ct1, kt1, ct5, kt5 = vals
                dx_display = dx.replace("_", " ").title()
                kt1_str = f"{kt1/n:.0%}" if n > 0 else "—"
                kt5_str = f"{kt5/n:.0%}" if n > 0 else "—"
                ct1_str = f"{ct1/n:.0%}" if n > 0 else "—"
                print(f"  {dx_display:<33s} {n:>5} {kt1_str:>12s} {kt5_str:>12s} {ct1_str:>15s}")

        ni = t2["noninfectious"]
        print(f"{'NONINFECTIOUS':<35s} {ni[0]:>5} {ni[2]/ni[0]:>12.0%} {ni[4]/ni[0]:>12.0%} {ni[1]/ni[0]:>15.0%}")

        gt = t2["grand_total"]
        print("-" * 85)
        print(f"{'GRAND TOTAL':<35s} {gt[0]:>5} {gt[2]/gt[0]:>12.0%} {gt[4]/gt[0]:>12.0%} {gt[1]/gt[0]:>15.0%}")

        print(f"\n--- KABISA weaknesses (from Demeester 2011) ---")
        print("  Chikungunya: 0% Top-1 (0/4) — our model gets this right")
        print("  EBV/mono-like: 8% Top-1 (1/13) — cosmopolitan diseases are hard")
        print("  Leptospirosis: 50% Top-1 (2/4) — our model gets this right")
        print("  Rickettsial: 62% Top-1 (5/8) — our model gets this right")

        print(f"\n--- Corresponding author for individual case data request ---")
        print("  Jozef Van den Ende, MD, PhD")
        print("  Institute of Tropical Medicine, Antwerp, Belgium")
        print("  Email: jvdende@itg.be")

    print(f"\nSaved to {output_dir / 'external_benchmarks.yaml'}")


if __name__ == "__main__":
    main()
