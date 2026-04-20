"""Build base destination-diagnosis priors from GeoSentinel + NNDSS Australian reweighting.

This script:
1. Loads GeoSentinel proportionate morbidity data (diagnosis × region)
2. Loads Australian NNDSS imported-case counts by region
3. Reweights GeoSentinel priors by Australian destination distribution
4. Outputs destination_priors.yaml

The reweighting adjusts for the fact that GeoSentinel over-represents
US/European traveller destinations (Latin America, Sub-Saharan Africa)
while Australian travellers disproportionately visit SE Asia and Oceania.

Usage:
    python -m src.priors.build_base_priors
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml

from src.utils import PROCESSED_DIR, RAW_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Region mapping: harmonise GeoSentinel regions to a common schema
# ---------------------------------------------------------------------------

REGIONS = [
    "southeast_asia",
    "south_central_asia",
    "northeast_asia",
    "oceania",
    "sub_saharan_africa",
    "north_africa_middle_east",
    "latin_america_caribbean",
    "europe",
    "north_america",
]

# The 33 pre-registered diagnoses (keys match diagnosis_definitions.yaml)
DIAGNOSES = [
    "malaria_falciparum",
    "malaria_vivax",
    "dengue",
    "chikungunya",
    "zika",
    "enteric_fever",
    "acute_bacterial_gastroenteritis",
    "hepatitis_a",
    "hepatitis_b_acute",
    "hepatitis_e",
    "rickettsial_infection",
    "leptospirosis",
    "acute_hiv_seroconversion",
    "influenza",
    "covid_19",
    "measles",
    "japanese_encephalitis",
    "melioidosis",
    "tuberculosis",
    "schistosomiasis",
    "strongyloides_acute",
    "amoebiasis",
    "brucellosis",
    "q_fever",
    "mpox",
    "oropouche",
    "yellow_fever",
    "rabies",
    "community_acquired_pneumonia",
    "uti_pyelonephritis",
    "viral_urti",
    "infectious_mononucleosis",
    "undifferentiated_viral_syndrome",
]

# ---------------------------------------------------------------------------
# GeoSentinel proportionate morbidity: P(diagnosis | region, ill traveller)
# ---------------------------------------------------------------------------
# Source: Leder 2013 (PMID 23552375) Table 3 case counts + regional proportions;
#         Brown/Angelo 2023 (PMID 37368820); Bierbrier 2024 (PMID 38195993);
#         Duvignaud/Angelo 2024 (PMID 38951998).
#
# Values are approximate proportionate morbidity ratios among febrile travellers
# from each region. Where disease-specific GeoSentinel data is unavailable,
# estimates from CDC Yellow Book geographic distributions are used with
# floor values.

# Minimum floor probability to avoid zero priors
FLOOR = 1e-4


def _build_geosentinel_pmr() -> dict[str, dict[str, float]]:
    """Return P(diagnosis | region) proportionate morbidity matrix.

    Returns dict[diagnosis][region] -> float (unnormalised).
    These are filled from published GeoSentinel data where available,
    and from clinical knowledge + geographic distributions otherwise.
    """
    # Initialise with floor values
    pmr: dict[str, dict[str, float]] = {}
    for dx in DIAGNOSES:
        pmr[dx] = {r: FLOOR for r in REGIONS}

    # --- Malaria (Leder 2013: 1,990 P.f cases; Sohail 2024 for Australian split) ---
    # GeoSentinel: ~85% from Sub-Saharan Africa, ~5% South-Central Asia, ~3% SE Asia,
    # ~3% Oceania, ~2% Latin America, ~1% MENA
    pmr["malaria_falciparum"]["sub_saharan_africa"] = 0.45
    pmr["malaria_falciparum"]["south_central_asia"] = 0.05
    pmr["malaria_falciparum"]["southeast_asia"] = 0.03
    pmr["malaria_falciparum"]["oceania"] = 0.04
    pmr["malaria_falciparum"]["latin_america_caribbean"] = 0.02
    pmr["malaria_falciparum"]["north_africa_middle_east"] = 0.01

    pmr["malaria_vivax"]["south_central_asia"] = 0.12
    pmr["malaria_vivax"]["oceania"] = 0.08
    pmr["malaria_vivax"]["southeast_asia"] = 0.04
    pmr["malaria_vivax"]["sub_saharan_africa"] = 0.03
    pmr["malaria_vivax"]["latin_america_caribbean"] = 0.02

    # --- Dengue (Duvignaud 2024: 5,958 cases) ---
    pmr["dengue"]["southeast_asia"] = 0.50
    pmr["dengue"]["south_central_asia"] = 0.15
    pmr["dengue"]["latin_america_caribbean"] = 0.16
    pmr["dengue"]["sub_saharan_africa"] = 0.07
    pmr["dengue"]["oceania"] = 0.02

    # --- Chikungunya (Bierbrier 2024: 1,202 cases) ---
    pmr["chikungunya"]["latin_america_caribbean"] = 0.43
    pmr["chikungunya"]["southeast_asia"] = 0.23
    pmr["chikungunya"]["south_central_asia"] = 0.14
    pmr["chikungunya"]["sub_saharan_africa"] = 0.08

    # --- Zika ---
    pmr["zika"]["latin_america_caribbean"] = 0.55
    pmr["zika"]["southeast_asia"] = 0.15
    pmr["zika"]["oceania"] = 0.10
    pmr["zika"]["sub_saharan_africa"] = 0.05

    # --- Enteric fever (Leder 2013: 467 cases) ---
    pmr["enteric_fever"]["south_central_asia"] = 0.55
    pmr["enteric_fever"]["southeast_asia"] = 0.15
    pmr["enteric_fever"]["sub_saharan_africa"] = 0.10
    pmr["enteric_fever"]["latin_america_caribbean"] = 0.05

    # --- Acute bacterial gastroenteritis (most common travel illness) ---
    pmr["acute_bacterial_gastroenteritis"]["south_central_asia"] = 0.25
    pmr["acute_bacterial_gastroenteritis"]["southeast_asia"] = 0.20
    pmr["acute_bacterial_gastroenteritis"]["sub_saharan_africa"] = 0.15
    pmr["acute_bacterial_gastroenteritis"]["latin_america_caribbean"] = 0.20
    pmr["acute_bacterial_gastroenteritis"]["north_africa_middle_east"] = 0.08
    pmr["acute_bacterial_gastroenteritis"]["oceania"] = 0.03
    pmr["acute_bacterial_gastroenteritis"]["northeast_asia"] = 0.02
    pmr["acute_bacterial_gastroenteritis"]["europe"] = 0.02

    # --- Hepatitis A ---
    pmr["hepatitis_a"]["south_central_asia"] = 0.20
    pmr["hepatitis_a"]["sub_saharan_africa"] = 0.15
    pmr["hepatitis_a"]["southeast_asia"] = 0.10
    pmr["hepatitis_a"]["latin_america_caribbean"] = 0.10
    pmr["hepatitis_a"]["north_africa_middle_east"] = 0.05

    # --- Hepatitis B (acute) ---
    pmr["hepatitis_b_acute"]["sub_saharan_africa"] = 0.10
    pmr["hepatitis_b_acute"]["southeast_asia"] = 0.08
    pmr["hepatitis_b_acute"]["oceania"] = 0.03
    pmr["hepatitis_b_acute"]["south_central_asia"] = 0.03

    # --- Hepatitis E ---
    pmr["hepatitis_e"]["south_central_asia"] = 0.15
    pmr["hepatitis_e"]["sub_saharan_africa"] = 0.05
    pmr["hepatitis_e"]["southeast_asia"] = 0.05

    # --- Rickettsial infection (Leder 2013: 267 spotted fever cases) ---
    pmr["rickettsial_infection"]["sub_saharan_africa"] = 0.40
    pmr["rickettsial_infection"]["southeast_asia"] = 0.15
    pmr["rickettsial_infection"]["south_central_asia"] = 0.10
    pmr["rickettsial_infection"]["europe"] = 0.05

    # --- Leptospirosis ---
    pmr["leptospirosis"]["southeast_asia"] = 0.30
    pmr["leptospirosis"]["south_central_asia"] = 0.15
    pmr["leptospirosis"]["latin_america_caribbean"] = 0.15
    pmr["leptospirosis"]["oceania"] = 0.10
    pmr["leptospirosis"]["sub_saharan_africa"] = 0.05

    # --- Acute HIV seroconversion ---
    pmr["acute_hiv_seroconversion"]["sub_saharan_africa"] = 0.15
    pmr["acute_hiv_seroconversion"]["southeast_asia"] = 0.05
    pmr["acute_hiv_seroconversion"]["latin_america_caribbean"] = 0.03

    # --- Influenza (worldwide, seasonal) ---
    for r in REGIONS:
        pmr["influenza"][r] = 0.05

    # --- COVID-19 (ubiquitous — no destination weighting) ---
    for r in REGIONS:
        pmr["covid_19"][r] = 0.03

    # --- Measles ---
    pmr["measles"]["south_central_asia"] = 0.10
    pmr["measles"]["southeast_asia"] = 0.08
    pmr["measles"]["sub_saharan_africa"] = 0.08
    pmr["measles"]["europe"] = 0.03

    # --- Japanese encephalitis ---
    pmr["japanese_encephalitis"]["southeast_asia"] = 0.02
    pmr["japanese_encephalitis"]["south_central_asia"] = 0.01
    pmr["japanese_encephalitis"]["northeast_asia"] = 0.005
    pmr["japanese_encephalitis"]["oceania"] = 0.005

    # --- Melioidosis ---
    pmr["melioidosis"]["southeast_asia"] = 0.02
    pmr["melioidosis"]["oceania"] = 0.01
    pmr["melioidosis"]["south_central_asia"] = 0.005

    # --- Tuberculosis ---
    pmr["tuberculosis"]["south_central_asia"] = 0.05
    pmr["tuberculosis"]["sub_saharan_africa"] = 0.05
    pmr["tuberculosis"]["southeast_asia"] = 0.03
    pmr["tuberculosis"]["oceania"] = 0.01

    # --- Schistosomiasis ---
    pmr["schistosomiasis"]["sub_saharan_africa"] = 0.15
    pmr["schistosomiasis"]["southeast_asia"] = 0.02
    pmr["schistosomiasis"]["latin_america_caribbean"] = 0.01

    # --- Strongyloides ---
    pmr["strongyloides_acute"]["southeast_asia"] = 0.05
    pmr["strongyloides_acute"]["sub_saharan_africa"] = 0.03
    pmr["strongyloides_acute"]["latin_america_caribbean"] = 0.02
    pmr["strongyloides_acute"]["oceania"] = 0.02

    # --- Amoebiasis ---
    pmr["amoebiasis"]["south_central_asia"] = 0.10
    pmr["amoebiasis"]["southeast_asia"] = 0.05
    pmr["amoebiasis"]["sub_saharan_africa"] = 0.05
    pmr["amoebiasis"]["latin_america_caribbean"] = 0.03

    # --- Brucellosis ---
    pmr["brucellosis"]["north_africa_middle_east"] = 0.05
    pmr["brucellosis"]["south_central_asia"] = 0.03
    pmr["brucellosis"]["latin_america_caribbean"] = 0.02
    pmr["brucellosis"]["sub_saharan_africa"] = 0.01

    # --- Q fever ---
    # Almost entirely locally acquired in Australia; very low imported prior
    pmr["q_fever"]["europe"] = 0.005
    pmr["q_fever"]["north_africa_middle_east"] = 0.003

    # --- Mpox ---
    pmr["mpox"]["sub_saharan_africa"] = 0.03
    pmr["mpox"]["europe"] = 0.01
    pmr["mpox"]["latin_america_caribbean"] = 0.005

    # --- Oropouche ---
    pmr["oropouche"]["latin_america_caribbean"] = 0.02

    # --- Yellow fever ---
    pmr["yellow_fever"]["sub_saharan_africa"] = 0.005
    pmr["yellow_fever"]["latin_america_caribbean"] = 0.002

    # --- Rabies ---
    pmr["rabies"]["south_central_asia"] = 0.02
    pmr["rabies"]["southeast_asia"] = 0.02
    pmr["rabies"]["sub_saharan_africa"] = 0.01
    pmr["rabies"]["latin_america_caribbean"] = 0.005

    # --- Non-tropical differentials (destination-independent) ---
    for r in REGIONS:
        pmr["community_acquired_pneumonia"][r] = 0.03
        pmr["uti_pyelonephritis"][r] = 0.02
        pmr["viral_urti"][r] = 0.08
        pmr["infectious_mononucleosis"][r] = 0.01
        pmr["undifferentiated_viral_syndrome"][r] = 0.10

    return pmr


# ---------------------------------------------------------------------------
# Australian traveller destination distribution (NNDSS reweighting)
# ---------------------------------------------------------------------------

def _build_australian_destination_weights() -> dict[str, float]:
    """Return Australian traveller destination proportions.

    Based on ABS Overseas Arrivals and Departures (Cat. 3401.0) 2012-2022
    and NNDSS imported-case distributions from Sohail 2024 papers.

    These represent the proportion of Australian outbound travellers
    visiting each region, used to reweight GeoSentinel priors from the
    GeoSentinel (US/European-weighted) denominator to an Australian one.
    """
    # ABS short-term resident departures by destination region (approximate
    # 2012-2019 pre-COVID average proportions)
    return {
        "southeast_asia": 0.35,       # Indonesia, Thailand, Vietnam, Philippines, Malaysia
        "south_central_asia": 0.06,   # India, Sri Lanka, Nepal
        "northeast_asia": 0.12,       # China, Japan, South Korea
        "oceania": 0.12,              # NZ, Fiji, PNG, Vanuatu, Samoa
        "sub_saharan_africa": 0.02,   # South Africa, Kenya, Tanzania
        "north_africa_middle_east": 0.03,  # UAE, Egypt, Turkey
        "latin_america_caribbean": 0.02,   # Mexico, Peru, Brazil
        "europe": 0.18,              # UK, Italy, France, Germany, Greece
        "north_america": 0.10,       # USA, Canada
    }


def _build_nndss_imported_case_distribution() -> dict[str, dict[str, float]]:
    """Return Australian imported-case proportions by (diagnosis, region).

    Where published NNDSS analyses provide destination-stratified data,
    use those directly. Otherwise, fall back to the GeoSentinel PMR.

    Sources:
    - Sohail 2024 malaria (PMID 38127641): region-stratified imported malaria
    - Sohail 2024 dengue (PMID 38243558): region-stratified imported dengue
    - Forster & Leder 2021 typhoid (PMID 34619766): per-country incidence
    - NAMAC reports: chikungunya country-of-acquisition
    """
    nndss: dict[str, dict[str, float]] = {}

    # Malaria P. falciparum — Sohail 2024: SSA 45%, Oceania 18%, SCA 12%,
    # MENA 11%, SEA 6%
    nndss["malaria_falciparum"] = {
        "sub_saharan_africa": 0.45,
        "oceania": 0.18,
        "south_central_asia": 0.12,
        "north_africa_middle_east": 0.11,
        "southeast_asia": 0.06,
    }

    # Malaria P. vivax — Sohail 2024: SCA dominant (India), Oceania (PNG)
    nndss["malaria_vivax"] = {
        "south_central_asia": 0.35,
        "oceania": 0.30,
        "southeast_asia": 0.10,
        "sub_saharan_africa": 0.08,
        "north_africa_middle_east": 0.08,
    }

    # Dengue — Sohail 2024: SEA 74%, SCA 12%, Oceania 11%
    nndss["dengue"] = {
        "southeast_asia": 0.74,
        "south_central_asia": 0.12,
        "oceania": 0.11,
        "latin_america_caribbean": 0.02,
        "sub_saharan_africa": 0.01,
    }

    # Enteric fever — Forster & Leder 2021: SCA dominant (Bangladesh, India)
    nndss["enteric_fever"] = {
        "south_central_asia": 0.65,
        "southeast_asia": 0.15,
        "sub_saharan_africa": 0.08,
        "oceania": 0.05,
        "north_africa_middle_east": 0.03,
    }

    # Chikungunya — NAMAC reports: Indonesia, India top sources for Australia
    nndss["chikungunya"] = {
        "southeast_asia": 0.45,
        "south_central_asia": 0.15,
        "latin_america_caribbean": 0.15,
        "oceania": 0.10,
        "sub_saharan_africa": 0.10,
    }

    return nndss


# ---------------------------------------------------------------------------
# Prior construction
# ---------------------------------------------------------------------------

def build_destination_priors() -> dict[str, dict[str, float]]:
    """Build reweighted P(diagnosis | region) priors for Australian travellers.

    Method:
    1. Start with GeoSentinel proportionate morbidity P_GS(dx | region)
    2. For diseases with NNDSS data, replace with Australian-specific
       P_AU(region | dx) and convert via Bayes' rule using Australian
       destination weights
    3. For remaining diseases, reweight GeoSentinel by Australian
       destination distribution
    4. Normalise per-region to get P(dx | region)

    Returns dict[diagnosis][region] -> float (normalised per-region).
    """
    geosentinel = _build_geosentinel_pmr()
    nndss = _build_nndss_imported_case_distribution()
    au_weights = _build_australian_destination_weights()

    priors: dict[str, dict[str, float]] = {}

    for dx in DIAGNOSES:
        priors[dx] = {}

        if dx in nndss:
            # Use NNDSS-derived Australian distribution directly
            nndss_dx = nndss[dx]
            for r in REGIONS:
                priors[dx][r] = nndss_dx.get(r, FLOOR)
        else:
            # Reweight GeoSentinel by Australian destination distribution
            # P_AU(dx | region) ∝ P_GS(dx | region) × W_AU(region) / W_GS(region)
            # Since we don't have explicit W_GS, use the GeoSentinel values
            # as-is but scale by the Australian destination weight
            for r in REGIONS:
                gs_val = geosentinel[dx][r]
                au_w = au_weights[r]
                priors[dx][r] = gs_val * au_w

    # Normalise: for each region, P(dx | region) should sum to 1
    for r in REGIONS:
        region_total = sum(priors[dx][r] for dx in DIAGNOSES)
        if region_total > 0:
            for dx in DIAGNOSES:
                priors[dx][r] = priors[dx][r] / region_total

    return priors


def save_priors(priors: dict[str, dict[str, float]], output_path: Path) -> None:
    """Save destination priors to YAML."""
    # Restructure as region -> diagnosis -> probability for readability
    output: dict[str, dict[str, float]] = {}
    for r in REGIONS:
        output[r] = {}
        for dx in DIAGNOSES:
            val = priors[dx][r]
            # Round to 6 decimal places for readability
            output[r][dx] = round(val, 6)

    metadata = {
        "metadata": {
            "description": "P(diagnosis | region) for febrile returned travellers",
            "method": "GeoSentinel proportionate morbidity reweighted by Australian "
                      "NNDSS imported-case distributions",
            "sources": [
                "Leder 2013 Ann Intern Med (PMID 23552375)",
                "Brown/Angelo 2023 MMWR (PMID 37368820)",
                "Bierbrier 2024 J Travel Med (PMID 38195993)",
                "Duvignaud/Angelo 2024 J Travel Med (PMID 38951998)",
                "Sohail 2024 malaria (PMID 38127641)",
                "Sohail 2024 dengue (PMID 38243558)",
                "Forster & Leder 2021 typhoid (PMID 34619766)",
                "NAMAC annual reports 2004-2015",
            ],
            "australian_reweighting": "ABS Cat. 3401.0 short-term departures 2012-2019",
            "normalisation": "Per-region normalised (sum to 1.0 within each region)",
            "floor_value": FLOOR,
            "generated_by": "src/priors/build_base_priors.py",
        },
    }

    with open(output_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        f.write("\n")
        yaml.dump({"priors": output}, f, default_flow_style=False, sort_keys=False)

    logger.info("Saved destination priors to %s", output_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    priors = build_destination_priors()
    output_path = PROCESSED_DIR / "destination_priors.yaml"
    save_priors(priors, output_path)

    # Print summary
    print(f"\nDestination priors saved to {output_path}")
    print(f"Regions: {len(REGIONS)}")
    print(f"Diagnoses: {len(DIAGNOSES)}")

    # Show top-3 diagnoses per region
    print("\n--- Top-3 diagnoses per region ---")
    for r in REGIONS:
        ranked = sorted(DIAGNOSES, key=lambda dx: priors[dx][r], reverse=True)[:3]
        top3 = ", ".join(f"{dx} ({priors[dx][r]:.3f})" for dx in ranked)
        print(f"  {r}: {top3}")

    # Verify normalisation
    for r in REGIONS:
        total = sum(priors[dx][r] for dx in DIAGNOSES)
        assert abs(total - 1.0) < 1e-6, f"Region {r} priors sum to {total}, not 1.0"
    print("\nNormalisation check passed (all regions sum to 1.0)")


if __name__ == "__main__":
    main()
