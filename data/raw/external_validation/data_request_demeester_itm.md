# Data Request: Demeester 2011 KABISA TRAVEL Validation Dataset

**To:** Jozef Van den Ende, MD, PhD (jvdende@itg.be), corresponding author
**CC:** Emmanuel Bottieau (ebottieau@itg.be), Institute of Tropical Medicine, Antwerp
**From:** Hayden Farquhar MBBS MPHTM
**Date:** [TO BE SENT]
**Subject:** Data sharing request — paired validation of a new returned-traveller fever tool against KABISA TRAVEL on the Demeester 2011 dataset

---

Dear Professor Van den Ende and colleagues,

I am writing to request access to the individual case dataset from your 2011 prospective evaluation of KABISA TRAVEL (DOI: 10.1111/j.1708-8305.2011.00566.x), for the purpose of a direct paired comparison with a new open-source diagnostic tool.

## Context

KABISA TRAVEL is the most rigorously validated diagnostic decision support system for febrile returned travellers in the published literature. Your 205-case multicenter dataset remains, to our knowledge, the gold-standard validation set for this clinical problem. We believe a head-to-head comparison on the same cases — rather than on separate case sets with different populations — would be the most scientifically robust way to benchmark a new tool.

## Our project

We have developed an Australian-weighted Bayesian diagnostic differential for febrile returned travellers, pre-registered on OSF (https://doi.org/10.17605/OSF.IO/MA6YD). It covers 33 diagnoses and uses:

- GeoSentinel destination-diagnosis priors reweighted by Australian imported-case distributions
- Graded symptom likelihoods calibrated against published prevalence data (Bierbrier 2024, Duvignaud 2024)
- Monthly-updated live outbreak priors from WHO Disease Outbreak News
- Explicit abstention when the model cannot discriminate

On our internal validation set (18 Australian cases), the model achieves 78% Top-1 and 100% Top-5 accuracy, outperforming our rule-based KABISA replication (39% Top-1, 89% Top-5). However, our validation set is small and partly composed of representative profiles rather than extracted cases. A paired comparison on your 205 confirmed-diagnosis cases would be far more compelling.

## What we found in your paper

From Table 2, we note that KABISA achieves 72% Top-1 and 88% Top-5 overall, with particular strengths in falciparum malaria (92% Top-1) and dengue (92% Top-1), but lower accuracy for chikungunya (0% Top-1), mononucleosis-like syndrome (8% Top-1), and leptospirosis (50% Top-1). Our model appears to perform well on several of these historically difficult categories, making a paired comparison especially informative.

## Data requested

For each of the 205 confirmed-diagnosis cases, we request:

**Minimum viable (destination + diagnosis only):**
- Destination region or country of travel
- Final reference diagnosis
- KABISA TRAVEL's Top-1 and Top-5 ranked diagnoses (if recorded)

**Ideal (adds clinical features for full model evaluation):**
- All of the above, plus:
- Clinical findings entered into KABISA (symptoms, signs, laboratory results)
- Incubation period (time from return to symptom onset)
- Type of traveller (tourist, VFR, migrant, expatriate)
- Age and sex

We do NOT require patient identifiers, exact dates, or centre-level identifiers.

## What we offer in return

- **Co-authorship** on the paired comparison analysis for any ITM collaborators who wish to contribute, or acknowledgement as data providers — your preference
- We will share all results and analysis code with your team **prior to publication**
- We will explicitly acknowledge KABISA TRAVEL as the benchmark standard and frame our work as building on the foundation KABISA established
- Our analysis code is open-source and will cite your work prominently
- We are happy to sign a **formal data sharing agreement** if required

## Why this matters

The field of returned-traveller fever diagnostics has few validated tools. A paired comparison between KABISA (rule-based expert system, 2008) and our model (Bayesian with live-updated priors, 2026) on the same case set would document how the field has progressed in 18 years, and whether newer approaches genuinely improve on the standard you set. We believe this would be valuable for the travel medicine community regardless of which system performs better.

## About me

I am an independent researcher (MBBS, Master of Public Health and Tropical Medicine) based in rural New South Wales, Australia. I have no institutional affiliation, competing interests, or industry funding. This tool is designed for rural Australian emergency departments where infectious disease consultation is hours away.

- ORCID: 0009-0002-6226-440X
- Email: hayden.farquhar@icloud.com
- Pre-registration: https://doi.org/10.17605/OSF.IO/MA6YD

Thank you for considering this request. KABISA TRAVEL's contribution to travel medicine education and clinical decision support has been foundational, and I would be honoured to collaborate with your group.

Kind regards,

Hayden Farquhar MBBS MPHTM
