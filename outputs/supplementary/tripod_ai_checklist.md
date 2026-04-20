# TRIPOD+AI Checklist — BEACON

Transparent Reporting of a multivariable prediction model for Individual Prognosis Or Diagnosis, extended for AI (TRIPOD+AI).

**Model:** BEACON (Bayesian Evidence-Adjusted Clinical Outbreak Navigator)
**Task:** Diagnostic differential for febrile returned travellers
**Pre-registration:** https://doi.org/10.17605/OSF.IO/MA6YD

## Title and Abstract

| # | Item | Location |
|---|------|----------|
| 1 | Identify as development and/or validation study | Title |
| 2 | Structured summary including model type, predictors, outcome, performance | Abstract |

## Introduction

| # | Item | Location |
|---|------|----------|
| 3a | Scientific/clinical background and rationale | Introduction §1 |
| 3b | Objectives, including whether development, validation, or both | Introduction §2 |

## Methods

| # | Item | Location |
|---|------|----------|
| 4a | Data sources: GeoSentinel (PMIDs 23552375, 37368820, 38195993, 38951998), NNDSS (PMIDs 38127641, 38243558, 34619766), CDC Yellow Book, Bottieau 2007 (PMID 17220752), O'Brien 2001 (PMID 11486283), WHO DON API | Methods §Data sources |
| 4b | Study dates: derivation data 2007-2024; validation cases from published reports 2007-2026 | Methods §Data sources |
| 5a | Key study dates including start/end of accrual, follow-up | Methods §Study design |
| 5b | AI-specific: development environment (Python 3.10+, local CPU), training not applicable (rule-based priors, no gradient-based training) | Methods §Technical |
| 6a | Eligibility criteria: febrile returned travellers from tropical/subtropical areas | Methods §Population |
| 6b | Treatment received: not applicable (diagnostic, not prognostic) | N/A |
| 7a | Outcome: ranked differential diagnosis (Top-1, Top-5 accuracy) | Methods §Outcomes |
| 7b | Outcome assessment: reference standard = confirmed microbiological/serological diagnosis | Methods §Reference standard |
| 8 | Predictors: 11 symptom features (graded), 8 exposure features, incubation period, 9 destination regions, vaccination status | Methods §Predictors |
| 9 | Sample size: derivation N/A (prior-based, no fitting); validation N=137 (38 published + 99 Bottieau-calibrated) | Methods §Sample size |
| 10a | Model development: Naive Bayes with likelihood ratios against base rates, peaked triangular incubation, hierarchical shrinkage, live outbreak multipliers | Methods §Model |
| 10b | AI-specific: no hyperparameter tuning on validation set; pre-registered thresholds (alpha=0.3, abstention=0.25) | Methods §Model |
| 10c | AI-specific: model type = Naive Bayes (generative, not discriminative). No neural network, no feature learning. | Methods §Model |
| 10d | Model complexity: 33 diagnoses × (11 symptoms + 8 exposures + incubation + 9 region priors) = ~700 parameters, all set from published data, not learned | Methods §Model |
| 11 | Risk groups: abstention when top-3 posteriors all < 0.25 | Methods §Abstention |
| 12 | Performance measures: Top-1, Top-5 accuracy, Brier score, calibration (reliability diagram), abstention rate/appropriateness, McNemar's test | Methods §Statistical analysis |

## Results

| # | Item | Location |
|---|------|----------|
| 13a | Flow of participants: 137 validation cases (38 published case reports from 22 papers + 99 Bottieau-calibrated semi-synthetic) | Results §Validation set |
| 13b | Demographics of validation cases: destination, diagnosis distribution | Results Table 1 |
| 14a | Number of predictors: 11 symptoms + 8 exposures + incubation + region = 21 input features | Results §Model |
| 14b | Unadjusted associations: likelihood ratios for key symptom-disease pairs (LR calibration analysis) | Results §LR calibration |
| 15a | Performance: Top-1 71.5% (95% CI 63.5-78.8%), Top-5 94.9% (91.2-98.5%), Brier 0.168 | Results §Primary |
| 15b | Calibration: reliability diagram (Figure 1) | Results Figure 1 |
| 16 | Model performance across subgroups: per-destination (Table), per-diagnosis (Table), malaria-specific | Results §Subgroups |

## AI-Specific Items

| # | Item | Location |
|---|------|----------|
| AI-1 | Software and version: Python 3.10+, scipy, numpy, pyyaml, streamlit | Methods §Technical |
| AI-2 | Data preprocessing: symptom grading from published prevalences; no imputation | Methods §Data |
| AI-3 | Missing data handling: missing features treated as non-informative (LR=1.0) | Methods §Missing data |
| AI-4 | Model interpretability: per-factor log-evidence decomposition (prior, symptoms, exposures, incubation) shown for every diagnosis | Methods §Interpretability |
| AI-5 | Robustness: perturbation sensitivity analysis (±20%, 1000 iterations, Top-1 SD=2.1%) | Results §Sensitivity |
| AI-6 | Fairness: destination-stratified performance reported; no individual-level demographic data used | Results §Subgroups |
| AI-7 | Deployment: open-source Streamlit app, monthly-updated outbreak priors via CI | Discussion §Deployment |

## Discussion

| # | Item | Location |
|---|------|----------|
| 17 | Limitations: Naive Bayes independence assumption, binary symptom input (no severity grading for most), small published validation set (N=38), no prospective validation, KABISA comparison is against replication not original, semi-synthetic cases are not fully independent | Discussion §Limitations |
| 18 | Interpretation: model comparable to published KABISA accuracy (72% Top-1) on a different case set; primary hypothesis (Top-5 ≥ 70%) met with CI lower bound 91.2%; live outbreak ETL is the maintained infrastructure contribution | Discussion §Interpretation |
| 19 | Implications: clinical decision support for rural/regional EDs without ID specialist access; safety alerts ensure malaria never missed | Discussion §Clinical implications |
| 20 | Registration: OSF https://doi.org/10.17605/OSF.IO/MA6YD | Methods §Registration |
| 21 | Data and code availability: GitHub hayden-farquhar/Traveller-Fever-Differential (replication) and hayden-farquhar/BEACON (app) | Data availability |

## Supplementary Materials

| Item | Content | File |
|------|---------|------|
| Table S1 | Evidence source table for all symptom grades | evidence_source_table.md |
| Table S2 | Stratified results by case provenance | stratified_provenance.yaml |
| Table S3 | Pre-registered statistical analyses | preregistered_statistics.yaml |
| Table S4 | Perturbation sensitivity analysis | perturbation_sensitivity.yaml |
| Table S5 | LR calibration against Bottieau 2007 | lr_calibration.yaml |
| Table S6 | Decision curve analysis | decision_curve.yaml |
| Table S7 | Signal classifier evaluation | classifier_evaluation.yaml |
| Figure S1 | Per-destination accuracy | fig3_destination_accuracy.png |
| Data S1 | Complete diagnosis definitions YAML | cdc_yellow_book_extraction.yaml |
| Data S2 | Validation cases (published) | validation_cases.yaml |
| Data S3 | Validation cases (Bottieau-calibrated) | validation_cases_bottieau.yaml |
