# OSF Pre-Registration: Australian-Weighted Bayesian Returned-Traveller Fever Differential with Live Outbreak Priors

**Registration date:** 2026-04-18
**Status:** FROZEN on OSF
**OSF Project:** https://osf.io/m85c7/
**OSF Registration:** https://osf.io/ma6yd/
**Registration DOI:** https://doi.org/10.17605/OSF.IO/MA6YD
**Registration date:** 2026-04-18T07:51:22Z

### Freeze sequencing

1. Access all derivation data sources (GeoSentinel papers, NNDSS, CDC Yellow Book) and record access dates in Section 3.1
2. Freeze this registration on OSF (locks analysis plan, hyperparameters, thresholds)
3. Extract validation case series, hash the frozen file, record hash in amendment log
4. Begin model development (Phases 1-3)

Derivation data may be inspected before freezing — only the validation case series outcomes must remain unseen until Phase 4.

---

## 1. Study information

### 1.1 Title

Australian-Weighted Bayesian Returned-Traveller Fever Differential with Live Outbreak Priors: Derivation, Benchmarking, and Open Deployment

### 1.2 Authors

Hayden Farquhar

### 1.3 Research question

In a febrile returned traveller presenting to an Australian emergency department, can a Naive Bayes diagnostic differential — constructed from hierarchically-pooled Australian-weighted destination priors with monthly-refreshed ProMED/WHO DON outbreak signals — produce Top-5 diagnostic accuracy non-inferior to a KABISA TRAVEL replication on extractable published Australian case series, with explicit abstention when posterior discrimination is insufficient?

### 1.4 Hypotheses

**Primary hypothesis (H1):** The Australian-weighted Naive Bayes model with live outbreak priors will achieve Top-5 accuracy >= 70% on the held-out Australian validation case series.

**Secondary hypothesis (H2):** Live outbreak prior integration will improve Top-5 accuracy by >= 3 percentage points compared to the same model without the live layer (base priors only).

**Tertiary hypothesis (H3):** The model's abstention mechanism will flag >= 80% of cases where the true diagnosis is not in the model's Top-5 differential.

### 1.5 Null response plan

If the primary hypothesis is not met (Top-5 < 70%), or if Top-5 accuracy is within 5 percentage points of the KABISA-replication baseline, superiority will not be claimed. The manuscript will be reframed as "maintained open infrastructure for Australian-weighted traveller fever differentials," with the live-updating ETL pipeline and transparent Bayesian evidence breakdown as the primary contributions.

---

## 2. Design plan

### 2.1 Study type

Diagnostic model derivation and retrospective external validation using published aggregate data and case series.

### 2.2 Study design

- **Derivation:** Naive Bayes model constructed from published GeoSentinel destination-diagnosis tables, reweighted by Australian NNDSS imported-case distributions, with symptom/incubation/exposure likelihoods derived from CDC Yellow Book and referenced clinical literature.
- **Live layer:** Monthly ProMED and WHO DON outbreak signals integrated via exponential smoothing.
- **Validation:** Retrospective application to published Australian returned-traveller case series (external to derivation data).
- **Benchmark comparators:** (1) KABISA TRAVEL logic replication; (2) destination-specific malaria-first heuristic.

### 2.3 Blinding

The validation case series will be extracted and frozen (file hash recorded below) before any model tuning or threshold calibration. The analyst will not inspect validation outcomes during model development (Phases 1-3). Benchmarking (Phase 4) will be conducted in a single pass against the frozen dataset.

---

## 3. Data sources

### 3.1 Derivation data (model construction)

