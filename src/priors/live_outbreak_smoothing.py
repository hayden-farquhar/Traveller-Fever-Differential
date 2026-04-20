"""Exponential smoothing of live outbreak signals into prior multipliers.

Reads classified signals from ProMED and WHO DON JSONL archives,
computes exponentially-smoothed signal intensity per (region, diagnosis),
and outputs prior multipliers capped at 3x.

Pre-registered hyperparameters:
    alpha = 0.3 (smoothing constant)
    max_multiplier = 3.0 (cap on prior upweight)

Usage:
    python -m src.priors.live_outbreak_smoothing
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml

from src.priors.build_base_priors import DIAGNOSES, REGIONS
from src.utils import PROCESSED_DIR, RAW_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Pre-registered hyperparameters
ALPHA = 0.3          # Exponential smoothing constant
MAX_MULTIPLIER = 3.0  # Cap on prior upweight
LOOKBACK_MONTHS = 6   # Number of months of archive to consider


def load_signals(archive_dir: Path) -> list[dict]:
    """Load all classified signals from JSONL archive directory."""
    signals = []
    if not archive_dir.exists():
        return signals

    for jsonl_file in sorted(archive_dir.glob("*.jsonl")):
        with open(jsonl_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("classified", False):
                        signals.append(record)
                except json.JSONDecodeError:
                    continue

    return signals


def count_signals_by_month(
    signals: list[dict],
) -> dict[str, dict[str, dict[str, int]]]:
    """Count classified signals per (month, region, diagnosis).

    Returns: {month_key: {region: {diagnosis: count}}}
    """
    counts: dict[str, dict[str, dict[str, int]]] = {}

    for signal in signals:
        date_str = signal.get("date", "")
        if not date_str:
            continue

        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            month_key = dt.strftime("%Y-%m")
        except ValueError:
            continue

        if month_key not in counts:
            counts[month_key] = {r: {dx: 0 for dx in DIAGNOSES} for r in REGIONS}

        for region in signal.get("regions", []):
            if region not in REGIONS:
                continue
            for dx in signal.get("diagnoses", []):
                if dx not in DIAGNOSES:
                    continue
                counts[month_key][region][dx] += 1

    return counts


def exponential_smoothing(
    monthly_counts: dict[str, dict[str, dict[str, int]]],
    alpha: float = ALPHA,
    lookback_months: int = LOOKBACK_MONTHS,
) -> dict[str, dict[str, float]]:
    """Apply exponential smoothing to monthly signal counts.

    For each (region, diagnosis), computes an exponentially-weighted
    moving average of monthly signal counts, then converts to a
    z-score-like multiplier.

    Returns: {region: {diagnosis: smoothed_value}}
    """
    # Sort months chronologically
    sorted_months = sorted(monthly_counts.keys())

    # Limit to recent months
    if len(sorted_months) > lookback_months:
        sorted_months = sorted_months[-lookback_months:]

    # Initialise smoothed values
    smoothed: dict[str, dict[str, float]] = {
        r: {dx: 0.0 for dx in DIAGNOSES} for r in REGIONS
    }

    if not sorted_months:
        return smoothed

    # Apply exponential smoothing: S_t = alpha * x_t + (1-alpha) * S_{t-1}
    for region in REGIONS:
        for dx in DIAGNOSES:
            s = 0.0
            for month in sorted_months:
                count = monthly_counts.get(month, {}).get(region, {}).get(dx, 0)
                s = alpha * count + (1 - alpha) * s
            smoothed[region][dx] = s

    return smoothed


def compute_multipliers(
    smoothed: dict[str, dict[str, float]],
    max_multiplier: float = MAX_MULTIPLIER,
) -> dict[str, dict[str, float]]:
    """Convert smoothed signal counts to prior multipliers.

    Multiplier = 1.0 + smoothed_value (bounded to [1.0, max_multiplier])

    A smoothed value of 0 → multiplier 1.0 (no change).
    Higher smoothed values → proportionally higher multipliers, capped.
    """
    multipliers: dict[str, dict[str, float]] = {}

    for region in REGIONS:
        multipliers[region] = {}
        region_data = smoothed.get(region, {})
        for dx in DIAGNOSES:
            s = region_data.get(dx, 0.0)
            # Convert to multiplier: 1 + s, capped
            mult = min(1.0 + s, max_multiplier)
            multipliers[region][dx] = round(mult, 4)

    return multipliers


def save_multipliers(
    multipliers: dict[str, dict[str, float]],
    smoothed: dict[str, dict[str, float]],
    output_path: Path,
) -> None:
    """Save live prior multipliers to YAML."""
    metadata = {
        "metadata": {
            "description": "Live outbreak prior multipliers from ProMED + WHO DON signals",
            "method": f"Exponential smoothing (alpha={ALPHA}), cap at {MAX_MULTIPLIER}x",
            "lookback_months": LOOKBACK_MONTHS,
            "sources": ["ProMED-mail RSS", "WHO Disease Outbreak News"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "src/priors/live_outbreak_smoothing.py",
        },
    }

    output = {"multipliers": multipliers}

    with open(output_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        f.write("\n")
        yaml.dump(output, f, default_flow_style=False, sort_keys=False)

    logger.info("Saved live multipliers to %s", output_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    # Load signals from both archives
    promed_signals = load_signals(RAW_DIR / "promed_archive")
    who_signals = load_signals(RAW_DIR / "who_don_archive")
    all_signals = promed_signals + who_signals

    logger.info("Loaded %d classified signals (%d ProMED, %d WHO DON)",
                len(all_signals), len(promed_signals), len(who_signals))

    if not all_signals:
        logger.info("No signals found. Creating baseline multipliers (all 1.0)")
        multipliers = {r: {dx: 1.0 for dx in DIAGNOSES} for r in REGIONS}
        smoothed = {r: {dx: 0.0 for dx in DIAGNOSES} for r in REGIONS}
    else:
        monthly_counts = count_signals_by_month(all_signals)
        logger.info("Signal months: %s", sorted(monthly_counts.keys()))

        smoothed = exponential_smoothing(monthly_counts)
        multipliers = compute_multipliers(smoothed)

    output_path = PROCESSED_DIR / "live_prior_multipliers.yaml"
    save_multipliers(multipliers, smoothed, output_path)

    # Summary: show elevated multipliers
    elevated = []
    for region in REGIONS:
        for dx in DIAGNOSES:
            m = multipliers[region][dx]
            if m > 1.05:  # >5% elevation
                elevated.append((region, dx, m, smoothed[region][dx]))

    print(f"\nLive outbreak smoothing complete:")
    print(f"  Total classified signals: {len(all_signals)}")
    print(f"  Output: {output_path}")

    if elevated:
        elevated.sort(key=lambda x: x[2], reverse=True)
        print(f"\n  Elevated multipliers ({len(elevated)} cells):")
        for region, dx, mult, smooth in elevated[:15]:
            print(f"    {region:30s} {dx:35s} ×{mult:.2f} (smoothed={smooth:.2f})")
    else:
        print("  No elevated multipliers (baseline — no outbreak signals)")


if __name__ == "__main__":
    main()
