"""Approximate KABISA TRAVEL replication for baseline comparison.

KABISA TRAVEL is a closed diagnostic tool developed at the Institute of
Tropical Medicine, Antwerp. Its full logic is not publicly available.
This replication is based on:
- Demeester 2010 J Travel Med (PMID 20412179): describes the algorithm
- Published validation data (~72% Top-1 accuracy)

The replication uses a simplified rule-based scoring system that
approximates KABISA's destination + symptom → diagnosis logic.

Limitations (to be documented in manuscript):
- Exact KABISA scoring weights are proprietary
- This replication may over- or under-estimate KABISA's actual performance
- The replication does NOT include KABISA's "expert system" refinements

Usage:
    from src.validation.replicate_kabisa import KABISAReplica
    model = KABISAReplica()
    result = model.diagnose(region, symptoms)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KABISAResult:
    """KABISA replication result for a single case."""
    ranked_diagnoses: list[tuple[str, float]]  # (diagnosis, score) pairs
    top_1: str
    top_5: list[str]


class KABISAReplica:
    """Approximate replication of KABISA TRAVEL diagnostic logic.

    Based on Demeester 2010 (PMID 20412179) description:
    - Destination determines which diseases are "in scope"
    - Symptom patterns select among in-scope diseases
    - Scoring is weighted by destination-specific disease frequency

    This is a SIMPLIFIED replication. The actual KABISA system uses
    a more sophisticated expert system with iterative refinement.
    """

    # Destination → disease scope (which diagnoses KABISA considers)
    # Based on KABISA's published endemic zones
    DESTINATION_SCOPE: dict[str, list[str]] = {
        "southeast_asia": [
            "dengue", "malaria_falciparum", "malaria_vivax", "chikungunya",
            "enteric_fever", "acute_bacterial_gastroenteritis", "hepatitis_a",
            "leptospirosis", "rickettsial_infection", "japanese_encephalitis",
            "melioidosis", "measles", "influenza", "tuberculosis",
            "strongyloides_acute", "covid_19",
        ],
        "south_central_asia": [
            "enteric_fever", "dengue", "malaria_vivax", "malaria_falciparum",
            "acute_bacterial_gastroenteritis", "hepatitis_a", "hepatitis_e",
            "chikungunya", "rickettsial_infection", "tuberculosis",
            "leptospirosis", "measles", "influenza", "brucellosis", "covid_19",
        ],
        "sub_saharan_africa": [
            "malaria_falciparum", "dengue", "chikungunya",
            "rickettsial_infection", "enteric_fever",
            "acute_bacterial_gastroenteritis", "schistosomiasis",
            "hepatitis_a", "tuberculosis", "measles", "yellow_fever",
            "leptospirosis", "influenza", "mpox", "covid_19",
        ],
        "latin_america_caribbean": [
            "dengue", "chikungunya", "zika", "oropouche",
            "acute_bacterial_gastroenteritis", "enteric_fever",
            "hepatitis_a", "leptospirosis", "yellow_fever",
            "malaria_falciparum", "influenza", "covid_19",
        ],
        "oceania": [
            "dengue", "malaria_vivax", "malaria_falciparum",
            "acute_bacterial_gastroenteritis", "enteric_fever",
            "leptospirosis", "melioidosis", "influenza",
            "japanese_encephalitis", "covid_19",
        ],
        "north_africa_middle_east": [
            "acute_bacterial_gastroenteritis", "hepatitis_a",
            "enteric_fever", "brucellosis", "rickettsial_infection",
            "tuberculosis", "influenza", "measles", "covid_19",
        ],
        "europe": [
            "influenza", "covid_19", "community_acquired_pneumonia",
            "viral_urti", "rickettsial_infection", "measles",
            "infectious_mononucleosis", "acute_bacterial_gastroenteritis",
        ],
        "northeast_asia": [
            "influenza", "covid_19", "viral_urti",
            "community_acquired_pneumonia", "hepatitis_a",
            "acute_bacterial_gastroenteritis", "measles",
        ],
        "north_america": [
            "influenza", "covid_19", "viral_urti",
            "community_acquired_pneumonia", "uti_pyelonephritis",
            "infectious_mononucleosis",
        ],
    }

    # Symptom → diagnosis scoring weights (simplified KABISA-style rules)
    # Higher = more associated
    SYMPTOM_SCORES: dict[str, dict[str, float]] = {
        "dengue": {"fever": 3, "rash": 2, "arthralgia_myalgia": 2,
                   "haemorrhagic_signs": 3, "gi_symptoms": 1},
        "malaria_falciparum": {"fever": 4, "arthralgia_myalgia": 1,
                               "neurological_symptoms": 2},
        "malaria_vivax": {"fever": 4, "arthralgia_myalgia": 1},
        "chikungunya": {"fever": 2, "rash": 2, "arthralgia_myalgia": 5},
        "enteric_fever": {"fever": 4, "gi_symptoms": 3, "rash": 1,
                          "respiratory_symptoms": 1},
        "acute_bacterial_gastroenteritis": {"fever": 1, "gi_symptoms": 5,
                                            "haemorrhagic_signs": 1},
        "hepatitis_a": {"fever": 1, "jaundice": 5, "gi_symptoms": 3},
        "hepatitis_e": {"fever": 1, "jaundice": 5, "gi_symptoms": 3},
        "rickettsial_infection": {"fever": 3, "rash": 3, "arthralgia_myalgia": 2},
        "leptospirosis": {"fever": 3, "jaundice": 3, "arthralgia_myalgia": 3,
                          "neurological_symptoms": 1},
        "measles": {"fever": 3, "rash": 4, "respiratory_symptoms": 3},
        "influenza": {"fever": 3, "arthralgia_myalgia": 2,
                      "respiratory_symptoms": 4},
        "covid_19": {"fever": 2, "respiratory_symptoms": 4,
                     "arthralgia_myalgia": 1, "neurological_symptoms": 1},
        "japanese_encephalitis": {"fever": 3, "neurological_symptoms": 5},
        "melioidosis": {"fever": 3, "respiratory_symptoms": 3,
                        "gi_symptoms": 1},
        "tuberculosis": {"fever": 2, "respiratory_symptoms": 4,
                         "haemorrhagic_signs": 1},
        "schistosomiasis": {"fever": 2, "rash": 2, "arthralgia_myalgia": 1,
                            "gi_symptoms": 2, "haemorrhagic_signs": 2},
        "zika": {"fever": 1, "rash": 3, "arthralgia_myalgia": 2},
        "oropouche": {"fever": 3, "arthralgia_myalgia": 3, "gi_symptoms": 1},
        "yellow_fever": {"fever": 3, "jaundice": 4, "haemorrhagic_signs": 3},
        "mpox": {"fever": 2, "rash": 5, "gi_symptoms": 1},
        "brucellosis": {"fever": 3, "arthralgia_myalgia": 3, "gi_symptoms": 1},
        "strongyloides_acute": {"fever": 1, "rash": 2,
                                "respiratory_symptoms": 2, "gi_symptoms": 2},
        "hepatitis_b_acute": {"fever": 1, "jaundice": 4, "rash": 1,
                              "arthralgia_myalgia": 2},
        "acute_hiv_seroconversion": {"fever": 2, "rash": 2,
                                     "arthralgia_myalgia": 2,
                                     "respiratory_symptoms": 1},
        "amoebiasis": {"fever": 2, "gi_symptoms": 4, "jaundice": 1},
        "q_fever": {"fever": 3, "respiratory_symptoms": 2,
                    "arthralgia_myalgia": 2},
        "rabies": {"fever": 1, "neurological_symptoms": 5},
        "community_acquired_pneumonia": {"fever": 3, "respiratory_symptoms": 5,
                                         "arthralgia_myalgia": 1},
        "uti_pyelonephritis": {"fever": 3, "gi_symptoms": 2},
        "viral_urti": {"fever": 1, "respiratory_symptoms": 4,
                       "arthralgia_myalgia": 1},
        "infectious_mononucleosis": {"fever": 3, "respiratory_symptoms": 2,
                                     "rash": 1, "jaundice": 1,
                                     "arthralgia_myalgia": 2},
        "undifferentiated_viral_syndrome": {"fever": 2, "arthralgia_myalgia": 1,
                                            "rash": 1},
    }

    def diagnose(
        self,
        region: str,
        symptoms: dict[str, bool],
    ) -> KABISAResult:
        """Run KABISA-style rule-based diagnosis.

        Args:
            region: Travel destination region
            symptoms: Dict of symptom_name -> present

        Returns:
            KABISAResult with ranked diagnoses
        """
        # Get diseases in scope for this destination
        in_scope = self.DESTINATION_SCOPE.get(region, [])
        if not in_scope:
            # Unknown region — use all diseases
            in_scope = list(self.SYMPTOM_SCORES.keys())

        # Score each in-scope disease
        scores: list[tuple[str, float]] = []
        for dx in in_scope:
            score = 0.0
            dx_weights = self.SYMPTOM_SCORES.get(dx, {})
            for symptom, present in symptoms.items():
                if present and symptom in dx_weights:
                    score += dx_weights[symptom]
            scores.append((dx, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)

        top_1 = scores[0][0] if scores else ""
        top_5 = [s[0] for s in scores[:5]]

        return KABISAResult(
            ranked_diagnoses=scores,
            top_1=top_1,
            top_5=top_5,
        )
