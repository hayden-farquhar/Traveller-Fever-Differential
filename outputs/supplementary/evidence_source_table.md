# Supplementary Table S1: Evidence Sources for BEACON Symptom Likelihood Matrix

## Description

This table documents the evidence source for every non-false (i.e., informative) cell in the BEACON clinical knowledge base (`cdc_yellow_book_extraction.yaml`). Each row represents a disease-symptom or disease-exposure pair that contributes to the Naive Bayes inference engine.

## Grading Scheme

| Grade | Prevalence Range | Assigned Probability |
|-------|-----------------|---------------------|
| high | >70% among symptomatic cases | P = 0.85 |
| moderate | 30-70% | P = 0.50 |
| low | 5-30% | P = 0.15 |
| false | <5% or absent | P = 0.05 |
| float | Exact published prevalence | As stated |

Float values represent exact prevalences extracted from published cohort studies (principally Bierbrier 2024, Duvignaud 2024, and Bottieau 2007) and are used directly without grade-to-probability conversion.

---

## Evidence Source Table

| Disease | Symptom/Exposure | Value | Source | PMID/Reference |
|---------|-----------------|-------|--------|----------------|
| Chikungunya | fever | 0.687 | Bierbrier 2024 (N=840 confirmed cases) | PMID 38195993 |
| Chikungunya | rash | 0.355 | Bierbrier 2024 (dermatologic) | PMID 38195993 |
| Chikungunya | arthralgia_myalgia | 0.988 | Bierbrier 2024 (musculoskeletal) | PMID 38195993 |
| Chikungunya | gi_symptoms | 0.18 | Bierbrier 2024 (nausea/vomiting) | PMID 38195993 |
| Chikungunya | small_joint_polyarthralgia | 0.90 | Bierbrier 2024 (bilateral small-joint) | PMID 38195993 |
| Chikungunya | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Chikungunya | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Cholera | gi_symptoms | high | CDC Yellow Book 2024 (profuse watery diarrhoea) | CDC Yellow Book 2024, Ch. 4 |
| Cholera | freshwater | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Cholera | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| COVID-19 | fever | moderate | Harrison's Principles 21e (Omicron era ~60%) | Harrison's 21e, Ch. 199 |
| COVID-19 | arthralgia_myalgia | moderate | Harrison's Principles 21e (~40-50%) | Harrison's 21e, Ch. 199 |
| COVID-19 | gi_symptoms | low | Harrison's Principles 21e (10-20% diarrhoea/vomiting) | Harrison's 21e, Ch. 199 |
| COVID-19 | respiratory_symptoms | high | Harrison's Principles 21e (>80% cough, sore throat) | Harrison's 21e, Ch. 199 |
| COVID-19 | neurological_symptoms | low | Harrison's Principles 21e (anosmia/ageusia ~15-20%) | Harrison's 21e, Ch. 199 |
| COVID-19 | productive_cough | 0.15 | Harrison's Principles 21e | Harrison's 21e, Ch. 199 |
| COVID-19 | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Dengue | fever | 0.870 | Duvignaud/Angelo 2024 (N=3,051) | PMID 38951998 |
| Dengue | rash | 0.289 | Duvignaud/Angelo 2024 | PMID 38951998 |
| Dengue | arthralgia_myalgia | 0.83 | Bottieau 2007 (n=64, myalgia/arthralgia combined) | PMID 17220752 |
| Dengue | haemorrhagic_signs | 0.15 | Duvignaud/Angelo 2024 (petechiae ~15%) | PMID 38951998 |
| Dengue | gi_symptoms | 0.42 | Bottieau 2007 (n=64, abdominal symptoms) | PMID 17220752 |
| Dengue | respiratory_symptoms | low | Bottieau 2007 (28%, cough/URI-like prodrome) | PMID 17220752 |
| Dengue | retro_orbital_pain | 0.55 | Duvignaud/Angelo 2024 | PMID 38951998 |
| Dengue | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Dengue | sexual | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Dengue | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis A | fever | moderate | CDC Yellow Book 2024 (60-70% prodromal) | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis A | jaundice | high | CDC Yellow Book 2024 (>70% symptomatic adults) | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis A | gi_symptoms | high | CDC Yellow Book 2024 (>80% anorexia, nausea) | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis A | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Influenza | fever | high | CDC Yellow Book 2024 (>80% sudden onset) | CDC Yellow Book 2024, Ch. 4 |
| Influenza | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (50-60% myalgia) | CDC Yellow Book 2024, Ch. 4 |
| Influenza | gi_symptoms | low | CDC Yellow Book 2024 (10-20%) | CDC Yellow Book 2024, Ch. 4 |
| Influenza | respiratory_symptoms | high | CDC Yellow Book 2024 (>90% cough, sore throat) | CDC Yellow Book 2024, Ch. 4 |
| Influenza | productive_cough | 0.10 | Harrison's Principles 21e (usually dry; productive ~10%) | Harrison's 21e, Ch. 198 |
| Influenza | retro_orbital_pain | 0.05 | Harrison's Principles 21e | Harrison's 21e, Ch. 198 |
| Influenza | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Influenza | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Japanese Encephalitis | fever | high | CDC Yellow Book 2024 (>90%) | CDC Yellow Book 2024, Ch. 4 |
| Japanese Encephalitis | gi_symptoms | moderate | CDC Yellow Book 2024 (vomiting ~40%) | CDC Yellow Book 2024, Ch. 4 |
| Japanese Encephalitis | neurological_symptoms | high | CDC Yellow Book 2024 (encephalitis hallmark) | CDC Yellow Book 2024, Ch. 4 |
| Japanese Encephalitis | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Japanese Encephalitis | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | fever | moderate | CDC Yellow Book 2024 (visceral form ~70%) | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | rash | moderate | CDC Yellow Book 2024 (cutaneous papules/ulcers ~50%) | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | haemorrhagic_signs | low | CDC Yellow Book 2024 (thrombocytopenia in visceral ~15%) | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | gi_symptoms | moderate | CDC Yellow Book 2024 (hepatosplenomegaly ~50%) | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | respiratory_symptoms | low | CDC Yellow Book 2024 (mucosal form rare) | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Leishmaniasis | sandfly | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | fever | high | CDC Yellow Book 2024 (>90%) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | rash | low | CDC Yellow Book 2024 (<10%) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | arthralgia_myalgia | high | CDC Yellow Book 2024 (>80% calf/back myalgia) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | jaundice | low | CDC Yellow Book 2024 (5-10% Weil disease) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | haemorrhagic_signs | low | CDC Yellow Book 2024 (~10% severe) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | gi_symptoms | moderate | CDC Yellow Book 2024 (40-60% nausea, vomiting) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | respiratory_symptoms | moderate | CDC Yellow Book 2024 (20-40% cough, pulmonary) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | neurological_symptoms | low | CDC Yellow Book 2024 (aseptic meningitis ~25%) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | productive_cough | 0.15 | CDC Yellow Book 2024 (pulmonary involvement ~15%) | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | freshwater | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Leptospirosis | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Malaria (P. falciparum) | fever | high | WHO World Malaria Report; Sohail 2024 (>95%) | PMID 38127641 |
| Malaria (P. falciparum) | arthralgia_myalgia | 0.67 | Bottieau 2007 (n=440, myalgia/arthralgia) | PMID 17220752 |
| Malaria (P. falciparum) | jaundice | low | Harrison's Principles 21e (10-15% haemolysis) | Harrison's 21e, Ch. 219 |
| Malaria (P. falciparum) | haemorrhagic_signs | low | Harrison's Principles 21e (thrombocytopenia ~70%, bleeding ~10%) | Harrison's 21e, Ch. 219 |
| Malaria (P. falciparum) | gi_symptoms | 0.56 | Bottieau 2007 (n=440, abdominal symptoms) | PMID 17220752 |
| Malaria (P. falciparum) | respiratory_symptoms | 0.17 | Bottieau 2007 (n=440) | PMID 17220752 |
| Malaria (P. falciparum) | neurological_symptoms | low | Harrison's Principles 21e (cerebral malaria 2-5%) | Harrison's 21e, Ch. 219 |
| Malaria (P. falciparum) | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Malaria (P. falciparum) | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Malaria (P. vivax) | fever | high | WHO; Price 2020 NEJM (>95%) | Price 2020 NEJM; PMID 38127641 |
| Malaria (P. vivax) | arthralgia_myalgia | moderate | Harrison's Principles 21e (30-40%) | Harrison's 21e, Ch. 219 |
| Malaria (P. vivax) | gi_symptoms | moderate | Harrison's Principles 21e (30-40%) | Harrison's 21e, Ch. 219 |
| Malaria (P. vivax) | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Malaria (P. vivax) | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Measles | fever | high | CDC Yellow Book 2024 (>95%) | CDC Yellow Book 2024, Ch. 4 |
| Measles | rash | high | CDC Yellow Book 2024 (>95% maculopapular) | CDC Yellow Book 2024, Ch. 4 |
| Measles | gi_symptoms | low | CDC Yellow Book 2024 (diarrhoea ~8%) | CDC Yellow Book 2024, Ch. 4 |
| Measles | respiratory_symptoms | high | CDC Yellow Book 2024 (>90% cough, coryza, conjunctivitis) | CDC Yellow Book 2024, Ch. 4 |
| Measles | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Meningococcal Disease | fever | high | CDC Yellow Book 2024 (>90%) | CDC Yellow Book 2024, Ch. 4 |
| Meningococcal Disease | haemorrhagic_signs | high | CDC Yellow Book 2024 (>70% petechial/purpuric) | CDC Yellow Book 2024, Ch. 4 |
| Meningococcal Disease | gi_symptoms | moderate | CDC Yellow Book 2024 (30-50% nausea, vomiting) | CDC Yellow Book 2024, Ch. 4 |
| Meningococcal Disease | neurological_symptoms | high | CDC Yellow Book 2024 (>80% meningism) | CDC Yellow Book 2024, Ch. 4 |
| Meningococcal Disease | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Norovirus | fever | low | CDC Yellow Book 2024 (low-grade ~20-30%) | CDC Yellow Book 2024, Ch. 4 |
| Norovirus | gi_symptoms | high | CDC Yellow Book 2024 (>95% vomiting/diarrhoea) | CDC Yellow Book 2024, Ch. 4 |
| Norovirus | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Norovirus | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | fever | moderate | CDC Yellow Book 2024 (~50% of symptomatic) | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (myalgia in prodrome ~40%) | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | gi_symptoms | moderate | CDC Yellow Book 2024 (GI prodrome ~40%) | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | neurological_symptoms | moderate | CDC Yellow Book 2024 (paralytic in ~1% infected) | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Poliomyelitis | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rabies | fever | moderate | CDC Yellow Book 2024 (~50-70% prodromal) | CDC Yellow Book 2024, Ch. 4 |
| Rabies | neurological_symptoms | high | CDC Yellow Book 2024 (paresthesia, hydrophobia, paralysis) | CDC Yellow Book 2024, Ch. 4 |
| Rabies | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | fever | high | CDC Yellow Book 2024 (>90%) | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | rash | 0.63 | Bottieau 2007 (n=70, 63% rash) | PMID 17220752 |
| Rickettsial Diseases | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (~40-50% myalgia) | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | gi_symptoms | low | CDC Yellow Book 2024 (10-20% nausea, vomiting) | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | respiratory_symptoms | low | CDC Yellow Book 2024 (10-20% cough) | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | neurological_symptoms | low | CDC Yellow Book 2024 (~10% encephalitis) | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | tick | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | mite | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | flea | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Rickettsial Diseases | louse | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | fever | high | CDC Yellow Book 2024 (>80% Katayama) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | rash | moderate | CDC Yellow Book 2024 (30-50% cercarial dermatitis) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (~40% myalgia) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | haemorrhagic_signs | low | CDC Yellow Book 2024 (haematuria ~20%) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | gi_symptoms | moderate | CDC Yellow Book 2024 (40-60% diarrhoea, hepatosplenomegaly) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | respiratory_symptoms | moderate | CDC Yellow Book 2024 (30-50% cough, wheeze) | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | productive_cough | low | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Schistosomiasis | freshwater | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | fever | high | CDC Yellow Book 2024 (biphasic; >90%) | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (~40%) | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | gi_symptoms | moderate | CDC Yellow Book 2024 (30-40% nausea, vomiting) | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | neurological_symptoms | high | CDC Yellow Book 2024 (meningitis, encephalitis) | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tick-Borne Encephalitis | tick | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tuberculosis | fever | moderate | CDC Yellow Book 2024 (60-80% subacute) | CDC Yellow Book 2024, Ch. 4 |
| Tuberculosis | haemorrhagic_signs | low | Harrison's Principles 21e (haemoptysis ~20%) | Harrison's 21e, Ch. 173 |
| Tuberculosis | gi_symptoms | moderate | Harrison's Principles 21e (40-60% weight loss, anorexia) | Harrison's 21e, Ch. 173 |
| Tuberculosis | respiratory_symptoms | high | CDC Yellow Book 2024 (>90% prolonged cough) | CDC Yellow Book 2024, Ch. 4 |
| Tuberculosis | productive_cough | 0.70 | Harrison's Principles 21e (chronic productive cough) | Harrison's 21e, Ch. 173 |
| Tuberculosis | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tuberculosis | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Tuberculosis | respiratory_droplet | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | fever | high | CDC Yellow Book 2024 (>95% stepwise) | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | rash | low | CDC Yellow Book 2024 (rose spots ~20-30%) | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (~40% myalgia) | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | gi_symptoms | high | CDC Yellow Book 2024 (>80% abdominal pain) | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | respiratory_symptoms | 0.50 | Bottieau 2007 (n=16, 50% cough/sore throat) | PMID 17220752 |
| Typhoid/Paratyphoid Fever | sexual | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Typhoid/Paratyphoid Fever | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | fever | high | CDC Yellow Book 2024 (>90%) | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (~50% myalgia, backache) | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | jaundice | high | CDC Yellow Book 2024 (hallmark of toxic phase) | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | haemorrhagic_signs | moderate | CDC Yellow Book 2024 (~40% in toxic phase) | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | gi_symptoms | moderate | CDC Yellow Book 2024 (~50% nausea, vomiting) | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Yellow Fever | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Zika | fever | moderate | CDC Yellow Book 2024 (~50-65% low-grade) | CDC Yellow Book 2024, Ch. 4 |
| Zika | rash | moderate | CDC Yellow Book 2024 (50-70% maculopapular) | CDC Yellow Book 2024, Ch. 4 |
| Zika | arthralgia_myalgia | moderate | CDC Yellow Book 2024 (40-60%) | CDC Yellow Book 2024, Ch. 4 |
| Zika | gi_symptoms | low | CDC Yellow Book 2024 (~10%) | CDC Yellow Book 2024, Ch. 4 |
| Zika | neurological_symptoms | low | CDC Yellow Book 2024 (GBS rare) | CDC Yellow Book 2024, Ch. 4 |
| Zika | small_joint_polyarthralgia | 0.30 | CDC Yellow Book 2024 (arthralgia less specific) | CDC Yellow Book 2024, Ch. 4 |
| Zika | mosquito | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Zika | sexual | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Zika | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis B (Acute) | fever | low | Harrison's Principles 21e (~20-30% prodromal) | Harrison's 21e, Ch. 337 |
| Hepatitis B (Acute) | rash | low | Harrison's Principles 21e (serum-sickness-like ~10-20%) | Harrison's 21e, Ch. 337 |
| Hepatitis B (Acute) | arthralgia_myalgia | low | Harrison's Principles 21e (polyarthralgia ~25%) | Harrison's 21e, Ch. 337 |
| Hepatitis B (Acute) | jaundice | moderate | Harrison's Principles 21e (icteric in ~30%) | Harrison's 21e, Ch. 337 |
| Hepatitis B (Acute) | gi_symptoms | moderate | Harrison's Principles 21e (~50% anorexia, nausea) | Harrison's 21e, Ch. 337 |
| Hepatitis B (Acute) | sexual | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis B (Acute) | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis E | fever | moderate | Harrison's Principles 21e (~50% prodromal) | Harrison's 21e, Ch. 337 |
| Hepatitis E | arthralgia_myalgia | low | Harrison's Principles 21e (~20%) | Harrison's 21e, Ch. 337 |
| Hepatitis E | jaundice | high | Harrison's Principles 21e (hallmark; >70%) | Harrison's 21e, Ch. 337 |
| Hepatitis E | gi_symptoms | high | Harrison's Principles 21e (>80% anorexia, nausea) | Harrison's 21e, Ch. 337 |
| Hepatitis E | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis E | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Hepatitis E | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Acute HIV Seroconversion | fever | high | Cohen 2010 NEJM (80-90%) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | rash | moderate | Cohen 2010 NEJM (50-70% maculopapular) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | arthralgia_myalgia | moderate | Cohen 2010 NEJM (50-70% myalgia) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | gi_symptoms | moderate | Cohen 2010 NEJM (30-50% diarrhoea, nausea) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | respiratory_symptoms | moderate | Cohen 2010 NEJM (50-70% pharyngitis) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | neurological_symptoms | low | Cohen 2010 NEJM (headache 30-70%; meningitis rare) | Cohen 2010 NEJM |
| Acute HIV Seroconversion | sexual | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Acute HIV Seroconversion | needle_blood | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Melioidosis | fever | high | Manson's Tropical Diseases 24e (>90% septicaemia) | Manson's 24e, Ch. 42 |
| Melioidosis | rash | low | Manson's Tropical Diseases 24e (skin abscesses ~15%) | Manson's 24e, Ch. 42 |
| Melioidosis | arthralgia_myalgia | low | Manson's Tropical Diseases 24e (septic arthritis uncommon) | Manson's 24e, Ch. 42 |
| Melioidosis | jaundice | low | Manson's Tropical Diseases 24e (~10% hepatosplenic) | Manson's 24e, Ch. 42 |
| Melioidosis | gi_symptoms | moderate | Manson's Tropical Diseases 24e (30-40% abscesses) | Manson's 24e, Ch. 42 |
| Melioidosis | respiratory_symptoms | moderate | Manson's Tropical Diseases 24e (~50% pneumonia) | Manson's 24e, Ch. 42 |
| Melioidosis | neurological_symptoms | low | Manson's Tropical Diseases 24e (brainstem encephalitis ~5%) | Manson's 24e, Ch. 42 |
| Melioidosis | productive_cough | 0.40 | Manson's Tropical Diseases 24e (pneumonia form ~40%) | Manson's 24e, Ch. 42 |
| Melioidosis | freshwater | true | Manson's Tropical Diseases 24e | Manson's 24e, Ch. 42 |
| Melioidosis | animal_contact | true | Manson's Tropical Diseases 24e | Manson's 24e, Ch. 42 |
| Strongyloides (Acute) | fever | low | Manson's Tropical Diseases 24e (~20% larval migration) | Manson's 24e, Ch. 56 |
| Strongyloides (Acute) | rash | moderate | Manson's Tropical Diseases 24e (30-50% larva currens) | Manson's 24e, Ch. 56 |
| Strongyloides (Acute) | gi_symptoms | moderate | Manson's Tropical Diseases 24e (40-60% diarrhoea) | Manson's 24e, Ch. 56 |
| Strongyloides (Acute) | respiratory_symptoms | low | Manson's Tropical Diseases 24e (Loeffler syndrome ~15-20%) | Manson's 24e, Ch. 56 |
| Strongyloides (Acute) | percutaneous_soil | true | Manson's Tropical Diseases 24e | Manson's 24e, Ch. 56 |
| Amoebiasis | fever | high | Manson's Tropical Diseases 24e (70-90% with liver abscess) | Manson's 24e, Ch. 50 |
| Amoebiasis | jaundice | low | Manson's Tropical Diseases 24e (~5-10% biliary) | Manson's 24e, Ch. 50 |
| Amoebiasis | haemorrhagic_signs | moderate | Manson's Tropical Diseases 24e (40-50% bloody diarrhoea) | Manson's 24e, Ch. 50 |
| Amoebiasis | gi_symptoms | high | Manson's Tropical Diseases 24e (>90% RUQ pain, diarrhoea) | Manson's 24e, Ch. 50 |
| Amoebiasis | respiratory_symptoms | low | Manson's Tropical Diseases 24e (~10-15% pleuropulmonary) | Manson's 24e, Ch. 50 |
| Amoebiasis | sexual | true | Manson's Tropical Diseases 24e | Manson's 24e, Ch. 50 |
| Amoebiasis | food_water | true | Manson's Tropical Diseases 24e | Manson's 24e, Ch. 50 |
| Brucellosis | fever | high | Harrison's Principles 21e (>90% undulant fever) | Harrison's 21e, Ch. 170 |
| Brucellosis | arthralgia_myalgia | high | Harrison's Principles 21e (>70% sacroiliitis) | Harrison's 21e, Ch. 170 |
| Brucellosis | jaundice | low | Harrison's Principles 21e (~5-10% granulomatous hepatitis) | Harrison's 21e, Ch. 170 |
| Brucellosis | gi_symptoms | moderate | Harrison's Principles 21e (40-50% hepatosplenomegaly) | Harrison's 21e, Ch. 170 |
| Brucellosis | neurological_symptoms | low | Harrison's Principles 21e (neurobrucellosis ~5%) | Harrison's 21e, Ch. 170 |
| Brucellosis | small_joint_polyarthralgia | 0.30 | Harrison's Principles 21e (sacroiliitis, joint ~30%) | Harrison's 21e, Ch. 170 |
| Brucellosis | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Brucellosis | food_water | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Brucellosis | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e, Ch. 170 |
| Q Fever | fever | high | Harrison's Principles 21e (>90%) | Harrison's 21e, Ch. 182 |
| Q Fever | rash | low | Harrison's Principles 21e (~10%) | Harrison's 21e, Ch. 182 |
| Q Fever | arthralgia_myalgia | moderate | Harrison's Principles 21e (~50% myalgia) | Harrison's 21e, Ch. 182 |
| Q Fever | jaundice | low | Harrison's Principles 21e (~10-15% granulomatous hepatitis) | Harrison's 21e, Ch. 182 |
| Q Fever | gi_symptoms | moderate | Harrison's Principles 21e (30-40% hepatitis, nausea) | Harrison's 21e, Ch. 182 |
| Q Fever | respiratory_symptoms | moderate | Harrison's Principles 21e (30-50% atypical pneumonia) | Harrison's 21e, Ch. 182 |
| Q Fever | neurological_symptoms | low | Harrison's Principles 21e (headache common; meningoencephalitis rare) | Harrison's 21e, Ch. 182 |
| Q Fever | productive_cough | low | Harrison's Principles 21e | Harrison's 21e, Ch. 182 |
| Q Fever | animal_contact | true | CDC Yellow Book 2024 | CDC Yellow Book 2024, Ch. 4 |
| Q Fever | food_water | true | Harrison's Principles 21e | Harrison's 21e, Ch. 182 |
| Q Fever | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e, Ch. 182 |
| Q Fever | tick | true | Harrison's Principles 21e | Harrison's 21e, Ch. 182 |
| Mpox | fever | moderate | Thornhill 2022 NEJM (~60% prodromal) | Thornhill 2022 NEJM |
| Mpox | rash | high | Thornhill 2022 NEJM (>95% vesiculopustular) | Thornhill 2022 NEJM |
| Mpox | arthralgia_myalgia | moderate | Thornhill 2022 NEJM (~40%) | Thornhill 2022 NEJM |
| Mpox | gi_symptoms | low | Thornhill 2022 NEJM (proctitis ~15-20%) | Thornhill 2022 NEJM |
| Mpox | respiratory_symptoms | low | Thornhill 2022 NEJM (pharyngitis ~15%) | Thornhill 2022 NEJM |
| Mpox | animal_contact | true | WHO Fact Sheet: Mpox | WHO Fact Sheet |
| Mpox | sexual | true | Thornhill 2022 NEJM | Thornhill 2022 NEJM |
| Mpox | respiratory_droplet | true | WHO Fact Sheet: Mpox | WHO Fact Sheet |
| Oropouche | fever | high | WHO Fact Sheet: Oropouche (>90%) | WHO Fact Sheet |
| Oropouche | rash | low | WHO Fact Sheet: Oropouche (~10-15%) | WHO Fact Sheet |
| Oropouche | arthralgia_myalgia | high | WHO Fact Sheet: Oropouche (>80%) | WHO Fact Sheet |
| Oropouche | haemorrhagic_signs | low | WHO Fact Sheet: Oropouche (~5-10% petechiae) | WHO Fact Sheet |
| Oropouche | gi_symptoms | moderate | WHO Fact Sheet: Oropouche (30-50%) | WHO Fact Sheet |
| Oropouche | neurological_symptoms | low | WHO Fact Sheet: Oropouche (meningoencephalitis ~5%) | WHO Fact Sheet |
| Oropouche | small_joint_polyarthralgia | 0.60 | WHO Fact Sheet: Oropouche (prominent arthralgia ~60%) | WHO Fact Sheet |
| Oropouche | midge | true | WHO Fact Sheet: Oropouche | WHO Fact Sheet |
| Oropouche | mosquito_secondary | true | WHO Fact Sheet: Oropouche | WHO Fact Sheet |
| Acute Bacterial Gastroenteritis | fever | moderate | Harrison's Principles 21e (~50% invasive pathogens) | Harrison's 21e, Ch. 128 |
| Acute Bacterial Gastroenteritis | arthralgia_myalgia | low | Harrison's Principles 21e (~15-20%) | Harrison's 21e, Ch. 128 |
| Acute Bacterial Gastroenteritis | haemorrhagic_signs | low | Harrison's Principles 21e (bloody diarrhoea ~15-20%) | Harrison's 21e, Ch. 128 |
| Acute Bacterial Gastroenteritis | gi_symptoms | high | Harrison's Principles 21e (>95% diarrhoea, cramps) | Harrison's 21e, Ch. 128 |
| Acute Bacterial Gastroenteritis | animal_contact | true | Harrison's Principles 21e | Harrison's 21e, Ch. 128 |
| Acute Bacterial Gastroenteritis | food_water | true | Harrison's Principles 21e | Harrison's 21e, Ch. 128 |
| Community-Acquired Pneumonia | fever | high | Harrison's Principles 21e (>85%) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | arthralgia_myalgia | low | Harrison's Principles 21e (~20%) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | gi_symptoms | low | Harrison's Principles 21e (10-20% atypical organisms) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | respiratory_symptoms | high | Harrison's Principles 21e (>95% cough, dyspnoea) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | neurological_symptoms | low | Harrison's Principles 21e (confusion ~10%) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | productive_cough | 0.80 | Harrison's Principles 21e (>80% productive sputum) | Harrison's 21e, Ch. 121 |
| Community-Acquired Pneumonia | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e, Ch. 121 |
| UTI/Pyelonephritis | fever | high | Harrison's Principles 21e (>85% in pyelonephritis) | Harrison's 21e, Ch. 130 |
| UTI/Pyelonephritis | arthralgia_myalgia | low | Harrison's Principles 21e (malaise ~20%) | Harrison's 21e, Ch. 130 |
| UTI/Pyelonephritis | gi_symptoms | moderate | Harrison's Principles 21e (40-60% nausea, vomiting) | Harrison's 21e, Ch. 130 |
| UTI/Pyelonephritis | sexual | true | Harrison's Principles 21e | Harrison's 21e, Ch. 130 |
| Viral URTI | fever | low | Harrison's Principles 21e (~20-30% low-grade) | Harrison's 21e, Ch. 31 |
| Viral URTI | arthralgia_myalgia | low | Harrison's Principles 21e (~15-20% mild) | Harrison's 21e, Ch. 31 |
| Viral URTI | respiratory_symptoms | high | Harrison's Principles 21e (>95% rhinorrhoea, sore throat) | Harrison's 21e, Ch. 31 |
| Viral URTI | productive_cough | 0.05 | Harrison's Principles 21e | Harrison's 21e, Ch. 31 |
| Viral URTI | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e, Ch. 31 |
| Infectious Mononucleosis | fever | high | Harrison's Principles 21e (>80% prolonged) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | rash | low | Harrison's Principles 21e (~5% spontaneous) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | arthralgia_myalgia | moderate | Harrison's Principles 21e (40-60% fatigue, myalgia) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | jaundice | low | Harrison's Principles 21e (hepatitis 5-10%) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | gi_symptoms | moderate | Harrison's Principles 21e (30-50% hepatosplenomegaly) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | respiratory_symptoms | high | Harrison's Principles 21e (>80% pharyngitis, tonsillar exudate) | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | sexual | true | Harrison's Principles 21e | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | needle_blood | true | Harrison's Principles 21e | Harrison's 21e, Ch. 189 |
| Infectious Mononucleosis | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e, Ch. 189 |
| Undifferentiated Viral Syndrome | fever | moderate | Harrison's Principles 21e (present but non-specific) | Harrison's 21e |
| Undifferentiated Viral Syndrome | rash | low | Harrison's Principles 21e (nonspecific exanthem ~15%) | Harrison's 21e |
| Undifferentiated Viral Syndrome | arthralgia_myalgia | low | Harrison's Principles 21e (mild ~20%) | Harrison's 21e |
| Undifferentiated Viral Syndrome | gi_symptoms | low | Harrison's Principles 21e (mild ~15%) | Harrison's 21e |
| Undifferentiated Viral Syndrome | respiratory_symptoms | low | Harrison's Principles 21e (mild URTI ~20%) | Harrison's 21e |
| Undifferentiated Viral Syndrome | mosquito | true | Harrison's Principles 21e | Harrison's 21e |
| Undifferentiated Viral Syndrome | respiratory_droplet | true | Harrison's Principles 21e | Harrison's 21e |

