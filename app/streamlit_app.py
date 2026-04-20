"""Streamlit app for the Australian Traveller Fever Differential.

Provides a clinical decision-support interface for febrile returned
travellers presenting to Australian emergency departments.

Usage:
    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.inference.naive_bayes import (
    EXPOSURE_FEATURES,
    SYMPTOM_FEATURES,
    TravellerFeverModel,
)
from src.priors.build_base_priors import REGIONS
from src.utils import CLINICAL_DIR, PROCESSED_DIR

# ---------------------------------------------------------------------------
# Display names for UI
# ---------------------------------------------------------------------------

REGION_DISPLAY = {
    "southeast_asia": "Southeast Asia (Indonesia, Thailand, Vietnam, Philippines, Malaysia, Cambodia, Myanmar, Laos)",
    "south_central_asia": "South-Central Asia (India, Sri Lanka, Nepal, Bangladesh, Pakistan)",
    "northeast_asia": "Northeast Asia (China, Japan, South Korea)",
    "oceania": "Oceania / Pacific (PNG, Fiji, Vanuatu, Samoa, Tonga, Solomon Islands)",
    "sub_saharan_africa": "Sub-Saharan Africa",
    "north_africa_middle_east": "North Africa / Middle East (Egypt, Turkey, UAE, Saudi Arabia)",
    "latin_america_caribbean": "Latin America & Caribbean (Mexico, Brazil, Peru, Colombia, Caribbean)",
    "europe": "Europe",
    "north_america": "North America (USA, Canada)",
}

SYMPTOM_DISPLAY = {
    "fever": "Fever / chills / rigors",
    "rash": "Rash (maculopapular, vesicular, petechial, or urticarial)",
    "arthralgia_myalgia": "Arthralgia / myalgia (joint or muscle pain)",
    "jaundice": "Jaundice (yellow skin/sclera, dark urine)",
    "haemorrhagic_signs": "Haemorrhagic signs (petechiae, purpura, bleeding, haematuria)",
    "gi_symptoms": "GI symptoms (diarrhoea, vomiting, abdominal pain)",
    "respiratory_symptoms": "Respiratory symptoms (cough, dyspnoea, sore throat)",
    "neurological_symptoms": "Neurological symptoms (headache, confusion, seizures, neck stiffness)",
    "productive_cough": "Productive cough (sputum / phlegm)",
    "retro_orbital_pain": "Retro-orbital pain (pain behind the eyes)",
    "small_joint_polyarthralgia": "Small-joint polyarthralgia (pain in hands, wrists, ankles — bilateral)",
}

EXPOSURE_DISPLAY = {
    "mosquito": "Mosquito bites",
    "freshwater": "Freshwater contact (swimming, wading, rafting)",
    "animal_contact": "Animal contact (bites, scratches, farm animals)",
    "sexual": "Sexual contact (new partner, unprotected)",
    "needle_blood": "Needle / blood exposure (tattoo, injection, needlestick)",
    "food_water": "Potentially contaminated food or water",
    "respiratory_droplet": "Close contact with respiratory illness",
    "tick": "Tick exposure (bush walking, safari)",
}

DIAGNOSIS_DISPLAY = {
    "malaria_falciparum": "Malaria (P. falciparum)",
    "malaria_vivax": "Malaria (P. vivax/ovale/malariae)",
    "dengue": "Dengue fever",
    "chikungunya": "Chikungunya",
    "zika": "Zika virus",
    "enteric_fever": "Enteric fever (typhoid/paratyphoid)",
    "acute_bacterial_gastroenteritis": "Acute bacterial gastroenteritis",
    "hepatitis_a": "Hepatitis A",
    "hepatitis_b_acute": "Hepatitis B (acute)",
    "hepatitis_e": "Hepatitis E",
    "rickettsial_infection": "Rickettsial infection (scrub/murine typhus, spotted fever)",
    "leptospirosis": "Leptospirosis",
    "acute_hiv_seroconversion": "Acute HIV seroconversion",
    "influenza": "Influenza",
    "covid_19": "COVID-19",
    "measles": "Measles",
    "japanese_encephalitis": "Japanese encephalitis",
    "melioidosis": "Melioidosis",
    "tuberculosis": "Tuberculosis (active pulmonary)",
    "schistosomiasis": "Schistosomiasis (Katayama fever)",
    "strongyloides_acute": "Strongyloides (acute)",
    "amoebiasis": "Amoebiasis (amoebic liver abscess)",
    "brucellosis": "Brucellosis",
    "q_fever": "Q fever",
    "mpox": "Mpox",
    "oropouche": "Oropouche virus",
    "yellow_fever": "Yellow fever",
    "rabies": "Rabies (post-exposure)",
    "community_acquired_pneumonia": "Community-acquired pneumonia",
    "uti_pyelonephritis": "UTI / pyelonephritis",
    "viral_urti": "Viral URTI",
    "infectious_mononucleosis": "Infectious mononucleosis (EBV/CMV)",
    "undifferentiated_viral_syndrome": "Undifferentiated viral syndrome",
}


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

@st.cache_resource
def load_model() -> tuple[TravellerFeverModel, str]:
    """Load the model and return (model, last_update_timestamp)."""
    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"

    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    live_path = PROCESSED_DIR / "live_prior_multipliers.yaml"

    model = TravellerFeverModel.from_yaml(
        priors_path, defs_path,
        live_multipliers_path=live_path if live_path.exists() else None,
    )

    # Get last update timestamp
    last_update = "Unknown"
    if live_path.exists():
        with open(live_path) as f:
            meta = yaml.safe_load(f)
        if meta and "metadata" in meta:
            last_update = meta["metadata"].get("generated_at", "Unknown")
            if last_update != "Unknown":
                try:
                    dt = datetime.fromisoformat(last_update)
                    last_update = dt.strftime("%d %B %Y, %H:%M UTC")
                except ValueError:
                    pass

    return model, last_update


# ---------------------------------------------------------------------------
# App layout
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="BEACON — Fever Differential",
        page_icon="🔦",
        layout="wide",
    )

    st.title("BEACON")
    st.caption(
        "**B**ayesian **E**vidence-**A**djusted **C**linical **O**utbreak **N**avigator | "
        "Australian-weighted diagnostic differential for febrile returned travellers"
    )

    model, last_update = load_model()

    # Sidebar
    with st.sidebar:
        st.header("About BEACON")
        st.markdown(
            "**Purpose:** Clinical decision support for febrile returned "
            "travellers presenting to Australian emergency departments.\n\n"
            "**Method:** Naive Bayes with Australian-weighted GeoSentinel "
            "destination priors, graded symptom likelihood ratios, "
            "hierarchical shrinkage, and monthly-updated "
            "outbreak signals from WHO DON.\n\n"
            "**NOT a substitute for clinical judgement.** Always consider "
            "malaria in any febrile returned traveller from an endemic area."
        )
        st.divider()
        st.metric("Last priors update", last_update)
        st.divider()
        st.markdown(
            "**Pre-registration:** [OSF](https://doi.org/10.17605/OSF.IO/MA6YD)\n\n"
            "**33 diagnoses** | **11 symptom features** | **9 regions** | Monthly CI update"
        )
        st.divider()
        st.markdown(
            "**Data sources:**\n"
            "- GeoSentinel Network (Leder 2013, Brown 2023, Bierbrier 2024, Duvignaud 2024)\n"
            "- Australian NNDSS (Sohail 2024, Forster 2021)\n"
            "- Bottieau 2007 (symptom calibration, N=2,071)\n"
            "- CDC Yellow Book 2024\n"
            "- WHO Disease Outbreak News (live API)"
        )

    # Main input form
    col_input, col_result = st.columns([1, 1.5])

    with col_input:
        st.header("Patient presentation")

        # Destination
        st.subheader("Travel destination(s)")
        selected_regions = []
        for region_key, display_name in REGION_DISPLAY.items():
            if st.checkbox(display_name, key=f"region_{region_key}"):
                selected_regions.append(region_key)

        st.subheader("Symptoms")
        symptoms = {}
        for sx_key, display_name in SYMPTOM_DISPLAY.items():
            symptoms[sx_key] = st.checkbox(display_name, key=f"sx_{sx_key}")

        st.subheader("Exposures")
        st.caption("Check exposures the patient **reports**. Leave unchecked "
                   "for exposures explicitly **denied** (model uses absence as evidence).")
        exposures = {}
        for exp_key, display_name in EXPOSURE_DISPLAY.items():
            exposures[exp_key] = st.checkbox(display_name, key=f"exp_{exp_key}")

        st.subheader("Vaccination status")
        st.caption("Select vaccines the patient has received (reduces prior for "
                   "vaccine-preventable diseases by 95%).")
        vaccinations = []
        vax_options = {
            "hepatitis_a": "Hepatitis A",
            "measles": "Measles / MMR",
            "yellow_fever": "Yellow fever",
            "japanese_encephalitis": "Japanese encephalitis",
        }
        for vax_key, vax_name in vax_options.items():
            if st.checkbox(vax_name, key=f"vax_{vax_key}"):
                vaccinations.append(vax_key)

        st.subheader("Incubation period")
        use_incubation = st.checkbox("Specify incubation period")
        incubation_days = None
        if use_incubation:
            incubation_days = st.number_input(
                "Days from return to symptom onset",
                min_value=0,
                max_value=365,
                value=7,
                step=1,
            )

        run_button = st.button("Generate differential", type="primary",
                               use_container_width=True)

    # Results
    with col_result:
        st.header("Differential diagnosis")

        if not run_button:
            st.info("Select travel destination(s) and clinical features, then click "
                    "'Generate differential'.")
            return

        if not selected_regions:
            st.warning("Please select at least one travel destination region.")
            return

        # Run inference — pass ALL exposures (True and False) so denied
        # exposures contribute as negative evidence
        result = model.diagnose(
            regions=selected_regions,
            symptoms=symptoms,
            exposures=exposures,
            incubation_days=incubation_days,
            vaccinations=vaccinations,
        )

        # Safety alerts — show FIRST, before differential
        if result.safety_alerts:
            for alert in result.safety_alerts:
                if alert.severity == "critical":
                    st.error(
                        f"**{alert.alert}**\n\n"
                        f"{alert.action}\n\n"
                        f"*Ref: {alert.references}*"
                    )
                else:
                    st.warning(
                        f"**{alert.alert}**\n\n"
                        f"{alert.action}\n\n"
                        f"*Ref: {alert.references}*"
                    )

        # Abstention warning
        if result.abstain:
            st.error(
                f"**Insufficient discrimination** — {result.abstention_reason}\n\n"
                "The clinical features provided do not clearly distinguish between "
                "diagnoses. Consider specialist referral or additional investigations."
            )

        # Top differential table
        st.subheader("Ranked differential")

        top_results = result.top_n(15)
        for i, dx in enumerate(top_results):
            display_name = DIAGNOSIS_DISPLAY.get(dx.diagnosis, dx.diagnosis)
            posterior_pct = dx.posterior * 100

            # Colour coding
            if posterior_pct >= 30:
                bar_color = "🔴"
            elif posterior_pct >= 10:
                bar_color = "🟠"
            elif posterior_pct >= 3:
                bar_color = "🟡"
            else:
                bar_color = "⚪"

            with st.container():
                cols = st.columns([0.5, 3, 1.5])
                cols[0].markdown(f"**{dx.rank}.**")
                cols[1].markdown(f"**{display_name}**")
                cols[2].markdown(f"{bar_color} **{posterior_pct:.1f}%**")

                # Evidence breakdown (expandable)
                with st.expander("Evidence breakdown", expanded=(i < 3)):
                    ev_cols = st.columns(4)
                    ev_cols[0].metric("Prior", f"{dx.log_prior:+.2f}")
                    ev_cols[1].metric("Symptoms", f"{dx.log_symptom_likelihood:+.2f}")
                    ev_cols[2].metric("Exposures", f"{dx.log_exposure_likelihood:+.2f}")
                    ev_cols[3].metric("Incubation", f"{dx.log_incubation_likelihood:+.2f}")

        # Safety reminder
        st.divider()
        st.warning(
            "**Clinical safety reminder:**\n"
            "- Always consider **malaria** in any febrile traveller from an endemic area — "
            "request thick/thin film and RDT regardless of model output\n"
            "- Consider **isolation precautions** for measles, mpox, VHF before examination\n"
            "- This tool uses a Naive Bayes model with known independence assumption "
            "violations — treat outputs as decision support, not diagnosis\n"
            "- Model covers 33 diagnoses — rare/atypical presentations may not be captured"
        )


if __name__ == "__main__":
    main()
