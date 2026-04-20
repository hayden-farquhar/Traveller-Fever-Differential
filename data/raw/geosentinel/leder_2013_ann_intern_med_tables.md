# Leder et al. 2013 Ann Intern Med — Extracted Tables

**Source:** Leder K, Torresi J, Libman MD, et al. "GeoSentinel Surveillance of Illness in Returned Travelers, 2007-2011." Ann Intern Med 158(6):456-68.
**PMID:** 23552375 | **DOI:** 10.7326/0003-4819-158-6-201303190-00005 | **PMC:** PMC4629801
**Access date:** 2026-04-18

---

## Table 1: Region × Syndrome Category (% of travellers, N=42,173)

| Region | Total % | GI % | Febrile % | Dermatologic % | Respiratory % | Neurologic % | GU/STI % |
|--------|---------|------|-----------|----------------|---------------|--------------|----------|
| Southeast Asia | 16.3 | 13.8 | 18.1 | 22.0 | 17.4 | 10.1 | 17.3 |
| South-Central Asia | 13.6 | 19.1 | 13.2 | 9.1 | 10.6 | 7.6 | 11.1 |
| Northeast Asia | 2.7 | 2.2 | 1.2 | 2.9 | 5.8 | 3.2 | 2.4 |
| Europe | 4.7 | 3.5 | 2.1 | 4.7 | 10.1 | 9.3 | 7.4 |
| Latin America/Caribbean | 19.2 | 20.4 | 14.3 | 27.3 | 14.2 | 23.6 | 15.6 |
| Middle East/North Africa | 6.1 | 8.7 | 2.5 | 5.6 | 5.2 | 6.5 | 6.1 |
| North America | 1.5 | 0.5 | 0.4 | 1.6 | 5.3 | 2.9 | 2.1 |
| Oceania | 0.8 | 0.7 | 1.0 | 1.2 | 0.9 | 1.4 | 0.5 |
| Sub-Saharan Africa | 26.7 | 22.5 | 42.6 | 19.5 | 20.6 | 22.3 | 26.9 |
| Australia/New Zealand | 0.5 | 0.2 | 0.2 | 0.7 | 1.8 | 0.7 | 0.6 |

**Total syndrome breakdown:** GI 34.0%, Febrile 23.3%, Dermatologic 19.5%, Respiratory 10.9%, GU/STI 2.9%, Neurologic 1.7%

## Table 1: Syndrome Counts

| Category | Travellers | Diagnoses |
|----------|-----------|-----------|
| GI | 14,346 (34.0%) | 14,837 |
| Febrile | 9,817 (23.3%) | 10,092 |
| Dermatologic | 8,227 (19.5%) | 9,669 |
| Respiratory | 4,613 (10.9%) | 4,851 |
| GU/STI/Gyn | 1,209 (2.9%) | 1,260 |
| Neurologic | 724 (1.7%) | 738 |

## Table 3: Key Specific Diagnoses (case counts from 42,173 travellers)

### Febrile illnesses (critical for our model)

| Diagnosis | Cases | % with pretravel visit |
|-----------|-------|----------------------|
| Malaria (P. falciparum) | 1,990 | 27.4% |
| Dengue | 1,473 | 36.9% |
| Enteric fever | 467 | 30.5% |
| Spotted fever rickettsia | 267 | 44.6% |
| Chikungunya | 164 | 29.9% |

### GI infections

| Diagnosis | Cases | % with pretravel visit |
|-----------|-------|----------------------|
| Giardia | 1,426 | 53.9% |
| Campylobacter | 753 | 53.3% |
| Strongyloides | 483 | 37.1% |
| E. histolytica | 340 | 41.5% |

### Dermatologic

| Diagnosis | Cases | % with pretravel visit |
|-----------|-------|----------------------|
| Rabies PEP | 1,249 | 25.5% |
| Cutaneous larva migrans | 806 | 42.1% |
| Cutaneous leishmaniasis | 264 | 49.6% |

## Table 4: Deaths (N=28)

| Cause | Deaths |
|-------|--------|
| Malaria (P. falciparum) | 7 (25%) |
| Dengue | 3 |
| Melioidosis | 2 |
| Pneumonia/respiratory | 6 |
| Other infections/sepsis | 10 |

## Notes for model building

- This table provides SYNDROME × REGION but NOT DIAGNOSIS × REGION cross-tab
- For diagnosis-specific regional priors, we need the supplementary materials from this paper
- The full paper likely has supplementary tables or appendix with diagnosis × region breakdowns
- Region definitions: GeoSentinel regions (not country-level)
- Key limitation: these are proportionate morbidity ratios, not incidence rates (no denominator of healthy travellers)
