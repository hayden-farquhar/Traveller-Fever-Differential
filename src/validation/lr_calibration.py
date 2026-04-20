"""Likelihood ratio calibration against published meta-analysis data.

Computes the model's effective likelihood ratios for key symptom-diagnosis
pairs and compares them against published LRs from:
- Hamer 2020 systematic review (PMID 33146395, J Travel Med taaa207)
- Individual disease-specific literature

This validates whether the model's symptom grading produces
clinically plausible discrimination.

Usage:
    python -m src.validation.lr_calibration
"""

from __future__ import annotations

import logging
import math

import yaml

from src.inference.naive_bayes import (
    SYMPTOM_BASE_RATES,
    SYMPTOM_FEATURES,
    SYMPTOM_GRADE_PRESENT,
    TravellerFeverModel,
)
from src.utils import CLINICAL_DIR, OUTPUTS_DIR, PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Published likelihood ratios from Hamer 2020 meta-analysis (PMID 33146395)
# and other disease-specific literature.
# Format: (symptom_or_sign, diagnosis, LR+_published, LR-_published, source)
PUBLISHED_LRS = [
    # From Hamer 2020 Table 2 — malaria predictors
    ("haemorrhagic_signs", "malaria", 3.0, None, "Hamer 2020: thrombocytopenia LR+ 3-11"),
    ("jaundice", "malaria", 5.0, None, "Hamer 2020: hyperbilirubinemia LR+ 5-7"),

    # From Hamer 2020 — rickettsial predictors
    ("rash", "rickettsial_diseases", 5.0, None, "Hamer 2020: skin rash LR+ 5 for rickettsia"),

    # From Bierbrier 2024 — chikungunya
    ("arthralgia_myalgia", "chikungunya", 2.8, None,
     "Bierbrier 2024: arthralgia 98.8% vs base ~40% → LR+ ~2.5"),

    # From Duvignaud 2024 — dengue
    ("haemorrhagic_signs", "dengue", 3.0, None,
     "Duvignaud 2024: petechiae/bleeding ~15% vs base ~5% → LR+ ~3"),

    # Clinical consensus — hepatitis
    ("jaundice", "hepatitis_a", 17.0, None,
     "Hepatitis A jaundice >70% vs base ~5% → LR+ ~17"),
    ("jaundice", "hepatitis_e", 17.0, None,
     "Hepatitis E jaundice >70% vs base ~5% → LR+ ~17"),

    # Clinical consensus — measles
    ("rash", "measles", 6.3, None,
     "Measles rash >95% vs base ~15% → LR+ ~6.3"),
    ("respiratory_symptoms", "measles", 3.6, None,
     "Measles cough/coryza >90% vs base ~25% → LR+ ~3.6"),

    # Clinical consensus — enteric fever
    ("gi_symptoms", "typhoid_and_paratyphoid_fever", 2.4, None,
     "Enteric fever GI >80% vs base ~35% → LR+ ~2.4"),

    # Clinical consensus — CAP
    ("respiratory_symptoms", "community_acquired_pneumonia", 3.8, None,
     "CAP cough >95% vs base ~25% → LR+ ~3.8"),

    # Neurological — JE
    ("neurological_symptoms", "japanese_encephalitis", 10.6, None,
     "JE neuro >85% vs base ~8% → LR+ ~10.6"),

    # Neurological — rabies
    ("neurological_symptoms", "rabies", 10.6, None,
     "Rabies neuro >85% vs base ~8% → LR+ ~10.6"),
]


def compute_model_lr(
    model: TravellerFeverModel,
    symptom: str,
    disease_key: str,
) -> tuple[float, float]:
    """Compute the model's effective LR+ and LR- for a symptom-disease pair.

    LR+ = P(symptom present | dx) / P(symptom present | background)
    LR- = P(symptom absent | dx) / P(symptom absent | background)
    """
    def_key = model._resolve_definition_key(disease_key)
    defn = model.diseases.get(def_key)
    if defn is None:
        return 1.0, 1.0

    grade = defn.symptoms.get(symptom, "false")
    p_dx = SYMPTOM_GRADE_PRESENT.get(grade, 0.05)
    p_base = SYMPTOM_BASE_RATES.get(symptom, 0.20)

    lr_positive = p_dx / p_base
    lr_negative = (1.0 - p_dx) / (1.0 - p_base)

    return lr_positive, lr_negative


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"

    model = TravellerFeverModel.from_yaml(priors_path, defs_path)

    print(f"\n{'='*80}")
    print("LIKELIHOOD RATIO CALIBRATION")
    print(f"{'='*80}")
    print(f"{'Symptom':<25s} {'Disease':<30s} {'Model LR+':>10s} {'Published LR+':>14s} {'Ratio':>7s}")
    print("-" * 80)

    results = []
    for symptom, disease, pub_lr_pos, pub_lr_neg, source in PUBLISHED_LRS:
        # Map diagnosis name — some published LRs use YAML keys
        model_lr_pos, model_lr_neg = compute_model_lr(model, symptom, disease)

        ratio = model_lr_pos / pub_lr_pos if pub_lr_pos else float("nan")
        concordant = 0.5 <= ratio <= 2.0  # Within 2-fold

        flag = "  ✓" if concordant else "  ✗"
        print(f"{symptom:<25s} {disease:<30s} {model_lr_pos:>10.2f} {pub_lr_pos:>14.1f} {ratio:>6.2f}{flag}")

        results.append({
            "symptom": symptom,
            "disease": disease,
            "model_lr_positive": round(model_lr_pos, 3),
            "published_lr_positive": pub_lr_pos,
            "ratio": round(ratio, 3),
            "concordant_2fold": concordant,
            "source": source,
        })

    # Summary
    n_concordant = sum(1 for r in results if r["concordant_2fold"])
    n_total = len(results)
    print("-" * 80)
    print(f"Concordance (within 2-fold): {n_concordant}/{n_total} ({n_concordant/n_total:.0%})")
    print(f"  ✓ = model LR+ within 0.5×–2.0× of published LR+")

    # Save
    output_dir = OUTPUTS_DIR / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "lr_calibration": {
            "n_pairs": n_total,
            "n_concordant": n_concordant,
            "concordance_rate": round(n_concordant / n_total, 3),
            "pairs": results,
        }
    }
    with open(output_dir / "lr_calibration.yaml", "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    print(f"\nSaved to {output_dir / 'lr_calibration.yaml'}")


if __name__ == "__main__":
    main()