| Source | PMID | DOI | Purpose | Access date |
|--------|------|-----|---------|-------------|
| Leder et al. 2013, *Ann Intern Med* 158(6):456-68 | 23552375 | [10.7326/0003-4819-158-6-201303190-00005](https://doi.org/10.7326/0003-4819-158-6-201303190-00005) | Destination-syndrome conditionals (42,173 travellers, 2007-2011) | 2026-04-18 (metadata) |
| Leder et al. 2013, *Emerg Infect Dis* 19(7):1049-73 | 23763775 | [10.3201/eid1907.121573](https://doi.org/10.3201/eid1907.121573) | Trend/cluster data (42,223 travellers, 2000-2010) | 2026-04-18 (metadata) |
| Brown, Angelo et al. 2023, *MMWR Surveill Summ* 72(7):1-22 | 37368820 | [10.15585/mmwr.ss7207a1](https://doi.org/10.15585/mmwr.ss7207a1) | Region-diagnosis conditionals (9,859 US nonmigrant travellers, 2012-2021) | 2026-04-18 (metadata) |
| Bierbrier et al. 2024, *J Travel Med* 31(2) | 38195993 | [10.1093/jtm/taae005](https://doi.org/10.1093/jtm/taae005) | Chikungunya-specific priors (1,202 travellers, 2005-2020) | 2026-04-18 (full text via PMC) |
| Duvignaud, Angelo et al. 2024, *J Travel Med* 31(7) | 38951998 | [10.1093/jtm/taae089](https://doi.org/10.1093/jtm/taae089) | Dengue-specific priors (5,958 travellers, 2007-2022) | 2026-04-18 (metadata) |
| Sohail et al. 2024, *J Travel Med* 31(3) | 38127641 | [10.1093/jtm/taad164](https://doi.org/10.1093/jtm/taad164) | Australian imported malaria (3,204 cases, 2012-2022) with species + destination | 2026-04-18 (metadata) |
| Sohail et al. 2024, *J Travel Med* 31(2) | 38243558 | [10.1093/jtm/taae014](https://doi.org/10.1093/jtm/taae014) | Australian imported dengue (12,568 cases, 2012-2022) with top-10 countries | 2026-04-18 (metadata) |
| Forster & Leder 2021, *J Travel Med* 28(8) | 34619766 | [10.1093/jtm/taab150](https://doi.org/10.1093/jtm/taab150) | Australian typhoid per-country incidence rates (923 cases, 2010-2017) | 2026-04-18 (metadata) |
| NAMAC annual reports (CDI, 2004-2015) | — | — | Arboviral + malaria imported counts with country-of-acquisition | 2026-04-18 (index) |
| NNDSS formal data request (pending) | — | — | Imported-case denominators for hep A, hep E, measles, leptospirosis (2012-2024) | TBD |
| CDC Yellow Book (2024 edition, online) | — | — | Symptom, incubation, exposure conditionals (22 diseases) | 2026-04-18 |

**Note on Australian reweighting sources:** The original plan assumed NNDSS public datasets would provide imported-case denominators. In practice, NNDSS public datasets only cover 4 diseases (influenza, meningococcal, pneumococcal, salmonella). Three published NNDSS analyses (Sohail malaria, Sohail dengue, Forster typhoid) provide high-quality destination-stratified imported-case data for the three highest-volume travel-associated febrile diagnoses. NAMAC annual reports (2004-2015) cover arboviruses and malaria with country-of-acquisition. A formal NNDSS data request has been drafted for remaining diseases. See `data/raw/nndss/australian_imported_case_sources.md` for full inventory.

**Note on changes from original plan:** The papers originally listed as "Angelo 2017" and "Hamer 2016 Zika" could not be located — the PMIDs in the initial plan (28329385 and 27496394) correspond to unrelated papers. They have been replaced with the most comprehensive available GeoSentinel analyses: Brown/Angelo 2023 MMWR and Duvignaud/Angelo 2024 dengue analysis. See `data/raw/geosentinel/extraction_notes.md` for full verification details.

All access dates are recorded at time of extraction. Dates marked "(metadata)" indicate PubMed API metadata retrieval; full PDF table extraction dates will be updated when PDFs are processed.

### 3.2 Live outbreak data

| Source | Scrape method | Frequency |
|--------|--------------|-----------|
| ProMED-mail RSS | `feedparser` + rule-based classifier | Monthly |
| WHO Disease Outbreak News | RSS/HTML scrape + rule-based classifier | Monthly |

### 3.3 Validation data (external, frozen)

Published Australian returned-traveller case series from:
- Melbourne Hospital for Tropical Diseases
- Westmead Hospital
- Royal Prince Alfred Hospital
- Royal Brisbane and Women's Hospital

**Inclusion criteria for validation cases:**
- Published in peer-reviewed literature
- Individual-level data extractable (destination, symptoms, exposures, incubation period, final diagnosis)
- Australian site
- Febrile presentation as primary or secondary complaint

**Exclusion criteria:**
- Cases with missing destination
- Cases with final diagnosis not in model's diagnosis set (these will be reported as a separate "out-of-scope" category)
- Paediatric-only series (age < 16) unless adult cases are separately extractable

### 3.4 Validation set freeze

- **Freeze timing:** Before any model hyperparameter tuning or threshold calibration.
- **File:** `data/processed/validation_cases.parquet`
- **SHA-256 hash:** [TO BE RECORDED AT FREEZE]
- **Number of cases:** [TO BE RECORDED AT FREEZE]
- **Diagnosis distribution:** [TO BE RECORDED AT FREEZE]

---

## 4. Model specification

### 4.1 Model class

Naive Bayes classifier with categorical and continuous features.

### 4.2 Prior construction

For each (destination, diagnosis) pair:

1. **Base rate** from GeoSentinel published tables (destination-diagnosis proportion).
2. **Australian reweighting:** Multiply by ratio of NNDSS Australian imported-case proportion to GeoSentinel global proportion for that destination.
3. **Hierarchical shrinkage:** Empirical Bayes partial pooling across destination groups:
   - Southeast Asia (Indonesia, Thailand, Vietnam, Cambodia, Laos, Myanmar, Philippines, Malaysia)
   - Pacific (Papua New Guinea, Fiji, Samoa, Tonga, Vanuatu, Solomon Islands)
   - South Asia (India, Sri Lanka, Bangladesh, Nepal, Pakistan)
   - East Africa (Kenya, Tanzania, Uganda, Ethiopia)
   - West Africa (Nigeria, Ghana, Sierra Leone, Liberia)
   - Southern Africa (South Africa, Mozambique, Zimbabwe)
   - Central America and Caribbean
   - South America (Brazil, Colombia, Peru, Ecuador, Bolivia)

   Shrinkage strength determined by effective sample size per destination cell. Destinations with < 10 cases in GeoSentinel are shrunk toward their group mean.

4. **Renormalisation** so that priors sum to 1 for each destination.

### 4.3 Likelihood specification

Per-diagnosis conditionals stored in `data/clinical_knowledge/diagnosis_definitions.yaml`. Every cell must cite a published reference.

**Symptom likelihoods** (binary, per diagnosis):
- Fever, rash, arthralgia/myalgia, jaundice, haemorrhagic signs, gastrointestinal symptoms, respiratory symptoms, neurological symptoms

**Exposure likelihoods** (binary, per diagnosis):
- Freshwater contact, mosquito exposure, animal contact, sexual contact, needle/blood exposure, food/water risk, respiratory/droplet exposure

**Incubation period** (continuous):
- Modelled as uniform distribution over published min-max range per diagnosis (conservative choice; gamma available as sensitivity analysis).

### 4.4 Live outbreak layer

**Smoothing parameter (pre-registered):** alpha = 0.3 (exponential smoothing)

**Update rule:**
```
signal_t = alpha * count_t + (1 - alpha) * signal_{t-1}
```

where `count_t` is the number of classified ProMED + WHO DON entries for a given (region, diagnosis) pair in month t.

**Prior upweighting:**
```
P_effective(dx | dest) proportional to P_baseline(dx | dest) * (1 + alpha_upweight * z_smoothed)
```

where `z_smoothed` is the z-score of the current smoothed signal relative to the trailing 12-month mean and standard deviation.

**Pre-registered constraints:**
- `alpha` (smoothing): **0.3** (fixed)
- `alpha_upweight` (scaling): **0.3** (fixed)
- Maximum upweight cap: **3x** baseline prior
- Minimum: no downweighting below baseline (floor at 1x)

### 4.5 Inference

```
P(dx | destination, exposures, symptoms, incubation) proportional to
  P(dx | destination_effective) *
  product_i P(symptom_i | dx) *
  product_j P(exposure_j | dx) *
  P(incubation | dx)
```

Posteriors normalised to sum to 1 across all diagnoses in scope for the given destination(s).

### 4.6 Abstention rule (pre-registered)

**Trigger:** If the three highest-ranked posterior probabilities are ALL < 0.25, the model outputs: "Insufficient discrimination for confident ranking — specialist referral recommended."

**Threshold:** 0.25 (fixed, not tuned on validation data)

**Rationale:** With a typical differential of 15-25 diagnoses, a uniform distribution would give each ~0.04-0.07. A top posterior of 0.25 represents meaningful discrimination above chance. If even the top-3 candidates cannot reach this threshold, the input combination is genuinely ambiguous.

---

## 5. Analysis plan

### 5.1 Primary outcome measures

| Metric | Definition | Success threshold |
|--------|-----------|-------------------|
| **Top-1 accuracy** | Proportion of validation cases where the highest-ranked diagnosis matches final diagnosis | Report; compare to KABISA replication |
| **Top-5 accuracy** | Proportion of cases where final diagnosis appears in top-5 ranked differential | >= 70% (primary hypothesis) |
| **Calibration** | Reliability diagram: binned predicted probability vs observed frequency for top-ranked diagnosis | Visual; report Brier score |
| **Abstention rate** | Proportion of cases triggering the abstention rule | Report |
| **Abstention appropriateness** | Among abstained cases, proportion where true diagnosis was NOT in top-5 | >= 80% (tertiary hypothesis) |

### 5.2 Secondary analyses

- **Live layer ablation:** Compare full model (with live priors) vs base model (without live priors) on the same validation set. Report Top-5 difference with 95% bootstrap CI (10,000 resamples).
- **Malaria-specific subset:** Report Top-1 accuracy for malaria cases separately; compare to destination-specific malaria-first heuristic.
- **Per-destination-group performance:** Report Top-5 accuracy stratified by destination group (SE Asia, Pacific, South Asia, Africa, Americas).
- **Per-diagnosis calibration:** Report calibration for the 5 most common diagnoses individually.
- **Sensitivity to alpha:** Repeat primary analysis with alpha = 0.1, 0.2, 0.4, 0.5. Report as supplementary (these are sensitivity analyses, not used for primary claims).
- **Sensitivity to abstention threshold:** Repeat with threshold = 0.15, 0.20, 0.30, 0.35. Report abstention rate and appropriateness trade-off curve.

### 5.3 Statistical comparisons

- **Non-inferiority comparison to KABISA replication:** McNemar's test for paired comparison of Top-5 accuracy on the same validation cases. Report p-value and 95% CI for the difference.
- **Bootstrap confidence intervals:** 10,000 bootstrap resamples for all primary metrics.
- **Multiple comparisons:** Secondary analyses are exploratory and will be reported as such. No multiplicity correction applied; findings described as hypothesis-generating.

### 5.4 Handling of edge cases

- **Cases with multiple destinations:** Use the destination with highest prior entropy (most uncertain) as primary; report sensitivity to destination choice.
- **Cases with missing symptoms/exposures:** Missing features treated as uninformative (likelihood set to 1.0, equivalent to marginalising out the feature).
- **Out-of-scope diagnoses:** Cases whose true diagnosis is not in the model's diagnosis set are excluded from Top-1/Top-5 accuracy but reported separately as a coverage metric (proportion of validation cases whose diagnosis is in-scope).

---

## 6. Diagnosis set

The following diagnoses are included in the model (subject to data availability during derivation; any additions or removals will be logged in `osf/amendment_log.md`):

### Tropical/infectious (core set)

1. Malaria (P. falciparum)
2. Malaria (P. vivax/ovale/malariae)
3. Dengue fever
4. Chikungunya
5. Zika virus
6. Enteric fever (typhoid/paratyphoid)
7. Acute bacterial gastroenteritis
8. Hepatitis A
9. Hepatitis B (acute)
10. Hepatitis E
11. Rickettsial infection (scrub typhus, murine typhus)
12. Leptospirosis
13. Acute HIV seroconversion
14. Influenza
15. COVID-19
16. Measles
17. Japanese encephalitis
18. Melioidosis
19. Tuberculosis (active pulmonary)
20. Schistosomiasis (acute/Katayama fever)
21. Strongyloides (acute)
22. Amoebiasis (amoebic liver abscess)
23. Brucellosis
24. Q fever
25. Mpox
26. Oropouche virus
27. Yellow fever
28. Rabies (post-exposure presentation)

### Non-tropical differential (important to include for calibration)

29. Community-acquired pneumonia
30. Urinary tract infection / pyelonephritis
31. Viral upper respiratory tract infection
32. Infectious mononucleosis (EBV/CMV)
33. Undifferentiated viral syndrome

---

## 7. Reporting standard

TRIPOD+AI checklist with supplementary ETL audit trail documenting:
- All data source access dates
- ProMED/WHO DON classifier performance (precision/recall on manually labelled subset)
- Prior version history (git-tracked)
- Complete `diagnosis_definitions.yaml` with per-cell citations

---

## 8. Ethics

This study uses only publicly available aggregate data and published case series. No individual patient data is collected or accessed. An ethics exemption determination is documented in `osf/ethics_determination.md`.

---

## 9. Timeline

| Phase | Weeks | Key deliverable |
|-------|-------|----------------|
| 0: Setup | 1 | Directory structure, dependencies, pre-registration frozen |
| 1: Priors extraction | 1-3 | GeoSentinel + NNDSS priors |
| 2: Live ETL | 3-5 | ProMED/WHO DON pipeline |
| 3: Inference engine | 5-7 | Naive Bayes + abstention |
| 4: Benchmarking | 7-9 | Validation against KABISA + frozen case series |
| 5: Streamlit app | 9-11 | Deployed tool |
| 6: Manuscript | 11-13 | TRIPOD+AI manuscript |

---

## 10. Amendments

Any changes to the pre-registered analysis plan made after this registration is frozen will be documented in `osf/amendment_log.md` with date, rationale, and classification as:
- **Protocol amendment:** Change to primary analysis (must be justified)
- **Sensitivity addition:** Additional exploratory analysis (does not require justification but must be labelled as post-hoc)
- **Error correction:** Fix to an error in the registration (must document original and corrected text)

---

## 11. Data and code availability

- All code will be released under an MIT license on GitHub.
- Processed priors and clinical knowledge YAML files will be released under CC-BY 4.0.
- Validation case series will be released as a structured dataset (derived from published sources only).
- The Streamlit tool will be maintained with monthly prior updates for a minimum of 24 months post-publication.

---

*This registration is to be frozen on the Open Science Framework before extraction of the validation case series. The SHA-256 hash of the frozen validation dataset will be appended to Section 3.4 as an amendment upon freeze.*
