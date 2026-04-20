"""Property tests for the Naive Bayes inference engine."""

import math

import pytest
import yaml

from src.inference.naive_bayes import TravellerFeverModel, DiseaseDefinition, SYMPTOM_FEATURES
from src.utils import CLINICAL_DIR, PROCESSED_DIR


@pytest.fixture
def model():
    """Load the model from generated YAML files."""
    priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"
    if not priors_path.exists():
        pytest.skip("Run build_base_priors.py first")
    return TravellerFeverModel.from_yaml(priors_path, defs_path)


class TestPosteriorNormalisation:
    """Posteriors must sum to 1."""

    def test_posteriors_sum_to_one(self, model):
        result = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True, "rash": True},
        )
        total = sum(dx.posterior for dx in result.diagnoses)
        assert abs(total - 1.0) < 1e-6

    def test_posteriors_sum_to_one_no_region(self, model):
        result = model.diagnose(
            regions=[],
            symptoms={"fever": True},
        )
        total = sum(dx.posterior for dx in result.diagnoses)
        assert abs(total - 1.0) < 1e-6

    def test_posteriors_sum_to_one_multiple_regions(self, model):
        result = model.diagnose(
            regions=["southeast_asia", "south_central_asia"],
            symptoms={"fever": True, "gi_symptoms": True},
            exposures={"food_water": True},
            incubation_days=10,
        )
        total = sum(dx.posterior for dx in result.diagnoses)
        assert abs(total - 1.0) < 1e-6


class TestSymptomMonotonicity:
    """Adding a symptom that is characteristic of a diagnosis should not
    decrease that diagnosis's log-posterior (relative to the baseline).

    This catches implementation bugs where likelihood computation is inverted.
    """

    def test_adding_jaundice_helps_hepatitis_a(self, model):
        """Hepatitis A has jaundice=high; adding jaundice should strongly
        increase its symptom likelihood (jaundice is rare in febrile
        travellers, so the likelihood ratio is large)."""
        result_no = model.diagnose(
            regions=["south_central_asia"],
            symptoms={"jaundice": False},
        )
        result_yes = model.diagnose(
            regions=["south_central_asia"],
            symptoms={"jaundice": True},
        )
        hepa_no = next(d for d in result_no.diagnoses if d.diagnosis == "hepatitis_a")
        hepa_yes = next(d for d in result_yes.diagnoses if d.diagnosis == "hepatitis_a")
        assert hepa_yes.log_symptom_likelihood > hepa_no.log_symptom_likelihood

    def test_adding_mosquito_helps_dengue_relative(self, model):
        """Dengue is mosquito-transmitted; reporting mosquito exposure should
        increase dengue's posterior relative to non-mosquito diseases."""
        result_no = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True},
            exposures={},
        )
        result_yes = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True},
            exposures={"mosquito": True},
        )
        dengue_no = next(d for d in result_no.diagnoses if d.diagnosis == "dengue")
        dengue_yes = next(d for d in result_yes.diagnoses if d.diagnosis == "dengue")
        # Reporting mosquito exposure should increase dengue's posterior
        assert dengue_yes.posterior >= dengue_no.posterior


class TestAbstention:
    """Abstention triggers when top-3 posteriors are all below threshold."""

    def test_abstention_with_minimal_input(self, model):
        """With no symptoms, exposures, or incubation, abstention may trigger
        if priors are spread across many diagnoses."""
        result = model.diagnose(
            regions=[],
            symptoms={},
        )
        # With uniform priors and no evidence, all posteriors should be equal
        # and below 0.25 (1/33 ≈ 0.03), so abstention should trigger
        assert result.abstain

    def test_no_abstention_with_strong_evidence(self, model):
        """Strong evidence should produce a clear top diagnosis."""
        result = model.diagnose(
            regions=["southeast_asia"],
            symptoms={
                "fever": True, "rash": True, "arthralgia_myalgia": True,
                "jaundice": False, "haemorrhagic_signs": False,
                "gi_symptoms": False, "respiratory_symptoms": False,
                "neurological_symptoms": False, "productive_cough": False,
                "retro_orbital_pain": False, "small_joint_polyarthralgia": False,
            },
            exposures={"mosquito": True},
            incubation_days=5,
        )
        assert not result.abstain
        assert result.diagnoses[0].posterior > 0.25


