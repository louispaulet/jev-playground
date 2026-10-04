"""Load population controls independently of the sampling and prose code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_PROFILE = Path(__file__).with_name("profiles") / "france.json"
DEMOGRAPHIC_FIELDS = [
    "persona_id",
    "sex",
    "age",
    "age_group",
    "csp",
    "region",
    "urban_area_size",
]
CONTEXT_FIELDS = [
    "activity_status",
    "occupation",
    "household",
    "housing",
    "transport",
    "routine",
    "interest",
    "tradeoff",
]
FIELDNAMES = DEMOGRAPHIC_FIELDS + [
    "country",
    "population_profile",
    "context_version",
    *CONTEXT_FIELDS,
    "bio",
]


def load_profile(path: Path = DEFAULT_PROFILE) -> dict[str, Any]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    validate_profile(profile)
    return profile


def validate_profile(profile: dict[str, Any]) -> None:
    """Check both axes of every control before asking the integer solver."""
    size = profile["reference_size"]
    if not isinstance(size, int) or size < 1:
        raise ValueError("reference_size must be a positive integer")
    ages = list(profile["age_ranges"])
    totals = {}
    for name in ("csp", "region", "urban_area"):
        values = list(profile[f"{name}_targets"].values())
        if any(not isinstance(v, int) or v < 0 for v in values) or sum(values) != size:
            raise ValueError(f"invalid {name} targets")
        totals[name] = values
    age_totals = np.zeros(len(ages), dtype=int)
    for targets in profile["sex_age_targets"].values():
        if list(targets) != ages or any(
            not isinstance(v, int) or v < 0 for v in targets.values()
        ):
            raise ValueError("invalid sex x age targets")
        age_totals += list(targets.values())
    if sum(age_totals) != size:
        raise ValueError("sex x age targets must sum to reference_size")
    totals["age"] = age_totals
    axes = {"age": ages, "region": list(profile["region_targets"])}
    for left, right in (
        ("age", "csp"),
        ("age", "region"),
        ("region", "csp"),
        ("region", "urban"),
    ):
        table = profile[f"{left}_{right}_targets"]
        right_name = "urban_area" if right == "urban" else right
        array = np.asarray(list(table.values()))
        if list(table) != axes[left] or array.shape != (
            len(totals[left]),
            len(totals[right_name]),
        ):
            raise ValueError(f"invalid {left} x {right} dimensions/order")
        if not np.issubdtype(array.dtype, np.integer) or (array < 0).any():
            raise ValueError(f"invalid {left} x {right} counts")
        if not np.array_equal(array.sum(axis=1), totals[left]) or not np.array_equal(
            array.sum(axis=0), totals[right_name]
        ):
            raise ValueError(f"{left} x {right} targets do not balance")
    for group, (low, high) in profile["age_ranges"].items():
        if (
            not isinstance(low, int)
            or not isinstance(high, int)
            or low > high
            or low < 18
        ):
            raise ValueError(f"invalid adult age range: {group}")

    context = profile["context"]
    occupational_csps = set(profile["csp_targets"]) - {
        context["retired_csp"],
        context["inactive_csp"],
    }
    if set(context["occupations"]) != occupational_csps or any(
        not jobs for jobs in context["occupations"].values()
    ):
        raise ValueError("occupation catalog must cover the occupational CSPs")
    if set(context["settlements"]) != set(profile["urban_area_targets"]) or set(
        context["locations"]
    ) != set(profile["region_targets"]):
        raise ValueError("context must cover all settlements and regions")
    for key in ("activity_weights", "inactive_young_weights"):
        weights = list(context[key].values())
        if (
            not weights
            or any(
                not isinstance(v, (int, float)) or not np.isfinite(v) or v < 0
                for v in weights
            )
            or sum(weights) <= 0
        ):
            raise ValueError(f"invalid context weights: {key}")
    for region, by_sex in profile.get("age_band_counts", {}).items():
        if region not in profile["region_targets"]:
            raise ValueError("age detail references an unknown region")
        for sex, counts in by_sex.items():
            if (
                sex not in profile["sex_age_targets"]
                or len(counts) != 17
                or any(not isinstance(v, int) or v < 0 for v in counts)
            ):
                raise ValueError(
                    "age_band_counts needs 17 nonnegative five-year counts per sex"
                )
    if (
        profile.get("age_band_counts")
        and max(high for low, high in profile["age_ranges"].values()) > 95
    ):
        raise ValueError("five-year age detail represents 95+ by age 95")
