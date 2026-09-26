"""Validate the synthetic population CSV against its documented quotas."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:
    from .create_population_sample import (
        AGE_RANGES,
        AGE_GROUPS,
        AGE_CSP_TARGETS,
        AGE_REGION_TARGETS,
        CSP_TARGETS,
        FIELDNAMES,
        REGION_CSP_TARGETS,
        REGION_TARGETS,
        REGION_URBAN_TARGETS,
        SEX_AGE_TARGETS,
        URBAN_AREA_TARGETS,
    )
except ImportError:  # Allows direct execution: python population/validate_population_sample.py
    from create_population_sample import (
        AGE_RANGES,
        AGE_GROUPS,
        AGE_CSP_TARGETS,
        AGE_REGION_TARGETS,
        CSP_TARGETS,
        FIELDNAMES,
        REGION_CSP_TARGETS,
        REGION_TARGETS,
        REGION_URBAN_TARGETS,
        SEX_AGE_TARGETS,
        URBAN_AREA_TARGETS,
    )


def assert_counts(actual: pd.Series, expected: dict[str, int], label: str) -> None:
    observed = actual.to_dict()
    if observed != expected:
        raise AssertionError(f"{label} mismatch: expected {expected}, observed {observed}")


def validate(csv_path: Path) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    if list(frame.columns[: len(FIELDNAMES)]) != FIELDNAMES:
        raise AssertionError(
            f"columns mismatch: expected {FIELDNAMES} first, observed {list(frame.columns)}"
        )
    unexpected_columns = set(frame.columns) - set(FIELDNAMES) - {"bio"}
    if unexpected_columns:
        raise AssertionError(f"unexpected columns: {sorted(unexpected_columns)}")
    if len(frame) != 1_000:
        raise AssertionError(f"expected 1,000 rows, observed {len(frame)}")
    if frame.isna().any().any():
        raise AssertionError("CSV contains missing values")
    if "bio" in frame.columns and frame["bio"].str.strip().eq("").any():
        raise AssertionError("CSV contains empty bios")
    if frame["persona_id"].nunique() != len(frame):
        raise AssertionError("persona_id values are not unique")

    if not frame["age"].between(18, 95).all():
        raise AssertionError("ages must be between 18 and 95")
    for age_group, (low, high) in AGE_RANGES.items():
        ages = frame.loc[frame["age_group"] == age_group, "age"]
        if not ages.between(low, high).all():
            raise AssertionError(f"age values outside the {age_group} band")

    cross_tab = frame.groupby(["sex", "age_group"]).size().to_dict()
    if cross_tab != SEX_AGE_TARGETS:
        raise AssertionError(
            f"sex x age_group mismatch: expected {SEX_AGE_TARGETS}, observed {cross_tab}"
        )
    age_csp = (
        frame.groupby(["age_group", "csp"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=AGE_GROUPS, columns=CSP_TARGETS, fill_value=0)
    )
    expected_age_csp = pd.DataFrame.from_dict(AGE_CSP_TARGETS, orient="index", columns=CSP_TARGETS)
    if not age_csp.equals(expected_age_csp):
        raise AssertionError("age x csp mismatch")

    region_csp = (
        frame.groupby(["region", "csp"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=REGION_TARGETS, columns=CSP_TARGETS, fill_value=0)
    )
    expected_region_csp = pd.DataFrame.from_dict(
        REGION_CSP_TARGETS, orient="index", columns=CSP_TARGETS
    )
    if not region_csp.equals(expected_region_csp):
        raise AssertionError("region x csp mismatch")

    age_region = (
        frame.groupby(["age_group", "region"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=AGE_GROUPS, columns=REGION_TARGETS, fill_value=0)
    )
    expected_age_region = pd.DataFrame.from_dict(
        AGE_REGION_TARGETS, orient="index", columns=REGION_TARGETS
    )
    if not age_region.equals(expected_age_region):
        raise AssertionError("age x region mismatch")

    region_urban = (
        frame.groupby(["region", "urban_area_size"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=REGION_TARGETS, columns=URBAN_AREA_TARGETS, fill_value=0)
    )
    expected_region_urban = pd.DataFrame.from_dict(
        REGION_URBAN_TARGETS, orient="index", columns=URBAN_AREA_TARGETS
    )
    if not region_urban.equals(expected_region_urban):
        raise AssertionError("region x urban_area_size mismatch")

    assert_counts(frame["csp"].value_counts().reindex(CSP_TARGETS, fill_value=0), CSP_TARGETS, "csp")
    assert_counts(
        frame["region"].value_counts().reindex(REGION_TARGETS, fill_value=0),
        REGION_TARGETS,
        "region",
    )
    assert_counts(
        frame["urban_area_size"].value_counts().reindex(URBAN_AREA_TARGETS, fill_value=0),
        URBAN_AREA_TARGETS,
        "urban_area_size",
    )

    unexpected_age_groups = set(frame["age_group"]) - set(AGE_GROUPS)
    if unexpected_age_groups:
        raise AssertionError(f"unexpected age groups: {unexpected_age_groups}")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("population_sample.csv"),
        help="CSV path to validate",
    )
    args = parser.parse_args()
    frame = validate(args.csv_path)
    print(f"PASS: {len(frame)} rows match all documented population quotas")


if __name__ == "__main__":
    main()
