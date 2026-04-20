# Project 3 — Australian-Weighted Bayesian Returned-Traveller Fever Differential with Live Outbreak Priors

## 0. Quick facts

- **Deliverable:** Open-source Streamlit (or React) tool with monthly-refreshed outbreak priors + derivation and benchmarking paper.
- **Timeline:** 10–14 weeks.
- **Compute:** Local CPU. GitHub Actions for monthly ETL.
- **Target journals:** *Journal of Travel Medicine*, *Emergency Medicine Australasia*, *Tropical Medicine & International Health*, *PLOS NTDs*.
- **Ethics:** HREC-exempt (public aggregate data + case series). Document exemption.
- **Reporting standard:** TRIPOD+AI + custom ETL audit trail.
- **Honest scope:** Naive Bayes is crude. KABISA's 72% Top-1 is the real benchmark. If you don't beat it on Top-1, pivot the paper to "maintained open infrastructure for Australian-weighted traveller fever differentials" — still publishable.

---

## 1. Research question and hypothesis

**Primary question.** In a febrile returned-traveller presenting to an Australian regional ED, can a Naive Bayes differential with hierarchically-pooled Australian-weighted priors and live-updating ProMED/WHO DON outbreak signals produce Top-5 accuracy non-inferior to KABISA TRAVEL on extractable Australian case series, with explicit abstention when top-3 posteriors are all below threshold?

