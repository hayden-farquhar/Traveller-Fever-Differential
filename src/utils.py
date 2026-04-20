"""Shared utilities for the traveller fever differential pipeline."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
CLINICAL_DIR = DATA_DIR / "clinical_knowledge"

# Output directories
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
SUPPLEMENTARY_DIR = OUTPUTS_DIR / "supplementary"


def ensure_dirs() -> None:
    """Create all data/output directories if they don't exist."""
    for d in [
        RAW_DIR / "geosentinel",
        RAW_DIR / "nndss",
        RAW_DIR / "promed_archive",
        RAW_DIR / "who_don_archive",
        INTERIM_DIR,
        PROCESSED_DIR,
        CLINICAL_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        SUPPLEMENTARY_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