---

## Key References

1. Bierbrier R, et al. Clinical spectrum of chikungunya in travellers: a GeoSentinel analysis. *J Travel Med*. 2024;31(2):taae014. **PMID 38195993**
2. Duvignaud A, Angelo KM, et al. GeoSentinel analysis of dengue clinical presentation 2007-2022. *J Travel Med*. 2024;31(5):taae073. **PMID 38951998**
3. Bottieau E, et al. Fever after a stay in the tropics: diagnostic predictors of the leading tropical conditions. *Medicine*. 2007;86(1):18-25. **PMID 17220752**
4. Sohail A, et al. Global malaria trends 2010-2022. *Lancet Infect Dis*. 2024;24(5):e320-e332. **PMID 38127641**
5. Cohen MS, et al. Acute HIV-1 infection. *N Engl J Med*. 2011;364(20):1943-1954.
6. Thornhill JP, et al. Monkeypox virus infection in humans across 16 countries. *N Engl J Med*. 2022;387(8):679-691.
7. Price RN, et al. Vivax malaria. *N Engl J Med*. 2020;383(16):1561-1572.
8. CDC. *CDC Yellow Book 2024: Health Information for International Travel*. Oxford University Press; 2023.
9. Loscalzo J, Fauci AS, Kasper DL, et al., eds. *Harrison's Principles of Internal Medicine*. 21st ed. McGraw-Hill; 2022.
10. Farrar J, et al., eds. *Manson's Tropical Diseases*. 24th ed. Elsevier; 2024.
11. World Health Organization. Disease Outbreak News and Fact Sheets. https://www.who.int/emergencies/disease-outbreak-news

---

*Table generated: 2026-04-20 | Total informative cells: 204 | Diseases: 38*
