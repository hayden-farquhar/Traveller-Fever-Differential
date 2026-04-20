"""Rule-based classifier for outbreak signals → (region, diagnosis) pairs.

Shared by ProMED and WHO DON scrapers. Uses keyword matching against
diagnosis definitions and a country-to-region mapping.

Unclassified entries are logged for manual review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Country → region mapping (covers most countries mentioned in outbreak alerts)
COUNTRY_TO_REGION: dict[str, str] = {
    # Southeast Asia
    "indonesia": "southeast_asia", "thailand": "southeast_asia",
    "vietnam": "southeast_asia", "philippines": "southeast_asia",
    "malaysia": "southeast_asia", "myanmar": "southeast_asia",
    "cambodia": "southeast_asia", "laos": "southeast_asia",
    "singapore": "southeast_asia", "timor-leste": "southeast_asia",
    "brunei": "southeast_asia",
    # South-Central Asia
    "india": "south_central_asia", "bangladesh": "south_central_asia",
    "pakistan": "south_central_asia", "sri lanka": "south_central_asia",
    "nepal": "south_central_asia", "afghanistan": "south_central_asia",
    "maldives": "south_central_asia", "bhutan": "south_central_asia",
    # Northeast Asia
    "china": "northeast_asia", "japan": "northeast_asia",
    "south korea": "northeast_asia", "korea": "northeast_asia",
    "mongolia": "northeast_asia", "taiwan": "northeast_asia",
    # Oceania
    "papua new guinea": "oceania", "fiji": "oceania",
    "vanuatu": "oceania", "samoa": "oceania",
    "tonga": "oceania", "solomon islands": "oceania",
    "new caledonia": "oceania", "french polynesia": "oceania",
    "new zealand": "oceania", "australia": "oceania",
    # Sub-Saharan Africa
    "nigeria": "sub_saharan_africa", "democratic republic of the congo": "sub_saharan_africa",
    "drc": "sub_saharan_africa", "congo": "sub_saharan_africa",
    "kenya": "sub_saharan_africa", "ethiopia": "sub_saharan_africa",
    "tanzania": "sub_saharan_africa", "uganda": "sub_saharan_africa",
    "south africa": "sub_saharan_africa", "mozambique": "sub_saharan_africa",
    "ghana": "sub_saharan_africa", "cameroon": "sub_saharan_africa",
    "mali": "sub_saharan_africa", "niger": "sub_saharan_africa",
    "chad": "sub_saharan_africa", "sudan": "sub_saharan_africa",
    "south sudan": "sub_saharan_africa", "somalia": "sub_saharan_africa",
    "madagascar": "sub_saharan_africa", "angola": "sub_saharan_africa",
    "zimbabwe": "sub_saharan_africa", "zambia": "sub_saharan_africa",
    "malawi": "sub_saharan_africa", "rwanda": "sub_saharan_africa",
    "burundi": "sub_saharan_africa", "senegal": "sub_saharan_africa",
    "guinea": "sub_saharan_africa", "sierra leone": "sub_saharan_africa",
    "liberia": "sub_saharan_africa", "burkina faso": "sub_saharan_africa",
    "ivory coast": "sub_saharan_africa", "cote d'ivoire": "sub_saharan_africa",
    # North Africa / Middle East
    "egypt": "north_africa_middle_east", "morocco": "north_africa_middle_east",
    "tunisia": "north_africa_middle_east", "algeria": "north_africa_middle_east",
    "libya": "north_africa_middle_east", "iran": "north_africa_middle_east",
    "iraq": "north_africa_middle_east", "saudi arabia": "north_africa_middle_east",
    "yemen": "north_africa_middle_east", "oman": "north_africa_middle_east",
    "uae": "north_africa_middle_east", "jordan": "north_africa_middle_east",
    "lebanon": "north_africa_middle_east", "syria": "north_africa_middle_east",
    "turkey": "north_africa_middle_east", "israel": "north_africa_middle_east",
    "palestine": "north_africa_middle_east", "qatar": "north_africa_middle_east",
    "bahrain": "north_africa_middle_east", "kuwait": "north_africa_middle_east",
    # Latin America / Caribbean
    "brazil": "latin_america_caribbean", "mexico": "latin_america_caribbean",
    "colombia": "latin_america_caribbean", "peru": "latin_america_caribbean",
    "argentina": "latin_america_caribbean", "chile": "latin_america_caribbean",
    "venezuela": "latin_america_caribbean", "ecuador": "latin_america_caribbean",
    "bolivia": "latin_america_caribbean", "paraguay": "latin_america_caribbean",
    "uruguay": "latin_america_caribbean", "cuba": "latin_america_caribbean",
    "haiti": "latin_america_caribbean", "dominican republic": "latin_america_caribbean",
    "jamaica": "latin_america_caribbean", "trinidad and tobago": "latin_america_caribbean",
    "guatemala": "latin_america_caribbean", "honduras": "latin_america_caribbean",
    "nicaragua": "latin_america_caribbean", "costa rica": "latin_america_caribbean",
    "panama": "latin_america_caribbean", "el salvador": "latin_america_caribbean",
    "suriname": "latin_america_caribbean", "guyana": "latin_america_caribbean",
    # Europe
    "united kingdom": "europe", "uk": "europe",
    "france": "europe", "germany": "europe", "italy": "europe",
    "spain": "europe", "portugal": "europe", "netherlands": "europe",
    "belgium": "europe", "greece": "europe", "sweden": "europe",
    "romania": "europe", "poland": "europe", "ukraine": "europe",
    "russia": "europe", "austria": "europe", "switzerland": "europe",
    # North America
    "united states": "north_america", "usa": "north_america",
    "canada": "north_america",
}

# Diagnosis keyword patterns (case-insensitive)
# Each maps to a pre-registered diagnosis key
DIAGNOSIS_PATTERNS: dict[str, list[str]] = {
    "malaria_falciparum": ["malaria", "plasmodium falciparum", "p. falciparum"],
    "malaria_vivax": ["plasmodium vivax", "p. vivax", "vivax malaria"],
    "dengue": ["dengue", "denv"],
    "chikungunya": ["chikungunya", "chikv"],
    "zika": ["zika", "zikv"],
    "enteric_fever": ["typhoid", "paratyphoid", "enteric fever", "salmonella typhi"],
    "acute_bacterial_gastroenteritis": ["cholera", "shigella", "campylobacter"],
    "hepatitis_a": ["hepatitis a", "hep a", "hav"],
    "hepatitis_b_acute": ["hepatitis b", "hep b", "hbv"],
    "hepatitis_e": ["hepatitis e", "hep e", "hev"],
    "rickettsial_infection": ["rickettsia", "scrub typhus", "murine typhus",
                               "tick bite fever", "spotted fever"],
    "leptospirosis": ["leptospirosis", "leptospira", "weil"],
    "acute_hiv_seroconversion": ["hiv"],
    "influenza": ["influenza", "avian influenza", "h5n1", "h7n9", "h5n6"],
    "covid_19": ["covid", "sars-cov-2", "coronavirus disease"],
    "measles": ["measles", "rubeola"],
    "japanese_encephalitis": ["japanese encephalitis", "jev"],
    "melioidosis": ["melioidosis", "burkholderia pseudomallei"],
    "tuberculosis": ["tuberculosis", "tb ", " tb,", "mycobacterium tuberculosis"],
    "schistosomiasis": ["schistosomiasis", "schistosoma", "bilharzia"],
    "strongyloides_acute": ["strongyloid"],
    "amoebiasis": ["amoebiasis", "entamoeba histolytica", "amoebic"],
    "brucellosis": ["brucellosis", "brucella"],
    "q_fever": ["q fever", "coxiella"],
    "mpox": ["mpox", "monkeypox"],
    "oropouche": ["oropouche", "orov"],
    "yellow_fever": ["yellow fever", "yfv"],
    "rabies": ["rabies", "lyssavirus"],
}


@dataclass
class ClassifiedSignal:
    """A classified outbreak signal."""
    source: str          # "promed" or "who_don"
    title: str
    date: str            # ISO date
    url: str
    diagnoses: list[str]  # matched diagnosis keys
    regions: list[str]    # matched region keys
    raw_text: str        # original text for audit
    classified: bool     # True if at least one (diagnosis, region) pair found


def classify_signal(
    title: str,
    text: str,
    source: str,
    date: str,
    url: str,
) -> ClassifiedSignal:
    """Classify a single outbreak alert into (diagnosis, region) pairs.

    Args:
        title: Alert title/subject
        text: Full text or summary of the alert
        source: "promed" or "who_don"
        date: ISO date string
        url: URL of the original alert

    Returns:
        ClassifiedSignal with matched diagnoses and regions.
    """
    combined = f"{title} {text}".lower()

    # Match diagnoses using word boundary matching to avoid false positives
    # (e.g., "hav" matching "have", "tb" matching "obtain")
    matched_dx = []
    for dx_key, patterns in DIAGNOSIS_PATTERNS.items():
        for pattern in patterns:
            if re.search(rf'\b{re.escape(pattern.lower())}\b', combined):
                if dx_key not in matched_dx:
                    matched_dx.append(dx_key)
                break

    # Special case: generic "malaria" without species → malaria_falciparum
    if "malaria_falciparum" in matched_dx and "malaria_vivax" not in matched_dx:
        pass  # Already correct
    elif "malaria_falciparum" in matched_dx and "malaria_vivax" in matched_dx:
        pass  # Both species mentioned

    # Match regions via country mentions
    matched_regions = []
    for country, region in COUNTRY_TO_REGION.items():
        # Word boundary matching to avoid false positives
        if re.search(rf'\b{re.escape(country)}\b', combined):
            if region not in matched_regions:
                matched_regions.append(region)

    classified = len(matched_dx) > 0 and len(matched_regions) > 0

    return ClassifiedSignal(
        source=source,
        title=title,
        date=date,
        url=url,
        diagnoses=matched_dx,
        regions=matched_regions,
        raw_text=combined[:500],  # Truncate for storage
        classified=classified,
    )
