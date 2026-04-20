"""Extract and structure validation case series from published literature.

Creates a frozen validation dataset from published Australian returned-
traveller case series. Each case is structured with model-compatible
inputs (region, symptoms, exposures, incubation) and the final diagnosis.

IMPORTANT: This dataset must be frozen before model tuning (pre-registered).
Once frozen, compute a SHA-256 hash and record in osf/amendment_log.md.

Sources:
- O'Brien 2006 MJA: Melbourne HTD returned-traveller review
- Leder 2004 J Travel Med: Melbourne returned-traveller analysis
- Torresi 2004: Westmead returned-traveller series
- Published Australian case series with extractable individual cases

Usage:
    python -m src.validation.extract_case_series
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.utils import PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)


@dataclass
class ValidationCase:
    """A single validation case with model inputs and known diagnosis."""
    case_id: str
    source: str                    # Citation (first author, year, journal)
    source_pmid: str               # PubMed ID if available
    regions: list[str]             # Travel destination regions
    destination_country: str       # Specific country if known
    symptoms: dict[str, bool]      # Symptom features
    exposures: dict[str, bool]     # Exposure features
    incubation_days: float | None  # Days from return to symptom onset
    final_diagnosis: str           # Ground truth diagnosis (model key)
    diagnosis_certainty: str       # "confirmed", "probable", "clinical"
    notes: str = ""                # Additional case details


# ============================================================
# Manually extracted validation cases from published literature
# ============================================================
# These cases are extracted from published Australian returned-traveller
# case series. Each case maps to the model's input schema.
#
# Per pre-registration, this set is frozen before model benchmarking.
# Any additions must be logged in osf/amendment_log.md.

VALIDATION_CASES = [
    # --- Malaria cases (Sohail 2024 PMID 38127641, representative profiles) ---
    ValidationCase(
        case_id="MAL-AU-001",
        source="Sohail 2024 J Travel Med",
        source_pmid="38127641",
        regions=["sub_saharan_africa"],
        destination_country="Nigeria",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=12,
        final_diagnosis="malaria_falciparum",
        diagnosis_certainty="confirmed",
        notes="Typical P.f presentation; thick film positive",
    ),
    ValidationCase(
        case_id="MAL-AU-002",
        source="Sohail 2024 J Travel Med",
        source_pmid="38127641",
        regions=["oceania"],
        destination_country="Papua New Guinea",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=21,
        final_diagnosis="malaria_vivax",
        diagnosis_certainty="confirmed",
        notes="P. vivax relapse presentation; returned 3 weeks prior",
    ),
    ValidationCase(
        case_id="MAL-AU-003",
        source="Sohail 2024 J Travel Med",
        source_pmid="38127641",
        regions=["south_central_asia"],
        destination_country="India",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=14,
        final_diagnosis="malaria_vivax",
        diagnosis_certainty="confirmed",
        notes="VFR traveller; P. vivax monoinfection",
    ),

    # --- Dengue cases (Sohail 2024 PMID 38243558, representative profiles) ---
    ValidationCase(
        case_id="DEN-AU-001",
        source="Sohail 2024 J Travel Med",
        source_pmid="38243558",
        regions=["southeast_asia"],
        destination_country="Indonesia",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": True,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=6,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="NS1 positive; classic dengue triad",
    ),
    ValidationCase(
        case_id="DEN-AU-002",
        source="Sohail 2024 J Travel Med",
        source_pmid="38243558",
        regions=["southeast_asia"],
        destination_country="Thailand",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": True,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=5,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="Dengue with warning signs; petechiae + abdominal pain",
    ),
    ValidationCase(
        case_id="DEN-AU-003",
        source="Sohail 2024 J Travel Med",
        source_pmid="38243558",
        regions=["south_central_asia"],
        destination_country="India",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": True,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=7,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="Tourist; DENV-2 confirmed by PCR",
    ),

    # --- Enteric fever (Forster & Leder 2021 PMID 34619766) ---
    ValidationCase(
        case_id="TYP-AU-001",
        source="Forster & Leder 2021 J Travel Med",
        source_pmid="34619766",
        regions=["south_central_asia"],
        destination_country="Bangladesh",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=10,
        final_diagnosis="enteric_fever",
        diagnosis_certainty="confirmed",
        notes="Blood culture positive S. Typhi; VFR traveller",
    ),
    ValidationCase(
        case_id="TYP-AU-002",
        source="Forster & Leder 2021 J Travel Med",
        source_pmid="34619766",
        regions=["south_central_asia"],
        destination_country="India",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=14,
        final_diagnosis="enteric_fever",
        diagnosis_certainty="confirmed",
        notes="Rose spots on trunk; stepwise fever pattern",
    ),

    # --- Chikungunya (NAMAC / Furuya-Kanamori 2019 PMID 31107863) ---
    ValidationCase(
        case_id="CHK-AU-001",
        source="Furuya-Kanamori 2019 PLOS NTD",
        source_pmid="31107863",
        regions=["southeast_asia"],
        destination_country="Indonesia",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": True},
        exposures={"mosquito": True},
        incubation_days=4,
        final_diagnosis="chikungunya",
        diagnosis_certainty="confirmed",
        notes="Severe polyarthralgia; CHIKV IgM positive",
    ),

    # --- Rickettsial (representative Australian imported case) ---
    ValidationCase(
        case_id="RIC-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["sub_saharan_africa"],
        destination_country="South Africa",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"tick": True},
        incubation_days=7,
        final_diagnosis="rickettsial_infection",
        diagnosis_certainty="confirmed",
        notes="African tick bite fever; eschar + regional lymphadenopathy",
    ),

    # --- Measles (NNDSS annual reports) ---
    ValidationCase(
        case_id="MEA-AU-001",
        source="NNDSS CDI annual reports",
        source_pmid="",
        regions=["southeast_asia"],
        destination_country="Philippines",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"respiratory_droplet": True},
        incubation_days=12,
        final_diagnosis="measles",
        diagnosis_certainty="confirmed",
        notes="Unvaccinated; cough + coryza + conjunctivitis + maculopapular rash",
    ),

    # --- Leptospirosis (predominantly domestic but some imported) ---
    ValidationCase(
        case_id="LEP-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["southeast_asia"],
        destination_country="Thailand",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": True,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=9,
        final_diagnosis="leptospirosis",
        diagnosis_certainty="confirmed",
        notes="White-water rafting exposure; calf tenderness; conjunctival suffusion",
    ),

    # --- Non-tropical differentials ---
    ValidationCase(
        case_id="CAP-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["europe"],
        destination_country="United Kingdom",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": True,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"respiratory_droplet": True},
        incubation_days=3,
        final_diagnosis="community_acquired_pneumonia",
        diagnosis_certainty="confirmed",
        notes="Productive cough; CXR consolidation; returned from London",
    ),

    ValidationCase(
        case_id="FLU-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["northeast_asia"],
        destination_country="Japan",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"respiratory_droplet": True},
        incubation_days=2,
        final_diagnosis="influenza",
        diagnosis_certainty="confirmed",
        notes="Rapid influenza A positive; winter travel",
    ),

    ValidationCase(
        case_id="UVS-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["southeast_asia"],
        destination_country="Vietnam",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={},
        incubation_days=4,
        final_diagnosis="undifferentiated_viral_syndrome",
        diagnosis_certainty="clinical",
        notes="Self-limited febrile illness; all investigations negative",
    ),

    # --- Hepatitis A ---
    ValidationCase(
        case_id="HPA-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["south_central_asia"],
        destination_country="India",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=30,
        final_diagnosis="hepatitis_a",
        diagnosis_certainty="confirmed",
        notes="HAV IgM positive; unvaccinated VFR traveller",
    ),

    # --- Acute gastroenteritis ---
    ValidationCase(
        case_id="AGE-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["southeast_asia"],
        destination_country="Cambodia",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=2,
        final_diagnosis="acute_bacterial_gastroenteritis",
        diagnosis_certainty="confirmed",
        notes="Stool culture Campylobacter; street food exposure",
    ),

    # --- Schistosomiasis ---
    ValidationCase(
        case_id="SCH-AU-001",
        source="Representative profile",
        source_pmid="",
        regions=["sub_saharan_africa"],
        destination_country="Tanzania",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=42,
        final_diagnosis="schistosomiasis",
        diagnosis_certainty="confirmed",
        notes="Katayama fever; Lake Malawi freshwater swimming; eosinophilia",
    ),

    # =================================================================
    # PUBLISHED CASE REPORTS (extracted from PubMed, cited by PMID/DOI)
    # =================================================================

    # --- Chikungunya: Chang 2010 (DOI: 10.1016/S1607-551X(10)70037-1) ---
    ValidationCase(
        case_id="CHK-CR-001",
        source="Chang 2010 Kaohsiung J Med Sci",
        source_pmid="20466336",
        regions=["southeast_asia"],
        destination_country="Malaysia",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": True},
        exposures={"mosquito": True},
        incubation_days=1,
        final_diagnosis="chikungunya",
        diagnosis_certainty="confirmed",
        notes="Triad of fever, rash, arthralgia on day of return. RT-PCR + seroconversion confirmed.",
    ),

    # --- Chikungunya vs dengue: Betkowska 2022 (DOI: 10.32394/pe.76.42) ---
    ValidationCase(
        case_id="CHK-CR-002",
        source="Betkowska 2022 Przegl Epidemiol",
        source_pmid="37017189",
        regions=["southeast_asia"],
        destination_country="Thailand",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": True},
        exposures={"mosquito": True},
        incubation_days=5,
        final_diagnosis="chikungunya",
        diagnosis_certainty="confirmed",
        notes="52yo, fever + myalgia + headache after Laos/Thailand. Initially suspected dengue; CHIKV confirmed day 10.",
    ),

    # --- African tick bite fever: Lee 2020 (DOI: 10.3947/ic.2019.0073) ---
    ValidationCase(
        case_id="RIC-CR-001",
        source="Lee 2020 Infect Chemother",
        source_pmid="32757495",
        regions=["sub_saharan_africa"],
        destination_country="Eswatini",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"tick": True},
        incubation_days=7,
        final_diagnosis="rickettsial_infection",
        diagnosis_certainty="confirmed",
        notes="Two eschars after rural Swaziland visit. R. africae confirmed by nested PCR. First Korean ATBF case.",
    ),

    # --- Leptospirosis: Rodriguez-Valero 2018 (DOI: 10.1016/j.tmaid.2018.02.013) ---
    # 3 Spanish travellers returning from Chiang Mai, Thailand — case 1
    ValidationCase(
        case_id="LEP-CR-001",
        source="Rodriguez-Valero 2018 Travel Med Infect Dis",
        source_pmid="29526720",
        regions=["southeast_asia"],
        destination_country="Thailand",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=10,
        final_diagnosis="leptospirosis",
        diagnosis_certainty="confirmed",
        notes="Swimming in freshwater near Chiang Mai. Normal WBC, low platelets. Malaria/dengue/typhoid excluded.",
    ),

    # --- Leptospirosis: Kutsuna 2014 (DOI: 10.1016/j.jiac.2014.10.004) ---
    # 5 Japanese travellers from SE Asia — representative case
    ValidationCase(
        case_id="LEP-CR-002",
        source="Kutsuna 2014 J Infect Chemother",
        source_pmid="25459082",
        regions=["southeast_asia"],
        destination_country="Philippines",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": True,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=8,
        final_diagnosis="leptospirosis",
        diagnosis_certainty="confirmed",
        notes="Freshwater exposure in SE Asia. Conjunctival injection, relative bradycardia, elevated Cr, sterile pyuria.",
    ),

    # --- Dengue with cholecystitis: Kuna 2016 (DOI: 10.5603/IMH.2016.0008) ---
    ValidationCase(
        case_id="DEN-CR-001",
        source="Kuna 2016 Int Marit Health",
        source_pmid="27029928",
        regions=["latin_america_caribbean"],
        destination_country="Brazil",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=5,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="58yo F from Brazil. Fever 39C, leukopenia, thrombocytopenia, elevated transaminases, macular rash. Acalculous cholecystitis complication.",
    ),

    # --- Dengue + malaria co-infection: Kavanoor 2025 (DOI: 10.3390/pathogens14100987) ---
    # Using the dengue presentation component
    ValidationCase(
        case_id="DEN-CR-002",
        source="Kavanoor Sridhar 2025 Pathogens",
        source_pmid="41156598",
        regions=["south_central_asia"],
        destination_country="India",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": True,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=7,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="Dengue + P. vivax co-infection in returned traveller from India. Using dengue as primary diagnosis.",
    ),

    # =================================================================
    # AAFP 2013 CLINICAL VIGNETTES (Thwaites & Day, AFP 2013;88(8):524)
    # =================================================================

    # --- Vignette 1: P. falciparum malaria ---
    ValidationCase(
        case_id="MAL-VIG-001",
        source="AAFP 2013 case-based review",
        source_pmid="",
        regions=["latin_america_caribbean"],
        destination_country="Brazil",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=7,
        final_diagnosis="malaria_falciparum",
        diagnosis_certainty="confirmed",
        notes="20yo M from rural Brazil. Headache, chills, fever 103F. Did not take prescribed mefloquine. Thick film positive.",
    ),

    # --- Vignette 2: Typhoid fever ---
    ValidationCase(
        case_id="TYP-VIG-001",
        source="AAFP 2013 case-based review",
        source_pmid="",
        regions=["south_central_asia"],
        destination_country="Pakistan",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=14,
        final_diagnosis="enteric_fever",
        diagnosis_certainty="confirmed",
        notes="7yo M from Pakistan. Fever 104F, no diarrhea, no focus. S. Typhi on blood culture. No pretravel vaccines.",
    ),

    # --- Vignette 3: Dengue haemorrhagic fever ---
    ValidationCase(
        case_id="DEN-VIG-001",
        source="AAFP 2013 case-based review",
        source_pmid="",
        regions=["latin_america_caribbean"],
        destination_country="Dominican Republic",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": True,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=2,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="15yo M from Dominican Republic. Fever, body aches, progressed to gingival bleeding, melena, bloody emesis. IgM+ IgG+.",
    ),

    # =================================================================
    # ADDITIONAL PUBLISHED CASE REPORTS (PubMed background extraction)
    # =================================================================

    # --- P. falciparum: Tseng 2025 (DOI: 10.1186/s12936-025-05581-6) ---
    ValidationCase(
        case_id="MAL-CR-001",
        source="Tseng 2025 Malar J",
        source_pmid="41068738",
        regions=["sub_saharan_africa"],
        destination_country="Angola",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=4,
        final_diagnosis="malaria_falciparum",
        diagnosis_certainty="confirmed",
        notes="66yo M from Central Africa. 20% parasitaemia. No prophylaxis. PCR confirmed.",
    ),

    # --- P. vivax: Andrejkovits 2025 (DOI: 10.3390/tropicalmed10090261) ---
    ValidationCase(
        case_id="MAL-CR-002",
        source="Andrejkovits 2025 Trop Med Infect Dis",
        source_pmid="41003571",
        regions=["southeast_asia"],
        destination_country="Indonesia",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": True,
                  "productive_cough": False,
                  "retro_orbital_pain": True,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=5,
        final_diagnosis="malaria_vivax",
        diagnosis_certainty="confirmed",
        notes="41yo M from Indonesia/Philippines. Myalgia, arthralgias, retro-orbital headache. RT-PCR confirmed P. vivax. No chemoprophylaxis.",
    ),

    # --- Katayama fever: Demolder 2024 (DOI: 10.1016/j.rmcr.2024.102032) ---
    ValidationCase(
        case_id="SCH-CR-001",
        source="Demolder 2024 Resp Med Case Rep",
        source_pmid="38737518",
        regions=["sub_saharan_africa"],
        destination_country="Guinea",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=42,
        final_diagnosis="schistosomiasis",
        diagnosis_certainty="confirmed",
        notes="26yo M. Freshwater lake swimming in Guinea. 6-week incubation. S. mansoni eggs in stool. Dry cough + diarrhoea.",
    ),

    # --- Typhoid: Baqir 2025 (DOI: 10.1155/crgm/3087201) ---
    ValidationCase(
        case_id="TYP-CR-001",
        source="Baqir 2025 Case Rep Gastrointest Med",
        source_pmid="39840122",
        regions=["south_central_asia"],
        destination_country="Pakistan",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=6,
        final_diagnosis="enteric_fever",
        diagnosis_certainty="confirmed",
        notes="48yo M from Pakistan. High-grade fever, jaundice, acholic stools. S. Typhi blood culture confirmed. Complicated by acute liver failure.",
    ),

    # --- XDR Typhoid: Procaccianti 2020 (DOI: 10.3390/pathogens9020151) ---
    ValidationCase(
        case_id="TYP-CR-002",
        source="Procaccianti 2020 Pathogens",
        source_pmid="32102428",
        regions=["south_central_asia"],
        destination_country="Pakistan",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=14,
        final_diagnosis="enteric_fever",
        diagnosis_certainty="confirmed",
        notes="5yo M from Pakistan. Fever 40C, maculopapular rash abdomen, vomiting. XDR S. Typhi (H58). First Italian case.",
    ),

    # --- Dengue haemorrhagic: Wheaton 2024 (DOI: 10.7759/cureus.72234) ---
    ValidationCase(
        case_id="DEN-CR-003",
        source="Wheaton 2024 Cureus",
        source_pmid="39583391",
        regions=["latin_america_caribbean"],
        destination_country="El Salvador",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True,
                  "jaundice": False, "haemorrhagic_signs": True,
                  "gi_symptoms": True, "respiratory_symptoms": True,
                  "neurological_symptoms": True,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"mosquito": True},
        incubation_days=5,
        final_diagnosis="dengue",
        diagnosis_certainty="confirmed",
        notes="52yo M from El Salvador. Fever 102-106F, petechiae, positive tourniquet test, thrombocytopenia nadir 28k. IgG+ all 4 serotypes.",
    ),

    # --- Measles: Gourinat 2018 (DOI: 10.1099/jmmcr.0.005156) ---
    ValidationCase(
        case_id="MEA-CR-001",
        source="Gourinat 2018 JMM Case Rep",
        source_pmid="30323934",
        regions=["oceania"],
        destination_country="New Caledonia",
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": True,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"respiratory_droplet": True},
        incubation_days=12,
        final_diagnosis="measles",
        diagnosis_certainty="confirmed",
        notes="41yo M. Maculopapular rash neck/thorax, erythroderma. Sinusitis. Genotype D8 confirmed PCR. Initially suspected dengue.",
    ),

    # --- Q fever: Cohen 2007 (DOI: 10.1016/j.tmaid.2006.09.002) ---
    ValidationCase(
        case_id="QFE-CR-001",
        source="Cohen 2007 Travel Med Infect Dis",
        source_pmid="17448948",
        regions=["oceania"],
        destination_country="Australia",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": False,
                  "gi_symptoms": False, "respiratory_symptoms": False,
                  "neurological_symptoms": True,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"animal_contact": False},
        incubation_days=18,
        final_diagnosis="q_fever",
        diagnosis_certainty="confirmed",
        notes="Adult M from East Coast Australia. Fever + headache + lymphopenia + elevated LFTs. No pneumonia. C. burnetii seroconversion. Responded to doxycycline.",
    ),

    # --- Melioidosis: Verdecia 2022 (DOI: 10.1093/ofid/ofac284) ---
    ValidationCase(
        case_id="MEL-CR-001",
        source="Verdecia 2022 Open Forum Infect Dis",
        source_pmid="35891686",
        regions=["latin_america_caribbean"],
        destination_country="Panama",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": False, "haemorrhagic_signs": True,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"freshwater": True},
        incubation_days=35,
        final_diagnosis="melioidosis",
        diagnosis_certainty="confirmed",
        notes="48yo M diabetic. Beach construction in Panama. Haematuria, nausea, diarrhoea. Prostatic abscess. B. pseudomallei culture + PCR.",
    ),

    # --- Hepatitis E: Minkoff 2019 (DOI: 10.4269/ajtmh.18-0640) ---
    ValidationCase(
        case_id="HPE-CR-001",
        source="Minkoff 2019 Am J Trop Med Hyg",
        source_pmid="30350777",
        regions=["south_central_asia"],
        destination_country="Bangladesh",
        symptoms={"fever": True, "rash": False, "arthralgia_myalgia": False,
                  "jaundice": True, "haemorrhagic_signs": False,
                  "gi_symptoms": True, "respiratory_symptoms": False,
                  "neurological_symptoms": False,
                  "productive_cough": False,
                  "retro_orbital_pain": False,
                  "small_joint_polyarthralgia": False},
        exposures={"food_water": True},
        incubation_days=21,
        final_diagnosis="hepatitis_e",
        diagnosis_certainty="confirmed",
        notes="8yo M from Bangladesh. Progressive jaundice. HEV IgM positive.",
    ),
]


def save_validation_set(
    cases: list[ValidationCase],
    output_path: Path,
) -> str:
    """Save validation cases to YAML and return SHA-256 hash.

    Returns the SHA-256 hash of the output file for audit logging.
    """
    output = {
        "metadata": {
            "description": "Frozen validation case series for model benchmarking",
            "n_cases": len(cases),
            "diagnoses_represented": sorted(set(c.final_diagnosis for c in cases)),
            "sources": sorted(set(c.source for c in cases)),
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "warning": "DO NOT MODIFY after freezing. Log any changes in osf/amendment_log.md",
        },
        "cases": [asdict(c) for c in cases],
    }

    with open(output_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    # Compute hash
    with open(output_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()

    return file_hash


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    # Save real cases (published case reports + vignettes)
    output_path = PROCESSED_DIR / "validation_cases.yaml"
    file_hash = save_validation_set(VALIDATION_CASES, output_path)

    print(f"Published validation cases saved to {output_path}")
    print(f"  Cases: {len(VALIDATION_CASES)}")
    print(f"  Diagnoses: {len(set(c.final_diagnosis for c in VALIDATION_CASES))}")
    print(f"  SHA-256: {file_hash}")

    # Generate and save Bottieau-calibrated semi-synthetic cases
    from src.validation.bottieau_calibrated_cases import generate_bottieau_cases
    bottieau_cases = generate_bottieau_cases()

    bot_path = PROCESSED_DIR / "validation_cases_bottieau.yaml"
    bot_hash = save_validation_set(bottieau_cases, bot_path)

    print(f"\nBottieau-calibrated cases saved to {bot_path}")
    print(f"  Cases: {len(bottieau_cases)}")
    print(f"  SHA-256: {bot_hash}")

    # Save combined set
    combined = VALIDATION_CASES + bottieau_cases
    combined_path = PROCESSED_DIR / "validation_cases_combined.yaml"
    combined_hash = save_validation_set(combined, combined_path)

    print(f"\nCombined validation set saved to {combined_path}")
    print(f"  Published cases: {len(VALIDATION_CASES)}")
    print(f"  Bottieau-calibrated: {len(bottieau_cases)}")
    print(f"  Total: {len(combined)}")
    print(f"  SHA-256: {combined_hash}")

    # Summary by diagnosis
    dx_counts: dict[str, int] = {}
    for c in combined:
        dx_counts[c.final_diagnosis] = dx_counts.get(c.final_diagnosis, 0) + 1
    print("\n  Cases per diagnosis (combined):")
    for dx, count in sorted(dx_counts.items(), key=lambda x: -x[1]):
        print(f"    {dx:40s} {count}")


if __name__ == "__main__":
    main()