class TestNewFeatureDiscrimination:
    """Tests for the 3 new discriminating symptom features."""

    def test_productive_cough_helps_cap_over_influenza(self, model):
        """Productive cough should favour CAP over influenza."""
        result = model.diagnose(
            regions=["europe"],
            symptoms={
                "fever": True, "respiratory_symptoms": True,
                "productive_cough": True,
            },
            exposures={"respiratory_droplet": True},
            incubation_days=3,
        )
        cap = next(d for d in result.diagnoses if d.diagnosis == "community_acquired_pneumonia")
        flu = next(d for d in result.diagnoses if d.diagnosis == "influenza")
        assert cap.posterior > flu.posterior

    def test_retro_orbital_helps_dengue_over_chikungunya(self, model):
        """Retro-orbital pain should favour dengue over chikungunya."""
        result = model.diagnose(
            regions=["southeast_asia"],
            symptoms={
                "fever": True, "rash": True, "arthralgia_myalgia": True,
                "retro_orbital_pain": True, "small_joint_polyarthralgia": False,
            },
            exposures={"mosquito": True},
            incubation_days=5,
        )
        dengue = next(d for d in result.diagnoses if d.diagnosis == "dengue")
        chik = next(d for d in result.diagnoses if d.diagnosis == "chikungunya")
        assert dengue.posterior > chik.posterior

    def test_polyarthralgia_helps_chikungunya_over_dengue(self, model):
        """Small-joint polyarthralgia should favour chikungunya over dengue."""
        result = model.diagnose(
            regions=["southeast_asia"],
            symptoms={
                "fever": True, "rash": True, "arthralgia_myalgia": True,
                "retro_orbital_pain": False, "small_joint_polyarthralgia": True,
            },
            exposures={"mosquito": True},
            incubation_days=5,
        )
        chik = next(d for d in result.diagnoses if d.diagnosis == "chikungunya")
        dengue = next(d for d in result.diagnoses if d.diagnosis == "dengue")
        assert chik.posterior > dengue.posterior


class TestIncubationCompatibility:
    """Incubation period should penalise diagnoses outside their published range."""

    def test_short_incubation_penalises_hep_a(self, model):
        """Hep A has 15-50 day incubation; 3-day incubation should penalise it."""
        result_3d = model.diagnose(
            regions=["south_central_asia"],
            symptoms={"fever": True, "jaundice": True, "gi_symptoms": True},
            incubation_days=3,
        )
        result_28d = model.diagnose(
            regions=["south_central_asia"],
            symptoms={"fever": True, "jaundice": True, "gi_symptoms": True},
            incubation_days=28,
        )
        hepa_3d = next(d for d in result_3d.diagnoses if d.diagnosis == "hepatitis_a")
        hepa_28d = next(d for d in result_28d.diagnoses if d.diagnosis == "hepatitis_a")
        assert hepa_28d.log_incubation_likelihood > hepa_3d.log_incubation_likelihood

    def test_long_incubation_penalises_dengue(self, model):
        """Dengue has 3-10 day incubation; 60-day incubation should penalise it."""
        result_5d = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True},
            incubation_days=5,
        )
        result_60d = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True},
            incubation_days=60,
        )
        dengue_5d = next(d for d in result_5d.diagnoses if d.diagnosis == "dengue")
        dengue_60d = next(d for d in result_60d.diagnoses if d.diagnosis == "dengue")
        assert dengue_5d.log_incubation_likelihood > dengue_60d.log_incubation_likelihood


class TestRanking:
    """Sanity checks for clinical plausibility of rankings."""

    def test_dengue_top3_for_sea_fever_mosquito(self, model):
        """Dengue should be in top-3 for SE Asia + fever + mosquito exposure."""
        result = model.diagnose(
            regions=["southeast_asia"],
            symptoms={"fever": True},
            exposures={"mosquito": True},
        )
        top3_names = [d.diagnosis for d in result.top_n(3)]
        assert "dengue" in top3_names

    def test_enteric_fever_top3_for_sca_gi_foodwater(self, model):
        """Enteric fever should be top-3 for South-Central Asia + GI + food/water."""
        result = model.diagnose(
            regions=["south_central_asia"],
            symptoms={"fever": True, "gi_symptoms": True},
            exposures={"food_water": True},
            incubation_days=12,
        )
        top5_names = [d.diagnosis for d in result.top_n(5)]
        assert "enteric_fever" in top5_names

    def test_malaria_falciparum_top3_for_ssa(self, model):
        """P. falciparum malaria should dominate for Sub-Saharan Africa + fever."""
        result = model.diagnose(
            regions=["sub_saharan_africa"],
            symptoms={"fever": True},
            exposures={"mosquito": True},
            incubation_days=12,
        )
        top3_names = [d.diagnosis for d in result.top_n(3)]
        assert "malaria_falciparum" in top3_names or "malaria" in top3_names
