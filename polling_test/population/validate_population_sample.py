"""Validate demographic controls and conditional fictional persona consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .create_population_sample import SAMPLE_SIZE, apportion, solve_joint_csp_counts
    from .personas import validate_persona
    from .population_profile import FIELDNAMES, load_profile, validate_profile
except ImportError:
    from create_population_sample import SAMPLE_SIZE, apportion, solve_joint_csp_counts
    from personas import validate_persona
    from population_profile import FIELDNAMES, load_profile, validate_profile


def validate(
    csv_path: Path, profile_path: Path | None = None, size: int | None = None
) -> pd.DataFrame:
    manifest_path = csv_path.with_suffix(".manifest.json")
    manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else {}
    )
    profile = (
        load_profile(profile_path)
        if profile_path
        else manifest.get("profile") or load_profile()
    )
    validate_profile(profile)
    expected_size = size if size is not None else manifest.get("size", SAMPLE_SIZE)
    frame = pd.read_csv(csv_path, keep_default_na=False)
    if list(frame.columns) != FIELDNAMES:
        raise ValueError(f"expected CSV columns {FIELDNAMES}")
    if len(frame) != expected_size or expected_size < 1:
        raise ValueError(f"expected {expected_size} rows, observed {len(frame)}")
    if frame.astype(str).apply(lambda col: col.str.strip().eq("")).any().any():
        raise ValueError("CSV contains empty fields")
    if frame["persona_id"].nunique() != len(frame):
        raise ValueError("persona_id values are not unique")
    for row in frame.to_dict("records"):
        try:
            validate_persona(row, profile)
        except (ValueError, KeyError) as error:
            raise ValueError(f"{row['persona_id']}: {error}") from error

    ages, regions, csps = (
        list(profile[key]) for key in ("age_ranges", "region_targets", "csp_targets")
    )
    joint = solve_joint_csp_counts(profile)
    age_sizes = apportion(joint.sum(axis=(1, 2)).tolist(), expected_size)
    scaled = np.asarray(
        [
            np.asarray(apportion(joint[i].ravel().tolist(), count)).reshape(
                joint.shape[1:]
            )
            for i, count in enumerate(age_sizes)
        ]
    )

    def check(columns: list[str], expected: dict[tuple[str, ...], int]) -> None:
        actual = frame.groupby(columns).size().to_dict()
        expected = {key: value for key, value in expected.items() if value}
        if actual != expected:
            raise ValueError(f"{' x '.join(columns)} allocation mismatch")

    sexes = list(profile["sex_age_targets"])
    check(
        ["sex", "age_group"],
        {
            (sex, group): count
            for group, total in zip(ages, age_sizes)
            for sex, count in zip(
                sexes,
                apportion([profile["sex_age_targets"][s][group] for s in sexes], total),
            )
        },
    )
    for columns, names, counts in (
        (["age_group", "csp"], (ages, csps), scaled.sum(axis=1)),
        (["region", "csp"], (regions, csps), scaled.sum(axis=0)),
        (["age_group", "region"], (ages, regions), scaled.sum(axis=2)),
    ):
        check(
            columns,
            {
                (a, b): int(counts[i, j])
                for i, a in enumerate(names[0])
                for j, b in enumerate(names[1])
            },
        )
    region_totals = scaled.sum(axis=(0, 2))
    check(
        ["region", "urban_area_size"],
        {
            (region, urban): count
            for region, total in zip(regions, region_totals)
            for urban, count in zip(
                profile["urban_area_targets"],
                apportion(profile["region_urban_targets"][region], int(total)),
            )
        },
    )
    # Quantify rounding against the source profile, rather than calling scaled
    # or fictional distributions statistically representative.
    deviations = []
    for field, targets in (
        ("csp", profile["csp_targets"]),
        ("region", profile["region_targets"]),
        ("urban_area_size", profile["urban_area_targets"]),
    ):
        for label, reference in targets.items():
            observed = int(frame[field].eq(label).sum())
            deviations.append(
                {
                    "field": field,
                    "value": label,
                    "observed": observed,
                    "target": reference * expected_size / profile["reference_size"],
                    "delta_pp": 100
                    * (
                        observed / expected_size - reference / profile["reference_size"]
                    ),
                }
            )
    frame.attrs["margin_deviations"] = deviations
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("population_sample.csv"),
    )
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--size", type=int)
    parser.add_argument(
        "--report",
        type=Path,
        help="write rounding deviations against the reference margins",
    )
    args = parser.parse_args()
    frame = validate(args.csv_path, args.profile, args.size)
    report = pd.DataFrame(frame.attrs["margin_deviations"])
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        report.to_csv(args.report, index=False)
    print(
        f"PASS: {len(frame)} coherent personas; max one-way reference deviation {report.delta_pp.abs().max():.3f} pp"
    )


if __name__ == "__main__":
    main()
