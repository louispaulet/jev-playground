"""Build reproducible, quota-controlled personas with explicit fictional context."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

try:
    from .personas import enrich_persona, sample_age
    from .population_profile import (
        DEFAULT_PROFILE,
        FIELDNAMES,
        load_profile,
        validate_profile,
    )
except ImportError:  # Direct script execution.
    from personas import enrich_persona, sample_age
    from population_profile import (
        DEFAULT_PROFILE,
        FIELDNAMES,
        load_profile,
        validate_profile,
    )

SAMPLE_SIZE = 1_000
SEED = 20250926


def apportion(weights: list[float], size: int) -> list[int]:
    """Largest remainder allocation; zero-weight cells always stay empty."""
    if size < 0 or not weights or any(w < 0 or not np.isfinite(w) for w in weights):
        raise ValueError("invalid allocation inputs")
    if size == 0:
        return [0] * len(weights)
    total = sum(weights)
    if total <= 0:
        raise ValueError("positive allocation requires positive weights")
    expected = [w * size / total for w in weights]
    counts = [int(v) for v in expected]
    order = sorted(range(len(weights)), key=lambda i: (-(expected[i] - counts[i]), i))
    for index in order[: size - sum(counts)]:
        counts[index] += 1
    return counts


def solve_joint_csp_counts(profile: dict[str, Any] | None = None) -> np.ndarray:
    """Fit integer age x region x CSP cells to all published pairwise controls."""
    profile = profile or load_profile()
    validate_profile(profile)
    ages = list(profile["age_ranges"])
    regions = list(profile["region_targets"])
    shape = (len(ages), len(regions), len(profile["csp_targets"]))
    cells = int(np.prod(shape))
    indices = np.arange(cells).reshape(shape)
    rows, targets = [], []
    for table, axes in (
        ("age_csp_targets", (0, 2)),
        ("region_csp_targets", (1, 2)),
        ("age_region_targets", (0, 1)),
    ):
        values = np.asarray(list(profile[table].values()))
        for left in range(shape[axes[0]]):
            for right in range(shape[axes[1]]):
                selection = [slice(None)] * 3
                selection[axes[0]], selection[axes[1]] = left, right
                row = np.zeros(3 * cells)
                row[indices[tuple(selection)].ravel()] = 1
                rows.append(row)
                targets.append(values[left, right])
    # Conditional-independence starting point within each CSP, rather than
    # pretending age and occupation are independent nationally.
    age_csp = np.asarray(list(profile["age_csp_targets"].values()))
    region_csp = np.asarray(list(profile["region_csp_targets"].values()))
    csp = np.asarray(list(profile["csp_targets"].values()))
    expected = (
        age_csp[:, None, :] * region_csp[None, :, :] / np.maximum(csp, 1)
    ).ravel()
    deviations = np.concatenate((np.eye(cells), -np.eye(cells), np.eye(cells)), axis=1)
    matrix = np.vstack([*rows, deviations])
    bounds = np.concatenate((targets, expected))
    result = milp(
        np.concatenate((np.zeros(cells), np.ones(2 * cells))),
        integrality=np.concatenate((np.ones(cells), np.zeros(2 * cells))),
        bounds=Bounds(0, np.inf),
        constraints=LinearConstraint(matrix, bounds, bounds),
        options={"time_limit": 60},
    )
    if not result.success:
        raise RuntimeError(f"could not fit population controls: {result.message}")
    return np.rint(result.x[:cells]).astype(int).reshape(shape)


def build_rows(
    size: int = SAMPLE_SIZE, seed: int = SEED, profile: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    profile = profile or load_profile()
    rng = random.Random(seed)
    ages, regions, csps = (
        list(profile[key]) for key in ("age_ranges", "region_targets", "csp_targets")
    )
    sexes = list(profile["sex_age_targets"])
    joint = solve_joint_csp_counts(profile)
    age_sizes = apportion(joint.sum(axis=(1, 2)).tolist(), size)
    rows = []
    for age_index, group in enumerate(ages):
        counts = apportion(joint[age_index].ravel().tolist(), age_sizes[age_index])
        assignments = [
            {
                "age_group": group,
                "region": regions[i // len(csps)],
                "csp": csps[i % len(csps)],
            }
            for i, count in enumerate(counts)
            for _ in range(count)
        ]
        sex_counts = apportion(
            [profile["sex_age_targets"][sex][group] for sex in sexes], len(assignments)
        )
        sex_values = [
            sex for sex, count in zip(sexes, sex_counts) for _ in range(count)
        ]
        rng.shuffle(sex_values)
        for row, sex in zip(assignments, sex_values):
            row["sex"] = sex
        rows.extend(assignments)
    for region in regions:
        positions = [row for row in rows if row["region"] == region]
        counts = apportion(profile["region_urban_targets"][region], len(positions))
        urban_values = [
            urban
            for urban, count in zip(profile["urban_area_targets"], counts)
            for _ in range(count)
        ]
        rng.shuffle(urban_values)
        for row, urban in zip(positions, urban_values):
            row["urban_area_size"] = urban
    rng.shuffle(rows)
    for index, row in enumerate(rows, 1):
        row["persona_id"] = f"{profile['id_prefix']}_{index:04d}"
        row["age"] = sample_age(row, profile, rng)
        # Separate random streams: rewriting a bio cannot change demographics.
        context_rng = random.Random(
            f"{seed}:{profile['profile_id']}:{row['persona_id']}:context-v2"
        )
        enrich_persona(row, profile, context_rng)
    return rows


def write_csv(
    output_path: Path,
    size: int = SAMPLE_SIZE,
    seed: int = SEED,
    profile_path: Path = DEFAULT_PROFILE,
) -> None:
    profile = load_profile(profile_path)
    rows = build_rows(size, seed, profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "profile": profile,
        "size": size,
        "seed": seed,
        "schema_version": 2,
        "context_provenance": "Fictional conditional scenarios; not calibrated to census or opinion data.",
        "allocation": "Exact pairwise quotas at reference_size; largest-remainder scaling of fitted cells otherwise.",
    }
    output_path.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).with_name("population_sample.csv")
    )
    parser.add_argument("--size", type=int, default=SAMPLE_SIZE)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    args = parser.parse_args()
    write_csv(args.output, args.size, args.seed, args.profile)
    print(f"Wrote {args.size} personas and provenance manifest to {args.output}")


if __name__ == "__main__":
    main()
