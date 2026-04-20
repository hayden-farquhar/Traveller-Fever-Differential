# Project 59: Australian-Weighted Bayesian Returned-Traveller Fever Differential with Live Outbreak Priors

## Project Tracking Synchronisation

**IMPORTANT:** Every time work is done on this project, you MUST update BOTH:
1. **This project's PROGRESS.md** — update with the specific work completed, status changes, submission updates, etc.
2. **The Research Project Tracker** at `/Users/haydenfarquhar/Documents/Research Projects/Research_Project_Tracker.xlsx` — update the relevant row on the Summary sheet to reflect current manuscript status, submission status, dates, preprint status, etc.

These two files must always be kept in sync. Never update one without updating the other.

## Overview

Open-source Naive Bayes diagnostic differential for febrile returned travellers with Australian-weighted destination priors (reweighted from GeoSentinel via NNDSS imported-case data) and monthly-refreshed live outbreak priors from ProMED/WHO DON. Benchmarked against KABISA TRAVEL replication. Streamlit tool with maintained ETL pipeline. Est. 10-14 weeks. Local CPU + GitHub Actions for monthly priors update.

**Target journals:** Journal of Travel Medicine > Emergency Medicine Australasia > PLOS NTDs

## Directory Structure

```
59 Traveller Fever Differential/
├── CLAUDE.md
├── PROGRESS.md
├── project-59-traveller-fever-differential.md
├── data/
│   ├── raw/                    # GeoSentinel tables, NNDSS snapshots, ProMED/WHO DON archives
│   ├── interim/                # Classified outbreak signals
│   └── processed/              # Destination priors, symptom/incubation/exposure conditionals
├── scripts/
│   ├── 01_extract_geosentinel.py      # PDF table extraction (tabula-py)
│   ├── 02_fetch_nndss.py              # NNDSS imported-case denominators
│   ├── 03_build_base_priors.py        # GeoSentinel + NNDSS Australian reweighting
│   ├── 04_hierarchical_shrinkage.py   # Empirical Bayes partial pooling
│   ├── 05_scrape_promed.py            # ProMED RSS monthly scraper
│   ├── 06_scrape_who_don.py           # WHO DON monthly scraper
│   ├── 07_live_outbreak_smoothing.py  # Exponential smoothing (alpha=0.3, cap 3x)
│   ├── 08_naive_bayes.py              # Inference engine + abstention
│   ├── 09_benchmark.py               # KABISA replication + validation
│   └── 10_streamlit_app.py           # Deployed tool
├── notebooks/
├── outputs/{figures,tables,supplementary}/
├── manuscript/
├── submissions/
└── repository/
```

## Tech Stack

- **Language:** Python 3.10+
- **Data extraction:** `tabula-py` (requires Java), `feedparser`, `aiohttp`, `beautifulsoup4`
- **ML/stats:** `scipy`, `scikit-learn`, `pyyaml`
- **App:** `streamlit`, `altair`
- **CI:** GitHub Actions for monthly ProMED/WHO DON scrape
- **Compute:** Local CPU only.

## Key Methods

- **Priors:** GeoSentinel (Leder 2013 PMID:23552375, Brown/Angelo 2023 PMID:37368820, Bierbrier 2024 PMID:38195993, Duvignaud/Angelo 2024 PMID:38951998) destination conditionals reweighted by NNDSS Australian imported-case distribution; hierarchical shrinkage via empirical Bayes across similar destinations
- **Likelihoods:** Per-diagnosis symptom, exposure, and incubation conditionals from CDC Yellow Book (stored in YAML, every cell cited)
- **Live layer:** ProMED + WHO DON monthly scrape; exponential smoothing (alpha=0.3 pre-registered); cap at 3x prior upweight
- **Inference:** Naive Bayes; ranked differential with per-factor log-evidence breakdown
- **Abstention:** Top-3 posteriors all <0.25 triggers "insufficient discrimination — refer"
- **Benchmarks:** KABISA replication, destination+fever malaria-first heuristic; metrics: Top-1, Top-5, calibration, abstention rate
- **Reporting:** TRIPOD+AI + custom ETL audit trail

## Notes for Claude

- KABISA's 72% Top-1 is real benchmark; may not beat it — if not, pivot to "maintained open infrastructure"
- Australian positioning is legitimate (SE Asia + Pacific destination mix differs from US/European tools)
- Naive Bayes independence assumption is violated (co-endemic diseases) — report honestly
- Validation: pre-registered Australian case series frozen before model tuning
- Monthly CI cron must be maintained 24+ months post-publication
- Java required for tabula-py — document in README
- Tool must show "Last priors update" timestamp and data sources sidebar
