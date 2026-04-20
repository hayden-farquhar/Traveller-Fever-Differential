# GeoSentinel Data Extraction Notes

**Date:** 2026-04-18

## Papers identified and verified via PubMed

### Primary derivation papers

1. **Leder et al. 2013** — "GeoSentinel Surveillance of Illness in Returned Travelers, 2007-2011"
   - *Ann Intern Med* 158(6):456-68
   - PMID: 23552375 | PMC: PMC4629801
   - DOI: 10.7326/0003-4819-158-6-201303190-00005
   - **Key data:** Destination-syndrome conditionals for 42,173 ill returned travellers across 53 sites in 24 countries. Asia 32.6%, sub-Saharan Africa 26.7%. Tables contain region × diagnosis frequencies.
   - **Extraction method:** Tables are likely image-based in PMC. Will need PDF download + tabula-py extraction.
   - **Access date:** 2026-04-18 (abstract/metadata via PubMed API)

2. **Leder et al. 2013** — "Travel-associated illness trends and clusters, 2000-2010"
   - *Emerg Infect Dis* 19(7):1049-73
   - PMID: 23763775 | PMC: PMC3713975
   - DOI: 10.3201/eid1907.121573
   - **Key data:** Longitudinal trend data for 42,223 ill travellers over 2000-2010 from 18 GeoSentinel sites. PM trends for malaria (decreasing), enteric fever and dengue (increasing). Case clustering detection.
   - **Access date:** 2026-04-18

3. **Bierbrier et al. 2024** — "Chikungunya infection in returned travellers: results from the GeoSentinel network, 2005-2020"
   - *J Travel Med* 31(2)
   - PMID: 38195993 | PMC: PMC11081466
   - DOI: 10.1093/jtm/taae005
   - **Key data:** 1,202 chikungunya travellers. Caribbean 28.9%, SE Asia 22.8%, South Central Asia 14.2%, South America 14.2%. Symptoms: musculoskeletal 98.8%, fever/chills 68.7%, dermatologic 35.5%. Full text retrieved.
   - **Access date:** 2026-04-18 (full text via PMC API)

4. **Duvignaud/Angelo et al. 2024** — "Epidemiology of travel-associated dengue from 2007 to 2022: A GeoSentinel analysis"
   - *J Travel Med* 31(7)
   - PMID: 38951998 | PMC: PMC11502266
   - DOI: 10.1093/jtm/taae089
   - **Key data:** 5,958 dengue travellers. SE Asia 50.4%, South Central Asia 14.9%, Caribbean 10.9%, South America 9.2%. Severe dengue in 1.6%. More comprehensive than older refs for dengue-specific priors.
   - **Access date:** 2026-04-18

5. **Brown/Angelo et al. 2023** — "Travel-Related Diagnoses Among U.S. Nonmigrant Travelers, GeoSentinel 2012-2021"
   - *MMWR Surveill Summ* 72(7):1-22
   - PMID: 37368820 | PMC: PMC10332343
   - DOI: 10.15585/mmwr.ss7207a1
   - **Key data:** Most comprehensive recent GeoSentinel analysis. 9,859 nonmigrant travellers. Region × diagnosis breakdowns. Replaces the "Angelo 2017" paper originally planned (which could not be located).
   - **Access date:** 2026-04-18

### Papers NOT found as cited in original project plan

- **"Angelo 2017, J Travel Med"** — No matching paper found. PMID 28329385 (listed in plan) is a cardiology paper. The Brown/Angelo 2023 MMWR (above) is the best substitute for region × diagnosis data.
- **"Hamer 2016 Zika"** — PMID 27496394 (listed in plan) is an SSB/asthma paper. The Hamer 2020 GeoSentinel review (PMID 33247586, DOI 10.1093/jtm/taaa219) discusses Zika in the context of GeoSentinel sentinel detection but does not provide Zika-specific priors. A dedicated Zika-specific GeoSentinel paper may exist but was not located.

## Tables requiring extraction

The following tables need to be extracted from PDFs using tabula-py:
- Leder 2013 Ann Intern Med: Tables 1-4 (region × diagnosis frequencies)
- Leder 2013 EID: Tables and supplementary materials
- Brown/Angelo 2023 MMWR: Tables (region × diagnosis, 2012-2021)

## Next steps

- Download PDFs for table extraction (requires journal access or open-access PDF links)
- Extract tables using tabula-py
- Reconcile across papers to build destination_priors.yaml
