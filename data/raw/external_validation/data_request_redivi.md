# Data Request: +REDIVI Febrile Returned Traveller Dataset

**To:** Pedro Guevara-Hernández (pegueiher@gmail.com), corresponding author
**CC:** José A. Pérez-Molina (senior author / +REDIVI network)
**From:** Hayden Farquhar MBBS MPHTM
**Date:** [TO BE SENT]
**Subject:** Data sharing request — external validation of a returned-traveller fever diagnostic tool using +REDIVI data

---

Dear Dr Guevara-Hernández and colleagues,

I am writing to request access to anonymised data from the +REDIVI febrile syndrome cohort for external validation of an open-source diagnostic tool.

## Our project

We have developed an Australian-weighted Bayesian diagnostic differential for febrile returned travellers, pre-registered on OSF (https://doi.org/10.17605/OSF.IO/MA6YD). The tool uses GeoSentinel destination priors reweighted by Australian imported-case distributions, graded symptom likelihoods, and monthly-updated outbreak signals from WHO Disease Outbreak News. It covers 33 diagnoses and includes an explicit abstention mechanism.

On our internal validation set (18 Australian cases), the model achieves 78% Top-1 and 100% Top-5 accuracy, outperforming a KABISA TRAVEL replication (39% Top-1, 89% Top-5) on the same cases. We now need external validation on an independent, larger dataset — and the +REDIVI febrile syndrome cohort described in your 2025 paper (DOI: 10.1016/j.tmaid.2025.102790) is the best available resource for this.

## Why +REDIVI

Your cohort of 4,186 febrile cases with confirmed diagnoses across 13 years is, to our knowledge, the largest available individual-level febrile returned-traveller dataset. Validation against a European (Spanish) population would directly test whether our model generalises beyond the Australian traveller population for which it was calibrated — this is itself a valuable finding regardless of the result.

## Data requested

We understand that data sharing constraints vary. We have structured our request in tiers — even the minimum tier would be highly valuable:

**Tier 1 (minimum viable — no clinical data needed):**
- Destination country or region of travel
- Final aetiological diagnosis (confirmed/probable/possible)
- Type of traveller (tourist, VFR, migrant)

This would allow us to test the model's prior calibration and Top-1/Top-5 accuracy using destination + diagnosis alone (no symptom data needed — the model would use destination priors only).

**Tier 2 (adds clinical discrimination):**
- All of Tier 1, plus:
- Clinical presentation category (febrile syndrome subtype, if recorded)
- Time from return to consultation (incubation proxy)

**Tier 3 (full validation):**
- All of Tier 2, plus:
- Individual symptom/sign data (fever pattern, rash, jaundice, GI, respiratory, neurological, haemorrhagic)
- Exposure history (mosquito, freshwater, animal contact, food/water, sexual)

We do NOT require patient identifiers, dates of birth, exact dates, or centre-level identifiers.

## What we offer in return

- We are happy to include +REDIVI collaborators as **co-authors** on the validation analysis, or to acknowledge the network as data providers — whichever you prefer.
- We will share all validation results and analysis code with the +REDIVI team **prior to publication** for review and comment.
- Our analysis code is open-source and will be publicly available on GitHub.
- We will provide a **formal data sharing agreement** if required by your institutions or ethics committees.

## About me

I am an independent researcher (MBBS, Master of Public Health and Tropical Medicine) based in regional New South Wales, Australia. I have no institutional affiliation, competing interests, or industry funding. This project is one of a portfolio of public health and clinical informatics research projects. The tool is designed as a clinical decision support aid for rural Australian emergency departments with limited access to infectious disease specialists.

- ORCID: 0009-0002-6226-440X
- Email: hayden.farquhar@icloud.com
- Pre-registration: https://doi.org/10.17605/OSF.IO/MA6YD

I would be grateful for any level of data sharing that is feasible within your governance framework. Even Tier 1 data alone would make this the largest external validation of a returned-traveller fever diagnostic tool to date.

Thank you for considering this request. I greatly admire the +REDIVI network's contribution to imported infectious disease surveillance and would welcome the opportunity to collaborate.

Kind regards,

Hayden Farquhar MBBS MPHTM
