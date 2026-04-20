"""Tests for signal classification and outbreak smoothing."""

import json
import tempfile
from pathlib import Path

import pytest

from src.ingest.signal_classifier import classify_signal
from src.priors.live_outbreak_smoothing import (
    ALPHA,
    MAX_MULTIPLIER,
    compute_multipliers,
    count_signals_by_month,
    exponential_smoothing,
    load_signals,
)


class TestSignalClassifier:
    def test_dengue_thailand(self):
        signal = classify_signal(
            title="Dengue outbreak - Thailand",
            text="Thailand reports 50,000 dengue cases in 2024",
            source="promed",
            date="2024-08-15T00:00:00+00:00",
            url="https://example.com/1",
        )
        assert signal.classified
        assert "dengue" in signal.diagnoses
        assert "southeast_asia" in signal.regions

    def test_mpox_drc(self):
        signal = classify_signal(
            title="Mpox - Democratic Republic of the Congo",
            text="DRC reports clade Ia mpox outbreak in Equateur province",
            source="who_don",
            date="2024-09-01T00:00:00+00:00",
            url="https://example.com/2",
        )
        assert signal.classified
        assert "mpox" in signal.diagnoses
        assert "sub_saharan_africa" in signal.regions

    def test_unclassifiable(self):
        signal = classify_signal(
            title="Conference announcement",
            text="Annual meeting of the International Society of Travel Medicine",
            source="promed",
            date="2024-10-01T00:00:00+00:00",
            url="https://example.com/3",
        )
        assert not signal.classified
        assert len(signal.diagnoses) == 0

    def test_multiple_matches(self):
        signal = classify_signal(
            title="Dengue and chikungunya - India",
            text="Co-circulation of dengue and chikungunya in Mumbai, India",
            source="promed",
            date="2024-07-01T00:00:00+00:00",
            url="https://example.com/4",
        )
        assert signal.classified
        assert "dengue" in signal.diagnoses
        assert "chikungunya" in signal.diagnoses
        assert "south_central_asia" in signal.regions

    def test_oropouche_brazil(self):
        signal = classify_signal(
            title="Oropouche virus disease - Brazil",
            text="Brazil reports expansion of Oropouche cases to southeastern states",
            source="who_don",
            date="2024-08-20T00:00:00+00:00",
            url="https://example.com/5",
        )
        assert signal.classified
        assert "oropouche" in signal.diagnoses
        assert "latin_america_caribbean" in signal.regions


class TestOutbreakSmoothing:
    def _make_signals(self):
        """Create synthetic signals for testing."""
        return [
            {"date": "2024-07-15T00:00:00+00:00", "regions": ["southeast_asia"],
             "diagnoses": ["dengue"], "classified": True},
            {"date": "2024-07-20T00:00:00+00:00", "regions": ["southeast_asia"],
             "diagnoses": ["dengue"], "classified": True},
            {"date": "2024-08-05T00:00:00+00:00", "regions": ["southeast_asia"],
             "diagnoses": ["dengue"], "classified": True},
            {"date": "2024-08-10T00:00:00+00:00", "regions": ["sub_saharan_africa"],
             "diagnoses": ["mpox"], "classified": True},
        ]

    def test_count_signals(self):
        signals = self._make_signals()
        counts = count_signals_by_month(signals)
        assert "2024-07" in counts
        assert "2024-08" in counts
        assert counts["2024-07"]["southeast_asia"]["dengue"] == 2
        assert counts["2024-08"]["southeast_asia"]["dengue"] == 1
        assert counts["2024-08"]["sub_saharan_africa"]["mpox"] == 1

    def test_smoothing_produces_elevated(self):
        signals = self._make_signals()
        counts = count_signals_by_month(signals)
        smoothed = exponential_smoothing(counts)
        # Dengue in SE Asia should have positive smoothed value
        assert smoothed["southeast_asia"]["dengue"] > 0
        # Non-signalled cells should be near zero
        assert smoothed["europe"]["dengue"] == 0.0

    def test_multiplier_cap(self):
        """Multipliers must not exceed MAX_MULTIPLIER."""
        # Create extreme smoothed values
        smoothed = {"southeast_asia": {"dengue": 10.0}}
        for dx in ["malaria_falciparum"]:
            smoothed["southeast_asia"][dx] = 0.0
        multipliers = compute_multipliers(
            {"southeast_asia": {"dengue": 10.0, "malaria_falciparum": 0.0}},
        )
        assert multipliers["southeast_asia"]["dengue"] == MAX_MULTIPLIER

    def test_baseline_multiplier_is_one(self):
        multipliers = compute_multipliers(
            {"southeast_asia": {"dengue": 0.0}},
        )
        assert multipliers["southeast_asia"]["dengue"] == 1.0

    def test_load_signals_from_jsonl(self, tmp_path):
        """Test loading signals from JSONL archive."""
        archive_dir = tmp_path / "archive"
        archive_dir.mkdir()
        jsonl_path = archive_dir / "2024-08.jsonl"
        records = [
            {"source": "promed", "title": "Dengue - Thailand",
             "date": "2024-08-01", "url": "https://x.com/1",
             "diagnoses": ["dengue"], "regions": ["southeast_asia"],
             "classified": True},
            {"source": "promed", "title": "Conference",
             "date": "2024-08-02", "url": "https://x.com/2",
             "diagnoses": [], "regions": [],
             "classified": False},
        ]
        with open(jsonl_path, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

        loaded = load_signals(archive_dir)
        # Only classified signals should be loaded
        assert len(loaded) == 1
        assert loaded[0]["diagnoses"] == ["dengue"]