**Primary hypothesis.** Australian-weighted priors + live outbreak updates will produce calibrated Top-5 accuracy ≥ 70% (KABISA's published Top-1 benchmark is 72%; Top-5 is a more useful ED metric) on the held-out Australian case series validation set.

**Null response plan.** If Top-5 does not beat the KABISA-replication baseline, the paper becomes "open maintained pipeline for traveller fever priors" — the live-ETL is itself the contribution.

---

## 2. Clinical context

A rural Australian ED sees a 24-year-old returning from Lombok with fever, headache, vomiting 6 days post-return. Nearest ID physician is 3 hours away. The registrar's decision:

- Which tests to order now?
- Is this malaria-until-proven-otherwise, or can I rule out with RDT + thick/thin + blood culture and start treating presumptively?
- Do I need to isolate for VHF / mpox / measles?

Existing tools:

- **KABISA TRAVEL** — 15 years old, closed, ITM-hosted, ~72% Top-1 accuracy
- **GIDEON** — proprietary
- **MALrisk** — malaria only

None reflects the 2024 Oropouche expansion in the Americas, mpox clusters, Japanese encephalitis re-emergence in Australia, or Australian destination mix (SE Asia + Pacific-heavy).

---

## 3. Prior art

| Tool | Strengths | Gap |
|---|---|---|
| KABISA TRAVEL | Validated, ~72% Top-1 | Closed, no live priors, US/European weighting |
| GIDEON | Broad coverage | Proprietary, expensive, no transparent Bayesian evidence |
| MALrisk | Malaria-specific validation | Single-disease only |
| FeverTravel (Demeester 2011) | Multi-centre validation set | Published but not maintained |
| GeoSentinel surveillance | Gold-standard aggregate priors | US/European over-represented |

**The two moats:**
1. **Live-outbreak ETL** requires a maintained pipeline. Closed tools cannot replicate without ongoing engineering.
2. **Australian weighting** — Indonesia, Thailand, Vietnam, Philippines, Pacific dominate. GeoSentinel priors are poorly calibrated for Australian destination mix.

---

## 4. Data sources

### Primary — destination × exposure × symptom conditionals

| Source | PMID | DOI | Licensing | Extract |
|---|---|---|---|---|
| Leder 2013 *Ann Intern Med* 158(6):456-68 | 23552375 | 10.7326/0003-4819-158-6-201303190-00005 | PMC open (PMC4629801) | Destination → syndrome table (42,173 travellers) |
| Leder 2013 *Emerg Infect Dis* 19(7):1049-73 | 23763775 | 10.3201/eid1907.121573 | PMC open (PMC3713975) | Trend/cluster data (42,223 travellers) |
| Brown/Angelo 2023 *MMWR Surveill Summ* 72(7):1-22 | 37368820 | 10.15585/mmwr.ss7207a1 | PMC open (PMC10332343) | Region × diagnosis (9,859 US nonmigrant travellers, 2012-2021) |
| Bierbrier 2024 *J Travel Med* 31(2) | 38195993 | 10.1093/jtm/taae005 | PMC open (PMC11081466) | Chikungunya-specific priors (1,202 travellers) |
| Duvignaud/Angelo 2024 *J Travel Med* 31(7) | 38951998 | 10.1093/jtm/taae089 | PMC open (PMC11502266) | Dengue-specific priors (5,958 travellers) |

**Note:** Original plan cited "Angelo 2017" (PMID 28329385) and "Hamer 2016 Zika" (PMID 27496394) — both PMIDs are incorrect (cardiology and SSB/asthma papers respectively). Replaced with verified GeoSentinel analyses above.

### Primary — Australian denominator

- **Australian NNDSS** — Public datasets at `health.gov.au/resources/collections/nndss-public-datasets` only cover influenza, meningococcal, pneumococcal, and salmonella. For imported-case denominators for malaria, dengue, enteric fever, etc., a **formal data request** to `NNDSS.datarequests@health.gov.au` is required. Interim data available from CDI annual reports and published NNDSS analyses (see `data/raw/nndss/data_request_template.md`).
- Melbourne Hospital for Tropical Diseases + Westmead returned-traveller case series (published, scrape from papers).

### Live priors

- **ProMED-mail RSS** — `promedmail.org/feed/` — scrape monthly.
- **WHO Disease Outbreak News** — `who.int/emergencies/disease-outbreak-news` — RSS/scrape monthly.
- **ECDC Communicable Disease Threats Report** — `ecdc.europa.eu/en/publications-data?f%5B0%5D=output_types%3A176` — optional tertiary.

### Symptom and incubation conditionals

- **CDC Yellow Book** chapters per disease (public, reference).
- **UpToDate** or *Manson's Tropical Diseases* if accessible — used as reference only, not scraped.

### Validation

- Extractable Australian case series: published Melbourne HTD, Westmead, RPA, Royal Brisbane returned-traveller reviews.

### Ethics

Aggregate published data + public RSS feeds. HREC-exempt. Document in `osf/ethics_determination.md`.

---

## 5. Methods

### 5.1 Destination-weighted prior construction

For each (Australian destination, diagnosis) cell:
- Base rate from GeoSentinel Leder/Angelo tables (destination-pool).
- Reweight by Australian NNDSS imported-case distribution.
- Hierarchical shrinkage: partial pooling across similar destinations (SE Asia, Pacific, South America) via empirical Bayes.

### 5.2 Symptom and incubation likelihoods

Per-diagnosis conditionals from CDC Yellow Book + *Manson's*:
- Incubation distribution (uniform or gamma over published range)
- Symptom likelihoods (binary, per diagnosis: fever, rash, arthralgia, jaundice, haemorrhage, GI, respiratory, neuro)
- Exposure likelihoods (freshwater, mosquito, animal, sexual, needle, food)

Store as YAML file under `data/clinical_knowledge/` — every cell cited to a reference.

### 5.3 Live-outbreak layer

- Monthly GitHub Action scrapes ProMED + WHO DON.
- Classify entries by (region, diagnosis). Use rule-based + LLM classifier (optional — could use local small model if available).
- Compute exponentially-smoothed signal per region × diagnosis.
- Upweight prior proportional to current signal: `P_effective(diagnosis | destination) ∝ P_baseline × (1 + α × z_score_smoothed)`.
- α pre-registered; default 0.3. Cap max upweight at 3x.

### 5.4 Inference

Naive Bayes:
```
P(dx | destination, exposures, symptoms, incubation) ∝
  P(dx | destination_effective) × 
  ∏ P(symptom_i | dx) × 
  ∏ P(exposure_j | dx) × 
  P(incubation | dx)
```

Output: ranked differential with per-factor evidence breakdown. Top-3 abstention: if all three top posteriors < 0.25, output "insufficient discrimination — refer".

### 5.5 Benchmarks

- KABISA replication: extract KABISA's published diagnostic logic from ITM documentation; replicate rule-based system.
- "Destination + fever → regional malaria-first" heuristic.
- MALrisk for malaria-specific comparison only.

Primary metrics:
- Top-1 accuracy
- Top-5 accuracy
- Calibration (reliability diagram for top-ranked diagnosis)
- Abstention rate × appropriateness of abstention

### 5.6 External validation

Published Australian case series — pre-registered as external validation set, extracted once, frozen before model tuning.

---

## 6. Technical stack

```toml
[project]
dependencies = [
    "pandas>=2.2",
    "numpy>=1.26",
    "scipy>=1.12",
    "scikit-learn>=1.4",
    "feedparser>=6.0",
    "aiohttp>=3.9",
    "beautifulsoup4>=4.12",
    "tabula-py>=2.9",       # PDF table extraction
    "pydantic>=2.6",
    "pyyaml>=6.0",
    "streamlit>=1.32",
    "altair>=5.2",
    "pytest>=8.0",
]
```

Java required for tabula-py (document in README).

---

## 7. Directory structure

```
traveller-fever-differential/
├── README.md
├── pyproject.toml
├── Dockerfile
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── monthly_priors_update.yml
├── osf/
│   ├── registration.md
│   ├── ethics_determination.md
│   └── amendment_log.md
├── data/
│   ├── raw/
│   │   ├── geosentinel/            # extracted tables
│   │   ├── nndss/                  # NNDSS annual snapshots
│   │   ├── promed_archive/         # monthly scrape outputs
│   │   └── who_don_archive/
│   ├── interim/
│   │   └── classified_signals.parquet
│   ├── processed/
│   │   ├── destination_priors.yaml
│   │   ├── symptom_conditionals.yaml
│   │   ├── incubation_conditionals.yaml
│   │   └── exposure_conditionals.yaml
│   └── clinical_knowledge/
│       └── diagnosis_definitions.yaml  # cited per-cell
├── src/
│   ├── ingest/
│   │   ├── extract_geosentinel.py
│   │   ├── fetch_nndss.py
│   │   ├── scrape_promed.py
│   │   └── scrape_who_don.py
│   ├── priors/
│   │   ├── build_base_priors.py
│   │   ├── hierarchical_shrinkage.py
│   │   └── live_outbreak_smoothing.py
│   ├── inference/
│   │   ├── naive_bayes.py
│   │   └── abstention.py
│   ├── validation/
│   │   ├── extract_case_series.py
│   │   ├── replicate_kabisa.py
│   │   └── benchmark.py
│   └── utils.py
├── results/
├── app/
│   └── streamlit_app.py
├── paper/
└── tests/
```

---

## 8. Phased workplan with Claude Code prompts

### Phase 0 — Setup (Week 1)

**Claude Code prompt:**
```
Create directory structure from §7 of traveller-fever plan.
uv init. Add dependencies from §6. Install Java for tabula-py.
Write README, pre-registration stub, ethics exemption, amendment log.
Stub .github/workflows/monthly_priors_update.yml for cron-triggered run.
```

### Phase 1 — Priors extraction (Weeks 1–3)

**Human tasks:**
- Extract GeoSentinel tables from 5 key papers (Leder 2013, Angelo 2017, Bierbrier 2024, Hamer 2016, plus 1–2 regional breakdowns).
- Build `data/clinical_knowledge/diagnosis_definitions.yaml` with per-diagnosis incubation, symptom, exposure data, each cell cited.

**Claude Code prompt:**
```
Implement src/ingest/extract_geosentinel.py using tabula-py on PDFs.
Implement src/ingest/fetch_nndss.py scraping/downloading the NNDSS
annual counts by condition.
Implement src/priors/build_base_priors.py: combine GeoSentinel destination
conditionals with NNDSS Australian imported-case weighting, producing
data/processed/destination_priors.yaml.
Implement src/priors/hierarchical_shrinkage.py: empirical-Bayes partial
pooling across similar destinations. Output pooled posteriors with 95% CrI.
```

### Phase 2 — Live outbreak ETL (Weeks 3–5)

**Claude Code prompt:**
```
Implement src/ingest/scrape_promed.py using feedparser on ProMED RSS.
Output: append-only JSONL at data/raw/promed_archive/YYYY-MM.jsonl.

Implement src/ingest/scrape_who_don.py.

Implement the classifier: for each entry, extract (region, diagnosis_hint)
using rule-based matching against diagnosis_definitions.yaml keywords.
Log unclassified entries for manual review.

Implement src/priors/live_outbreak_smoothing.py. Exponential smoothing with
α=0.3 (pre-registered). Cap prior upweight at 3x. Output
data/processed/live_prior_multipliers.yaml with per-(region, diagnosis) multiplier.

Configure .github/workflows/monthly_priors_update.yml to run on 1st of month,
commit updated priors to main, open PR if any prior multiplier changed by >20%
(for human review).
```

### Phase 3 — Inference engine (Weeks 5–7)

**Claude Code prompt:**
```
Implement src/inference/naive_bayes.py.
Inputs: destination list, exposures (multi-select), symptoms (multi-select),
incubation days.
Output: ranked differential list with per-factor log-evidence breakdown.

Implement src/inference/abstention.py: if top-3 posteriors all < 0.25,
return abstention signal.

Write property tests: posteriors sum to 1; removing a symptom cannot
increase the log-posterior of a diagnosis for which that symptom is a
likelihood > 0.5. Catches implementation bugs.
```

### Phase 4 — Benchmarking (Weeks 7–9)

**Human task:** extract validation case series. Freeze this set before any model tuning.

**Claude Code prompt:**
```
Implement src/validation/extract_case_series.py parsing published case
series tables into structured cases (inputs + known diagnosis).
Freeze data/processed/validation_cases.parquet at Phase 3 completion.

Implement src/validation/replicate_kabisa.py — rule-based replica of
KABISA logic per ITM documentation. If full logic is not public, use
the diagnostic rules from Demeester 2011 as the approximate baseline.
Document assumptions.

Implement src/validation/benchmark.py. Compute Top-1, Top-5, calibration,
abstention rate and appropriateness. Output results/tables/benchmark.csv
and results/figures/reliability_top1.png.
```

### Phase 5 — Streamlit/React app (Weeks 9–11)

**Claude Code prompt:**
```
Build app/streamlit_app.py.
Inputs:
- Destination(s) — multi-select with curated country list
- Exposures (freshwater, mosquito, animal, sexual, needle, food, respiratory)
- Symptom checklist
- Incubation period (days since return)

Outputs:
- Ranked top-10 differentials with log-evidence breakdown per diagnosis
- Per-diagnosis: destination prior, symptom likelihood product,
  incubation compatibility, live outbreak multiplier, final posterior
- Abstention banner when triggered
- 'Last priors update' timestamp visible to user
- 'Data sources and limitations' sidebar linking to OSF + GitHub

Deploy-ready for Streamlit Community Cloud or Vercel.
```

### Phase 6 — Manuscript (Weeks 11–13)

**Claude Code prompt:**
```
Draft paper/manuscript.md per TRIPOD+AI with bespoke ETL audit appendix.
Key sections:
- Gap: outdated closed tools, no Australian weighting, no live priors
- Methods: priors → live ETL → Naive Bayes → abstention
- Results: Top-1, Top-5, calibration, abstention appropriateness
- Discussion: where Naive Bayes independence assumption hurts (co-endemic diseases)
Limitations must include:
- Naive Bayes independence assumption is violated
- MALrisk outperforms on malaria specifically (don't hide this)
- Case series extraction may be biased toward 'interesting' diagnoses
- Live priors can be gamed by ProMED noise
- No prospective validation
Run manuscript-evaluator skill.
```

---

## 9. Validation strategy

| Layer | What | How |
|---|---|---|
| Unit | Prior renormalization | pytest |
| Unit | Inference property tests | pytest |
| ETL | Monthly scrape round-trip | CI check |
| Benchmark | KABISA replication | Side-by-side on validation set |
| Calibration | Reliability diagram | Reported |
| External | Pre-registered Australian case series | Frozen |
| Prospective | **Out of scope — Phase 2** | N/A |

---

## 10. Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| KABISA replication is inaccurate | High | Medium | Document replication limits; also compare to Demeester 2011 |
| Top-5 does not beat KABISA | Medium | Medium | Pivot framing to "maintained open infrastructure" |
| ProMED/WHO DON feed changes format | Medium | Low | Monthly CI checks for schema drift |
| Malaria-heavy case series favours MALrisk | High | Low | Report malaria-specific subset separately |
| Naive Bayes independence assumption | Certain | Medium | Report; suggest BN extension for future work |
| Case series validation is biased | Medium | Medium | Use multiple independent series; report per-series |
| Abstention thresholds arbitrary | Medium | Low | Pre-register; report abstention rate vs usefulness tradeoff |

---

## 11. Publication plan

- Pre-print on medRxiv.
- Target *Journal of Travel Medicine* first — right audience.
- *Emergency Medicine Australasia* for the Australian framing.
- *PLOS NTDs* if the tropical disease coverage lands well.
- Supplement: diagnosis_definitions.yaml with every citation, validation cases, ETL audit log.
- **Tool lives on** after the paper — maintain for at least 24 months via the monthly CI cron.

---

## 12. OSF / ethics checklist

- [ ] OSF pre-registration frozen before validation set extraction
- [ ] Ethics exemption documented
- [ ] All data source snapshot dates logged
- [ ] Validation case series frozen before benchmarking
- [ ] Code + priors CC-BY licensed
- [ ] Monthly CI run status documented on OSF after paper publication

---

## 13. Why this project is defensible

1. **Labour moat** — monthly maintained ETL is real work others won't replicate.
2. **Australian positioning** — legitimate. Your MPHTM + rural NSW base gives face validity.
3. **Honest abstention** — methodologically defensible; better than overclaiming.
4. **Graceful degradation** — if Top-5 doesn't beat KABISA, the infrastructure is the paper.

The main intellectual honesty issue to resolve: is the tool actually better, or is it just newer? Pre-register the answer criteria before you look at validation numbers. If Top-5 is within 5pp of KABISA replication, don't claim superiority — claim parity with added transparency and maintenance.
