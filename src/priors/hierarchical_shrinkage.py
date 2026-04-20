"""Empirical Bayes hierarchical shrinkage for destination-diagnosis priors.

Pools extreme per-region priors toward a global mean across regions,
with shrinkage strength inversely proportional to the effective information
content of each cell. This stabilises estimates for sparse region-diagnosis
combinations while preserving well-supported estimates.

Method:
    For each diagnosis d:
        global_mean_d = mean across regions of P(d | region)
        For each region r:
            shrunk_P(d | r) = w_r * P_raw(d | r) + (1 - w_r) * global_mean_d

    where w_r is a confidence weight based on how far the region's diagnosis
    distribution is from the floor (proxy for information content).

    Region groups (e.g., SE Asia + Oceania) share additional pooling for
    geographically coherent diseases.

Usage:
    python -m src.priors.hierarchical_shrinkage
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml

from src.priors.build_base_priors import DIAGNOSES, REGIONS
from src.utils import PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)

# Region groups for partial pooling of geographically related destinations
REGION_GROUPS = {
    "tropical_asia_pacific": ["southeast_asia", "south_central_asia", "oceania"],
    "africa_mena": ["sub_saharan_africa", "north_africa_middle_east"],
    "americas": ["latin_america_caribbean", "north_america"],
    "europe_temperate": ["europe", "northeast_asia"],
}

# Shrinkage hyperparameter: controls baseline pooling strength
# Higher = more shrinkage toward global mean
# 0.3 gives moderate shrinkage — well-supported cells retain ~70%+ of raw value
SHRINKAGE_STRENGTH = 0.3

# Floor value — cells at or near floor have minimal information
FLOOR = 1e-4


def load_raw_priors(path: Path) -> dict[str, dict[str, float]]:
    """Load raw destination priors (region -> diagnosis -> probability)."""
    with open(path) as f:
        raw = yaml.safe_load(f)
    return raw["priors"]


def compute_information_weight(
    prior_value: float,
    floor: float = FLOOR,
    max_weight: float = 0.95,
) -> float:
    """Compute confidence weight for a prior cell.

    Cells near the floor have low information (weight → 0, more shrinkage).
    Cells with substantial prior values retain their estimate (weight → max).

    Uses a logistic-like mapping from prior magnitude to weight.
    """
    if prior_value <= floor * 2:
        return 0.05  # Near-floor: heavy shrinkage
    # Log-scale ratio above floor, mapped to [0.05, max_weight]
    ratio = np.log10(prior_value / floor)
    # ratio ~ 0 at floor, ~ 3-4 for dominant diagnoses
    weight = min(max_weight, 0.05 + (max_weight - 0.05) * (1 - np.exp(-ratio)))
    return float(weight)


def apply_hierarchical_shrinkage(
    raw_priors: dict[str, dict[str, float]],
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, dict[str, float]]]]:
    """Apply two-level hierarchical shrinkage.

    Level 1: Shrink toward global mean across all regions.
    Level 2: Shrink toward region-group mean for geographically coherent groups.

    Returns:
        (shrunk_priors, diagnostics) where diagnostics contains per-cell
        shrinkage weights and credible interval proxies.
    """
    shrunk: dict[str, dict[str, float]] = {r: {} for r in REGIONS}
    diagnostics: dict[str, dict[str, dict[str, float]]] = {r: {} for r in REGIONS}

    for dx in DIAGNOSES:
        # --- Level 1: Global shrinkage ---
        raw_values = [raw_priors[r].get(dx, FLOOR) for r in REGIONS]
        global_mean = float(np.mean(raw_values))

        # --- Level 2: Region-group means ---
        group_means: dict[str, float] = {}
        for group_name, group_regions in REGION_GROUPS.items():
            group_vals = [raw_priors[r].get(dx, FLOOR) for r in group_regions]
            group_means[group_name] = float(np.mean(group_vals))

        # Find which group each region belongs to
        region_to_group: dict[str, str] = {}
        for group_name, group_regions in REGION_GROUPS.items():
            for r in group_regions:
                region_to_group[r] = group_name

        for r in REGIONS:
            raw_val = raw_priors[r].get(dx, FLOOR)
            w = compute_information_weight(raw_val)

            # Two-level shrinkage target:
            # Blend region-group mean (70%) and global mean (30%)
            group = region_to_group.get(r)
            if group:
                shrink_target = 0.7 * group_means[group] + 0.3 * global_mean
            else:
                shrink_target = global_mean

            # Apply shrinkage
            shrunk_val = w * raw_val + (1 - w) * shrink_target

            # Credible interval proxy: wider for more-shrunk cells
            # This is a rough approximation, not a true Bayesian CrI
            ci_half_width = (1 - w) * max(raw_val, shrink_target) * 1.96
            ci_lower = max(FLOOR, shrunk_val - ci_half_width)
            ci_upper = shrunk_val + ci_half_width

            shrunk[r][dx] = shrunk_val
            diagnostics[r][dx] = {
                "raw": raw_val,
                "shrunk": shrunk_val,
                "weight": w,
                "shrinkage_pct": (1 - w) * 100,
                "ci_lower_95": ci_lower,
                "ci_upper_95": ci_upper,
                "shrink_target": shrink_target,
            }

    # Re-normalise per region
    for r in REGIONS:
        total = sum(shrunk[r][dx] for dx in DIAGNOSES)
        if total > 0:
            for dx in DIAGNOSES:
                shrunk[r][dx] /= total

    return shrunk, diagnostics


def save_shrunk_priors(
    shrunk: dict[str, dict[str, float]],
    diagnostics: dict[str, dict[str, dict[str, float]]],
    output_path: Path,
    diagnostics_path: Path,
) -> None:
    """Save shrunk priors and diagnostics to YAML."""
    # Round for readability
    output = {}
    for r in REGIONS:
        output[r] = {dx: round(v, 6) for dx, v in shrunk[r].items()}

    metadata = {
        "metadata": {
            "description": "Hierarchically shrunk P(diagnosis | region) priors",
            "method": "Two-level empirical Bayes: global mean + region-group mean",
            "shrinkage_strength": SHRINKAGE_STRENGTH,
            "region_groups": {k: v for k, v in REGION_GROUPS.items()},
            "input": "destination_priors.yaml (raw GeoSentinel + NNDSS reweighted)",
            "generated_by": "src/priors/hierarchical_shrinkage.py",
        },
    }

    with open(output_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        f.write("\n")
        yaml.dump({"priors": output}, f, default_flow_style=False, sort_keys=False)

    # Save diagnostics (shrinkage details per cell)
    diag_output = {}
    for r in REGIONS:
        diag_output[r] = {}
        for dx in DIAGNOSES:
            d = diagnostics[r][dx]
            diag_output[r][dx] = {
                "raw": round(d["raw"], 6),
                "shrunk": round(d["shrunk"], 6),
                "weight": round(d["weight"], 3),
                "shrinkage_pct": round(d["shrinkage_pct"], 1),
                "ci_95": [round(d["ci_lower_95"], 6), round(d["ci_upper_95"], 6)],
            }

    with open(diagnostics_path, "w") as f:
        yaml.dump(
            {"shrinkage_diagnostics": diag_output},
            f,
            default_flow_style=False,
            sort_keys=False,
        )

    logger.info("Saved shrunk priors to %s", output_path)
    logger.info("Saved shrinkage diagnostics to %s", diagnostics_path)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_dirs()

    raw_path = PROCESSED_DIR / "destination_priors.yaml"
    if not raw_path.exists():
        print("Run build_base_priors.py first")
        return

    raw_priors = load_raw_priors(raw_path)
    shrunk, diagnostics = apply_hierarchical_shrinkage(raw_priors)

    output_path = PROCESSED_DIR / "destination_priors_shrunk.yaml"
    diag_path = PROCESSED_DIR / "shrinkage_diagnostics.yaml"
    save_shrunk_priors(shrunk, diagnostics, output_path, diag_path)

    print(f"Shrunk priors saved to {output_path}")
    print(f"Diagnostics saved to {diag_path}")

    # Show cells with heaviest shrinkage (most changed)
    print("\n--- Top-10 most-shrunk cells ---")
    cells = []
    for r in REGIONS:
        for dx in DIAGNOSES:
            d = diagnostics[r][dx]
            if d["raw"] > FLOOR * 2:  # Skip floor-level cells
                change = abs(d["shrunk"] - d["raw"]) / max(d["raw"], 1e-6)
                cells.append((r, dx, d["raw"], d["shrunk"], d["shrinkage_pct"], change))
    cells.sort(key=lambda x: x[5], reverse=True)
    for r, dx, raw, shrunk_v, pct, change in cells[:10]:
        print(f"  {r:30s} {dx:35s} {raw:.4f} → {shrunk_v:.4f} ({pct:.0f}% shrinkage)")

    # Verify normalisation
    for r in REGIONS:
        total = sum(shrunk[r][dx] for dx in DIAGNOSES)
        assert abs(total - 1.0) < 1e-6, f"{r} sums to {total}"
    print("\nNormalisation check passed")


if __name__ == "__main__":
    main()
