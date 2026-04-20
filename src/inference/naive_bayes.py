"""BEACON — Naive Bayes inference engine for febrile returned-traveller differential diagnosis.

Computes:
    P(dx | destination, symptoms, exposures, incubation) ∝
        P(dx | destination) ×
        ∏ P(symptom_i | dx) ×
        ∏ P(exposure_j | dx) ×
        P(incubation | dx)

Output: ranked differential with per-factor log-evidence breakdown.
Abstention: if top-3 posteriors all < 0.25, returns abstention signal.

Usage:
    from src.inference.naive_bayes import TravellerFeverModel
    model = TravellerFeverModel.from_yaml(priors_path, definitions_path)
    result = model.diagnose(
        regions=["southeast_asia"],
        symptoms={"fever": True, "rash": True, "arthralgia_myalgia": True},
        exposures={"mosquito": True},
        incubation_days=5,
    )
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

logger = logging.getLogger(__name__)

# Symptom and exposure feature names used in the inference schema
SYMPTOM_FEATURES = [
    "fever",
    "rash",
    "arthralgia_myalgia",
    "jaundice",
    "haemorrhagic_signs",
    "gi_symptoms",
    "respiratory_symptoms",
    "neurological_symptoms",
    "productive_cough",
    "retro_orbital_pain",
    "small_joint_polyarthralgia",
]

EXPOSURE_FEATURES = [
    "mosquito",
    "freshwater",
    "animal_contact",
    "sexual",
    "needle_blood",
    "food_water",
    "respiratory_droplet",
    "tick",
]

# Pre-registered constants
ABSTENTION_THRESHOLD = 0.25
TOP_K_ABSTENTION = 3

# ---------------------------------------------------------------------------
# Fix 2: Symptom likelihood ratios with base rates
# ---------------------------------------------------------------------------
# Instead of raw P(symptom|dx), the model uses the likelihood ratio:
#   LR = P(symptom|dx) / P(symptom|febrile traveller)
# This makes common symptoms (fever, myalgia) less discriminating
# and rare symptoms (jaundice, haemorrhagic) more discriminating.

# Graded symptom probabilities: P(symptom present | dx has grade)
# Values can also be floats (0.0-1.0) for exact published prevalences.
SYMPTOM_GRADE_PRESENT: dict[str, float] = {
    "high": 0.85,
    "moderate": 0.50,
    "low": 0.15,
    "false": 0.05,
    True: 0.60,       # backwards compatibility
    False: 0.05,
}


def resolve_symptom_probability(grade) -> float:
    """Convert a YAML symptom value to P(symptom present | dx).

    Accepts:
    - String grades: "high", "moderate", "low", "false"
    - Float/int: exact prevalence (0.0-1.0), used directly
    - Boolean: True/False (backwards compatibility)
    """
    if isinstance(grade, (int, float)) and not isinstance(grade, bool):
        # Exact prevalence value — clamp to [0.01, 0.99]
        return max(0.01, min(0.99, float(grade)))
    return SYMPTOM_GRADE_PRESENT.get(grade, 0.05)

# Base rates: P(symptom present | febrile returned traveller, any diagnosis)
# These represent the background prevalence of each symptom among the
# population presenting to this tool (febrile returned travellers).
# Sources: Leder 2013, Wilson 2007 NEJM, O'Brien 2006 MJA
SYMPTOM_BASE_RATES: dict[str, float] = {
    "fever": 0.95,                  # selection criterion — nearly all have it
    "rash": 0.15,                   # ~15% of febrile travellers
    "arthralgia_myalgia": 0.40,     # ~40% — very common in febrile illness
    "jaundice": 0.05,               # ~5% — rare, highly specific
    "haemorrhagic_signs": 0.05,     # ~5% — rare, alarming
    "gi_symptoms": 0.35,            # ~35% — very common
    "respiratory_symptoms": 0.25,   # ~25%
    "neurological_symptoms": 0.08,  # ~8% (beyond headache)
    "productive_cough": 0.12,       # ~12% — most febrile coughs are dry
    "retro_orbital_pain": 0.08,     # ~8% — uncommon; relatively specific to dengue
    "small_joint_polyarthralgia": 0.10,  # ~10% — general myalgia common, small-joint specific is rare
}

# ---------------------------------------------------------------------------
# Exposure likelihoods
# ---------------------------------------------------------------------------
# Fix 3: exposure absence as negative evidence
P_EXPOSURE_GIVEN_ROUTE = 0.70
P_EXPOSURE_GIVEN_NOT_ROUTE = 0.05
# When patient DENIES an exposure, diseases requiring that route are penalised
P_ABSENT_EXPOSURE_GIVEN_ROUTE = 0.30       # 1 - P_EXPOSURE_GIVEN_ROUTE
P_ABSENT_EXPOSURE_GIVEN_NOT_ROUTE = 0.95   # 1 - P_EXPOSURE_GIVEN_NOT_ROUTE


# ---------------------------------------------------------------------------
# Must-not-miss safety rules
# ---------------------------------------------------------------------------
# These fire regardless of posterior probability. They are clinical safety
# overrides, not diagnostic predictions.

@dataclass
class SafetyAlert:
    """A must-not-miss clinical safety alert."""
    diagnosis: str
    alert: str
    action: str
    severity: str       # "critical", "high", "moderate"
    references: str     # citation(s) supporting this alert

# Regions where malaria is endemic
MALARIA_ENDEMIC_REGIONS = {
    "sub_saharan_africa", "south_central_asia", "southeast_asia",
    "oceania", "latin_america_caribbean", "north_africa_middle_east",
}

# Diseases preventable by vaccination — prior reduced by this factor if vaccinated
# Ref: CDC Yellow Book 2024 immunisation chapters; WHO position papers
VACCINE_PREVENTABLE: dict[str, list[str]] = {
    "hepatitis_a": ["hepatitis_a"],
    "measles": ["measles"],
    "yellow_fever": ["yellow_fever"],
    "japanese_encephalitis": ["japanese_encephalitis"],
}
VACCINATION_PRIOR_REDUCTION = 0.05  # 95% reduction — vaccine efficacy ≥95% for all listed


def generate_safety_alerts(
    regions: list[str],
    symptoms: dict[str, bool],
    exposures: dict[str, bool],
) -> list[SafetyAlert]:
    """Generate must-not-miss safety alerts based on clinical context.

    These are evidence-based clinical safety rules that fire regardless
    of posterior probability. Each alert is cited to a published guideline
    or consensus recommendation.
    """
    alerts = []

    # Malaria: any febrile traveller from endemic area
    # Ref: WHO Guidelines for Malaria 2023 (3rd ed), §1.1;
    #      Australasian Society for Infectious Diseases (ASID) guidelines
    #      for returned traveller (Leung 2014, MJA 200(8):477-80, PMID 24794608);
    #      CDC Yellow Book 2024, Malaria chapter: "Malaria should be considered
    #      in any febrile patient who has travelled to a malaria-endemic area."
    if any(r in MALARIA_ENDEMIC_REGIONS for r in regions):
        alerts.append(SafetyAlert(
            diagnosis="malaria",
            alert="Malaria must be excluded in any febrile traveller from an endemic area",
            action="Request thick/thin blood film AND rapid diagnostic test (RDT) regardless "
                   "of clinical probability. Repeat at 12-24h intervals if initially negative.",
            severity="critical",
            references="WHO Malaria Guidelines 2023; ASID returned traveller guidelines "
                       "(Leung 2014, PMID 24794608); CDC Yellow Book 2024",
        ))

    # Measles: rash + fever + respiratory from any destination
    # Ref: CDNA National Guidelines for Public Health Units — Measles (2019);
    #      WHO measles fact sheet: "any person with fever and maculopapular rash
    #      with cough, coryza, or conjunctivitis should be considered a suspect case";
    #      Australian Immunisation Handbook (ATAGI): contact/airborne precautions
    if symptoms.get("rash") and symptoms.get("respiratory_symptoms"):
        alerts.append(SafetyAlert(
            diagnosis="measles",
            alert="Measles is highly contagious and must be considered with fever + rash + respiratory symptoms",
            action="Isolate patient immediately (airborne precautions). Check vaccination status. "
                   "Request measles IgM serology and nasopharyngeal swab for PCR. "
                   "Notify public health if clinically suspected (notifiable in all Australian states).",
            severity="high",
            references="CDNA National Measles Guidelines 2019; WHO measles surveillance standards; "
                       "Australian Immunisation Handbook (ATAGI)",
        ))

    # VHF/high-consequence: haemorrhagic signs from SSA
    # Ref: PHE Advisory Committee on Dangerous Pathogens (ACDP) guidelines:
    #      "viral haemorrhagic fever: ACDP algorithm and guidance on management
    #      of patients" (2017); ASID high-consequence infectious diseases protocol;
    #      Emerging Infectious Diseases assessment guidelines (NSW Health 2023)
    if symptoms.get("haemorrhagic_signs") and "sub_saharan_africa" in regions:
        alerts.append(SafetyAlert(
            diagnosis="viral_haemorrhagic_fever",
            alert="Haemorrhagic signs in a traveller from Sub-Saharan Africa — consider VHF",
            action="Activate high-consequence infectious disease protocol. "
                   "Contact infectious diseases and public health IMMEDIATELY. "
                   "Standard + contact + droplet precautions minimum. "
                   "Do NOT perform aerosol-generating procedures until VHF excluded.",
            severity="critical",
            references="UK ACDP VHF Guidelines 2017; NSW Health HCID Protocol 2023; "
                       "ASID position statement on VHF management",
        ))

    # Mpox: vesiculopustular rash + sexual/animal exposure
    # Ref: WHO mpox interim guidance (2024); CDNA Mpox CDPLAN (2024);
    #      Thornhill 2022 NEJM 387:679 (clade IIb clinical features)
    if symptoms.get("rash") and (exposures.get("sexual") or exposures.get("animal_contact")):
        alerts.append(SafetyAlert(
            diagnosis="mpox",
            alert="Vesiculopustular rash with sexual or animal contact — consider mpox",
            action="Isolate (contact + droplet precautions). "
                   "Notify public health (nationally notifiable). "
                   "Swab lesion base for OPXV PCR. "
                   "Assess for HIV co-testing if sexual exposure.",
            severity="high",
            references="WHO Mpox Interim Guidance 2024; CDNA Mpox CDPLAN 2024; "
                       "Thornhill 2022 NEJM (PMID 35866746)",
        ))

    return alerts


@dataclass
class DiagnosisResult:
    """Result for a single diagnosis in the differential."""
    diagnosis: str
    posterior: float
    log_posterior: float
    log_prior: float
    log_symptom_likelihood: float
    log_exposure_likelihood: float
    log_incubation_likelihood: float
    rank: int = 0


@dataclass
class DifferentialResult:
    """Complete differential diagnosis result."""
    diagnoses: list[DiagnosisResult]
    abstain: bool
    abstention_reason: str = ""
    regions_used: list[str] = field(default_factory=list)
    n_diagnoses: int = 0
    safety_alerts: list[SafetyAlert] = field(default_factory=list)

    def top_n(self, n: int = 10) -> list[DiagnosisResult]:
        return self.diagnoses[:n]

    def summary(self) -> str:
        lines = []
        if self.safety_alerts:
            for alert in self.safety_alerts:
                sev = "🔴" if alert.severity == "critical" else "🟠"
                lines.append(f"{sev} SAFETY: {alert.alert}")
                lines.append(f"   → {alert.action}")
                lines.append(f"   Ref: {alert.references}")
            lines.append("")
        if self.abstain:
            lines.append(f"⚠ ABSTENTION: {self.abstention_reason}")
            lines.append("")
        lines.append(f"Top differential (regions: {', '.join(self.regions_used)}):")
        for dx in self.top_n(10):
            lines.append(
                f"  {dx.rank}. {dx.diagnosis:40s} "
                f"P={dx.posterior:.3f}  "
                f"[prior={dx.log_prior:+.2f}, "
                f"sx={dx.log_symptom_likelihood:+.2f}, "
                f"exp={dx.log_exposure_likelihood:+.2f}, "
                f"inc={dx.log_incubation_likelihood:+.2f}]"
            )
        return "\n".join(lines)


@dataclass
class DiseaseDefinition:
    """Clinical definition of a disease for inference."""
    name: str
    incubation_min: float
    incubation_max: float
    incubation_mode: float         # typical/peak incubation (for triangular dist)
    symptoms: dict[str, str | bool]
    exposures: dict[str, bool]


# ---------------------------------------------------------------------------
# Fix 1: Peaked incubation — parse "typical" field into a numeric mode
# ---------------------------------------------------------------------------

def parse_incubation_mode(typical_str: str, inc_min: float, inc_max: float) -> float:
    """Parse the 'typical' incubation field into a numeric mode.

    Handles formats: "3-7", "28", "2", "weeks to months", "typhoid 8-14; ..."
    Falls back to midpoint of min-max if unparseable.
    """
    if not typical_str:
        return (inc_min + inc_max) / 2

    s = str(typical_str).strip().lower()

    # Try single number: "28", "2"
    try:
        return float(s)
    except ValueError:
        pass

    # Try range: "3-7", "5-14", "14-21"
    m = re.match(r'^(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2

    # Try "X to Y": "2-4 weeks" → take midpoint
    m = re.match(r'^(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*weeks?', s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2 * 7

    # Try compound: "typhoid 8-14; paratyphoid 1-10" → take first range
    m = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', s)
    if m:
        return (float(m.group(1)) + float(m.group(2))) / 2

    # "weeks to months" → ~30 days
    if "week" in s and "month" in s:
        return 42.0
    if "weeks to years" in s:
        return 60.0
    if "week" in s:
        return 21.0
    if "month" in s:
        return 60.0

    # Fallback: midpoint
    return (inc_min + inc_max) / 2


class TravellerFeverModel:
    """Naive Bayes model for febrile returned-traveller differential diagnosis."""

    DEFINITION_KEY_MAP = {
        "enteric_fever": "typhoid_and_paratyphoid_fever",
        "rickettsial_infection": "rickettsial_diseases",
    }

    def __init__(
        self,
        destination_priors: dict[str, dict[str, float]],
        disease_definitions: dict[str, DiseaseDefinition],
        live_multipliers: Optional[dict[str, dict[str, float]]] = None,
    ):
        self.destination_priors = destination_priors
        self.diseases = disease_definitions
        self.live_multipliers = live_multipliers or {}
        first_region = next(iter(destination_priors))
        self._diagnosis_names = sorted(destination_priors[first_region].keys())

    def _resolve_definition_key(self, dx_name: str) -> str:
        """Map a priors diagnosis name to its YAML definition key."""
        return self.DEFINITION_KEY_MAP.get(dx_name, dx_name)

    @classmethod
    def from_yaml(
        cls,
        priors_path: Path,
        definitions_path: Path,
        live_multipliers_path: Optional[Path] = None,
    ) -> TravellerFeverModel:
        """Load model from YAML files."""
        with open(priors_path) as f:
            raw = yaml.safe_load(f)
        destination_priors = raw["priors"]

        with open(definitions_path) as f:
            raw_defs = yaml.safe_load(f)

        diseases = {}
        for name, defn in raw_defs["diseases"].items():
            symptoms = {k: v for k, v in defn.get("symptoms", {}).items()
                        if k in SYMPTOM_FEATURES}
            exposures = {k: v for k, v in defn.get("exposure_routes", {}).items()
                         if k in EXPOSURE_FEATURES}

            inc_min = float(defn["incubation_days"]["min"])
            inc_max = float(defn["incubation_days"]["max"])
            typical = str(defn["incubation_days"].get("typical", ""))
            inc_mode = parse_incubation_mode(typical, inc_min, inc_max)
            # Clamp mode within [min, max]
            inc_mode = max(inc_min, min(inc_max, inc_mode))

            diseases[name] = DiseaseDefinition(
                name=name,
                incubation_min=inc_min,
                incubation_max=inc_max,
                incubation_mode=inc_mode,
                symptoms=symptoms,
                exposures=exposures,
            )

        live_mult = None
        if live_multipliers_path and live_multipliers_path.exists():
            with open(live_multipliers_path) as f:
                raw_live = yaml.safe_load(f)
            if raw_live:
                live_mult = raw_live.get("multipliers", raw_live)

        return cls(destination_priors, diseases, live_mult)

    def _compute_prior(
        self,
        dx_name: str,
        regions: list[str],
    ) -> float:
        """Compute P(dx | destination) as average over selected regions."""
        if not regions:
            return 1.0 / len(self._diagnosis_names)

        prior_sum = 0.0
        for r in regions:
            region_priors = self.destination_priors.get(r, {})
            base = region_priors.get(dx_name, 1e-4)

            if r in self.live_multipliers:
                mult = self.live_multipliers[r].get(dx_name, 1.0)
                mult = min(mult, 3.0)
                base *= mult

            prior_sum += base

        return prior_sum / len(regions)

    def _compute_symptom_likelihood(
        self,
        dx_name: str,
        symptoms: dict[str, bool],
    ) -> float:
        """Compute ∏ LR(symptom_i | dx) in log space.

        Uses likelihood ratios: LR = P(symptom|dx) / P(symptom|background)
        This makes common symptoms (fever) non-discriminating and rare
        symptoms (jaundice) highly discriminating.
        """
        key = self._resolve_definition_key(dx_name)
        if key not in self.diseases:
            return 0.0

        defn = self.diseases[key]
        log_lik = 0.0

        for symptom, present in symptoms.items():
            if symptom not in SYMPTOM_FEATURES:
                continue

            grade = defn.symptoms.get(symptom, "false")
            p_dx = resolve_symptom_probability(grade)
            p_base = SYMPTOM_BASE_RATES.get(symptom, 0.20)

            if present:
                # Likelihood ratio: P(symptom present | dx) / P(symptom present | background)
                lr = p_dx / p_base
            else:
                # P(symptom absent | dx) / P(symptom absent | background)
                lr = (1.0 - p_dx) / (1.0 - p_base)

            # Clamp to avoid extreme ratios
            lr = max(lr, 0.01)
            lr = min(lr, 50.0)

            log_lik += math.log(lr)

        return log_lik

    def _compute_exposure_likelihood(
        self,
        dx_name: str,
        exposures: dict[str, bool],
    ) -> float:
        """Compute ∏ P(exposure_j | dx) in log space.

        Fix 3: both reported AND denied exposures contribute evidence.
        Denied exposure penalises diseases that require that route.
        """
        key = self._resolve_definition_key(dx_name)
        if key not in self.diseases:
            return 0.0

        defn = self.diseases[key]
        log_lik = 0.0

        for exposure, reported in exposures.items():
            if exposure not in EXPOSURE_FEATURES:
                continue

            dx_has_route = defn.exposures.get(exposure, False)

            if reported:
                if dx_has_route:
                    log_lik += math.log(P_EXPOSURE_GIVEN_ROUTE)
                else:
                    log_lik += math.log(P_EXPOSURE_GIVEN_NOT_ROUTE)
            else:
                # Exposure explicitly denied — penalise diseases needing it
                if dx_has_route:
                    log_lik += math.log(P_ABSENT_EXPOSURE_GIVEN_ROUTE)
                else:
                    log_lik += math.log(P_ABSENT_EXPOSURE_GIVEN_NOT_ROUTE)

        return log_lik

    def _compute_incubation_likelihood(
        self,
        dx_name: str,
        incubation_days: Optional[float],
    ) -> float:
        """Compute P(incubation | dx) using triangular distribution.

        Fix 1: Peaked at the typical/modal incubation period, not uniform.
        A 12-day incubation for malaria (typical 10-15d) gets high density,
        not the density of a uniform distribution over 7-365 days.

        Outside the published range, exponential decay penalty applies.
        """
        key = self._resolve_definition_key(dx_name)
        if incubation_days is None or key not in self.diseases:
            return 0.0

        defn = self.diseases[key]
        a = defn.incubation_min
        b = defn.incubation_max
        c = defn.incubation_mode   # peak of the triangle

        range_width = max(b - a, 0.5)

        if a <= incubation_days <= b:
            # Triangular distribution density
            # f(x) = 2(x-a) / ((b-a)(c-a))        if a <= x <= c
            # f(x) = 2(b-x) / ((b-a)(b-c))        if c < x <= b
            if c <= a:
                # Degenerate: mode at min — use right-triangle
                density = 2.0 * (b - incubation_days) / (range_width * range_width)
            elif c >= b:
                # Degenerate: mode at max — use left-triangle
                density = 2.0 * (incubation_days - a) / (range_width * range_width)
            elif incubation_days <= c:
                density = 2.0 * (incubation_days - a) / (range_width * (c - a))
            else:
                density = 2.0 * (b - incubation_days) / (range_width * (b - c))

            # Avoid log(0)
            density = max(density, 1e-10)
            return math.log(density)
        else:
            # Outside range: exponential decay from boundary
            if incubation_days < a:
                dist = a - incubation_days
            else:
                dist = incubation_days - b

            # Density at boundary for smooth transition
            if incubation_days < a and c > a:
                boundary_density = 1e-6  # density at min is 0 for triangular
            elif incubation_days > b and c < b:
                boundary_density = 1e-6
            else:
                boundary_density = 2.0 / range_width  # peak density

            # Decay with half-life proportional to range width
            half_life = max(range_width * 0.1, 1.0)
            penalty = boundary_density * math.exp(-dist / half_life)
            penalty = max(penalty, 1e-10)
            return math.log(penalty)

    def diagnose(
        self,
        regions: list[str],
        symptoms: dict[str, bool],
        exposures: Optional[dict[str, bool]] = None,
        incubation_days: Optional[float] = None,
        vaccinations: Optional[list[str]] = None,
    ) -> DifferentialResult:
        """Run Naive Bayes inference and return ranked differential.

        Args:
            regions: List of travel destination regions
            symptoms: Dict of symptom_name -> present (True/False)
            exposures: Dict of exposure_name -> reported (True/False).
                       Include False entries for explicitly denied exposures.
            incubation_days: Days between return and symptom onset
            vaccinations: List of vaccines received (e.g. ["hepatitis_a", "measles"]).
                          Vaccinated diseases have prior reduced by 95%.

        Returns:
            DifferentialResult with ranked diagnoses, evidence breakdown,
            and safety alerts.
        """
        exposures = exposures or {}
        vaccinations = vaccinations or []

        # Build set of diagnoses with reduced priors due to vaccination
        vaccinated_dx: set[str] = set()
        for vaccine in vaccinations:
            for dx in VACCINE_PREVENTABLE.get(vaccine, []):
                vaccinated_dx.add(dx)

        results: list[DiagnosisResult] = []

        for dx_name in self._diagnosis_names:
            prior = self._compute_prior(dx_name, regions)

            # Apply vaccination reduction
            if dx_name in vaccinated_dx:
                prior *= VACCINATION_PRIOR_REDUCTION

            log_prior = math.log(max(prior, 1e-10))

            log_sx = self._compute_symptom_likelihood(dx_name, symptoms)
            log_exp = self._compute_exposure_likelihood(dx_name, exposures)
            log_inc = self._compute_incubation_likelihood(dx_name, incubation_days)

            log_posterior = log_prior + log_sx + log_exp + log_inc

            results.append(DiagnosisResult(
                diagnosis=dx_name,
                posterior=0.0,
                log_posterior=log_posterior,
                log_prior=log_prior,
                log_symptom_likelihood=log_sx,
                log_exposure_likelihood=log_exp,
                log_incubation_likelihood=log_inc,
            ))

        # Normalise posteriors using log-sum-exp
        log_posteriors = np.array([r.log_posterior for r in results])
        log_max = np.max(log_posteriors)
        log_sum = log_max + np.log(np.sum(np.exp(log_posteriors - log_max)))

        for i, r in enumerate(results):
            r.posterior = float(np.exp(r.log_posterior - log_sum))

        results.sort(key=lambda r: r.posterior, reverse=True)
        for i, r in enumerate(results):
            r.rank = i + 1

        abstain = False
        abstention_reason = ""
        top_k = results[:TOP_K_ABSTENTION]
        if all(r.posterior < ABSTENTION_THRESHOLD for r in top_k):
            abstain = True
            top_posteriors = ", ".join(f"{r.posterior:.3f}" for r in top_k)
            abstention_reason = (
                f"Insufficient discrimination — top-{TOP_K_ABSTENTION} posteriors "
                f"all below {ABSTENTION_THRESHOLD} ({top_posteriors}). "
                f"Consider specialist referral."
            )

        # Generate safety alerts
        alerts = generate_safety_alerts(regions, symptoms, exposures)

        return DifferentialResult(
            diagnoses=results,
            abstain=abstain,
            abstention_reason=abstention_reason,
            regions_used=regions,
            n_diagnoses=len(results),
            safety_alerts=alerts,
        )


def main() -> None:
    """Demo: run a sample case through the model."""
    from src.utils import CLINICAL_DIR, PROCESSED_DIR

    logging.basicConfig(level=logging.INFO)

    priors_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    if not priors_path.exists():
        priors_path = PROCESSED_DIR / "destination_priors.yaml"
    defs_path = CLINICAL_DIR / "cdc_yellow_book_extraction.yaml"

    if not priors_path.exists():
        print("Run build_base_priors.py first to generate destination_priors.yaml")
        return

    model = TravellerFeverModel.from_yaml(priors_path, defs_path)

    print("=" * 70)
    print("CASE: 24yo returned from Lombok, 5 days post-return")
    print("Symptoms: fever, rash, arthralgia/myalgia")
    print("Exposures: mosquito bites")
    print("Incubation: 5 days")
    print("=" * 70)

    result = model.diagnose(
        regions=["southeast_asia"],
        symptoms={
            "fever": True, "rash": True, "arthralgia_myalgia": True,
            "jaundice": False, "haemorrhagic_signs": False,
            "gi_symptoms": False, "respiratory_symptoms": False,
            "neurological_symptoms": False,
        },
        exposures={"mosquito": True},
        incubation_days=5,
    )
    print(result.summary())

    print("\n" + "=" * 70)
    print("CASE: 30yo returned from Delhi, 10 days post-return")
    print("Symptoms: fever, GI symptoms")
    print("Exposures: food/water")
    print("Incubation: 10 days")
    print("=" * 70)

    result2 = model.diagnose(
        regions=["south_central_asia"],
        symptoms={
            "fever": True, "rash": False, "arthralgia_myalgia": False,
            "jaundice": False, "haemorrhagic_signs": False,
            "gi_symptoms": True, "respiratory_symptoms": False,
            "neurological_symptoms": False,
        },
        exposures={"food_water": True},
        incubation_days=10,
    )
    print(result2.summary())


if __name__ == "__main__":
    main()
