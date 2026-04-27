# BEACON

**Bayesian Evidence-Adjusted Clinical Outbreak Navigator**

An open-source diagnostic differential for febrile returned travellers, with Australian-weighted destination priors and monthly-refreshed live outbreak signals from WHO Disease Outbreak News.

**Pre-registration:** [OSF](https://doi.org/10.17605/OSF.IO/MA6YD)

## Overview

BEACON produces a ranked differential diagnosis for a febrile returned traveller, given:

- **Destination(s)** visited (9 world regions)
- **Symptoms** (11 clinical features with graded prevalence-based likelihoods)
- **Exposures** (8 routes, including absence as negative evidence)
- **Incubation period** (days since return, triangular distribution)
- **Vaccination status** (reduces priors for vaccine-preventable diseases)

The model uses:

1. **GeoSentinel** destination-diagnosis conditionals reweighted by Australian NNDSS imported-case distributions
2. **Hierarchical shrinkage** via empirical Bayes across similar destination regions
3. **Live outbreak priors** from monthly WHO DON API scrapes with exponential smoothing (alpha=0.3, cap 3x)
4. **Symptom likelihood ratios** against febrile-traveller base rates (not raw probabilities)
5. **Must-not-miss safety alerts** for malaria, measles, VHF, mpox — with cited clinical guidelines
6. **Explicit abstention** when the top-3 posteriors are all below 0.25

Covers 33 diagnoses including tropical infections, vaccine-preventable diseases, and common non-tropical differentials.

## Performance

Validated on N=137 cases (38 published case reports + 99 Bottieau-calibrated semi-synthetic):

| Metric | BEACON | KABISA replication | Published KABISA |
|--------|--------|-------------------|-----------------|
| **Top-1 accuracy** | **71.5%** (95% CI 63.5–78.8%) | 26.3% | 72% (205 cases) |
| **Top-5 accuracy** | **94.9%** (95% CI 91.2–98.5%) | 70.8% | 88% (205 cases) |
| Brier score | 0.168 | — | — |

McNemar's test: p < 0.001 for both Top-1 and Top-5 vs KABISA replication.

**Sensitivity analyses:**

- *Symptom-grade perturbation* (`src/validation/perturbation_sensitivity.py`): ±20% random variation across all symptom grades, 1,000 iterations → Top-1 SD = 2.1 pp, Top-5 SD = 0.7 pp.
- *O'Brien 2001 base-rate sensitivity* (`src/validation/base_rate_sensitivity.py`, added in v1.1.0): ±20%, ±40%, ±50% perturbation of likelihood-ratio denominators, 1,000 iterations each → Top-1 and Top-5 mathematically invariant (SD 0.0 across 3,000 iterations); only Brier varies (SD 0.002). The invariance is structural: base-rate perturbation produces a multiplicative change in likelihood ratios that is identical across all 33 diagnoses and cancels in the relative ranking. See `outputs/tables/base_rate_sensitivity.yaml` for full results and the manuscript Supplementary Table S10.

## Setup

### Prerequisites

- Python 3.10+
- Java 17+ (required for `tabula-py` PDF table extraction)

### Install

```bash
pip install -e ".[dev]"
```

### Run the app

```bash
streamlit run app/streamlit_app.py
```

## Project structure

```
src/
├── ingest/          # Data extraction: GeoSentinel, NNDSS, WHO DON, ProMED
├── priors/          # Prior construction, hierarchical shrinkage, live outbreak smoothing
├── inference/       # Naive Bayes engine, safety alerts, abstention logic
└── validation/      # Case series, KABISA replication, benchmarking, statistical analyses

data/
├── raw/             # Source data (GeoSentinel tables, NNDSS, scrape archives, external validation)
├── processed/       # Destination priors, conditionals, live multipliers, validation cases
└── clinical_knowledge/  # Graded symptom definitions (cited per-cell)

app/                 # Streamlit deployment
```

## Data sources

| Source | Use | Access |
|--------|-----|--------|
| GeoSentinel (Leder 2013, Brown/Angelo 2023, Bierbrier 2024, Duvignaud 2024) | Destination-diagnosis base rates | PMC open access |
| Australian NNDSS (Sohail 2024, Forster & Leder 2021) | Imported-case reweighting | Published analyses |
| Bottieau 2007 (N=2,071) | Symptom prevalence calibration | Published |
| CDC Yellow Book 2024 | Incubation, exposure conditionals | Public |
| WHO Disease Outbreak News | Live outbreak signals | OData API |

## Monthly priors update

A GitHub Actions workflow runs on the 1st of each month to scrape WHO DON, update live outbreak multipliers, and open a PR for review. See `.github/workflows/monthly_priors_update.yml`.

## Citation

Farquhar H. BEACON: An Australian-weighted Bayesian diagnostic differential for febrile returned travellers with live outbreak priors. 2026. Pre-registered at https://doi.org/10.17605/OSF.IO/MA6YD

## Licence

Code: MIT. Clinical knowledge data: CC-BY-4.0.
