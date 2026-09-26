"""Create a deterministic 1,000-person synthetic adult population sample."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


SAMPLE_SIZE = 1_000
SEED = 20250926

FIELDNAMES = [
    "persona_id",
    "sex",
    "age",
    "age_group",
    "csp",
    "region",
    "urban_area_size",
]

AGE_GROUPS = ("18-24", "25-34", "35-49", "50-64", "65+")
AGE_RANGES = {
    "18-24": (18, 24),
    "25-34": (25, 34),
    "35-49": (35, 49),
    "50-64": (50, 64),
    "65+": (65, 95),
}

# Targets are integer allocations from the reference distributions described in
# population_sampling.md. The checked-in values make this sample reproducible.
SEX_AGE_TARGETS = {
    ("male", "18-24"): 53,
    ("male", "25-34"): 72,
    ("male", "35-49"): 115,
    ("male", "50-64"): 119,
    ("male", "65+"): 119,
    ("female", "18-24"): 51,
    ("female", "25-34"): 73,
    ("female", "35-49"): 120,
    ("female", "50-64"): 124,
    ("female", "65+"): 154,
}

CSP_TARGETS = {
    "farmer": 7,
    "craft_trader_business_owner": 36,
    "manager_intellectual_profession": 107,
    "intermediate_profession": 144,
    "employee": 153,
    "worker": 116,
    "retired": 278,
    "other_inactive": 159,
}

REGION_TARGETS = {
    "Auvergne-Rhône-Alpes": 120,
    "Bourgogne-Franche-Comté": 41,
    "Bretagne": 52,
    "Centre-Val de Loire": 38,
    "Corse": 6,
    "Grand Est": 82,
    "Hauts-de-France": 86,
    "Île-de-France": 179,
    "Normandie": 49,
    "Nouvelle-Aquitaine": 93,
    "Occitanie": 92,
    "Pays de la Loire": 57,
    "Provence-Alpes-Côte d'Azur": 78,
    "Guadeloupe": 6,
    "Martinique": 5,
    "Guyane": 4,
    "La Réunion": 12,
}

URBAN_AREA_TARGETS = {
    "rural_outside_urban_unit": 208,
    "urban_unit_under_20k": 180,
    "urban_unit_20k_to_99k": 141,
    "urban_unit_100k_to_1_999_999": 309,
    "paris_urban_unit": 162,
}

# Pairwise targets are derived from the INSEE RP2022 tables documented in
# population_sampling.md. They preserve the one-way margins above while
# enforcing realistic conditional distributions at this sample size.
AGE_CSP_TARGETS = {
    "18-24": [0, 1, 4, 12, 19, 14, 0, 54],
    "25-34": [1, 5, 25, 35, 34, 26, 0, 19],
    "35-49": [2, 15, 43, 57, 53, 41, 0, 24],
    "50-64": [3, 14, 33, 40, 46, 34, 43, 30],
    "65+": [1, 1, 2, 0, 1, 1, 235, 32],
}

REGION_CSP_TARGETS = {
    "Auvergne-Rhône-Alpes": [1, 5, 13, 18, 18, 14, 33, 18],
    "Bourgogne-Franche-Comté": [1, 1, 3, 5, 6, 6, 13, 6],
    "Bretagne": [1, 2, 5, 7, 7, 6, 17, 7],
    "Centre-Val de Loire": [0, 1, 3, 6, 6, 5, 12, 5],
    "Corse": [0, 0, 0, 1, 1, 1, 2, 1],
    "Grand Est": [1, 2, 6, 12, 13, 12, 23, 13],
    "Hauts-de-France": [0, 2, 7, 12, 14, 12, 23, 16],
    "Île-de-France": [0, 6, 36, 28, 28, 14, 35, 32],
    "Normandie": [0, 2, 4, 7, 7, 7, 15, 7],
    "Nouvelle-Aquitaine": [1, 4, 8, 12, 14, 11, 31, 12],
    "Occitanie": [1, 4, 8, 13, 14, 9, 28, 15],
    "Pays de la Loire": [1, 2, 5, 8, 8, 8, 18, 7],
    "Provence-Alpes-Côte d'Azur": [0, 4, 8, 11, 12, 7, 23, 13],
    "Guadeloupe": [0, 0, 0, 1, 1, 1, 2, 1],
    "Martinique": [0, 0, 0, 1, 1, 1, 1, 1],
    "Guyane": [0, 0, 0, 0, 1, 1, 0, 2],
    "La Réunion": [0, 1, 1, 2, 2, 1, 2, 3],
}

REGION_URBAN_TARGETS = {
    "Auvergne-Rhône-Alpes": [26, 20, 22, 52, 0],
    "Bourgogne-Franche-Comté": [18, 8, 8, 7, 0],
    "Bretagne": [15, 17, 10, 10, 0],
    "Centre-Val de Loire": [13, 9, 7, 9, 0],
    "Corse": [2, 1, 3, 0, 0],
    "Grand Est": [23, 18, 15, 26, 0],
    "Hauts-de-France": [18, 14, 14, 40, 0],
    "Île-de-France": [6, 8, 3, 0, 162],
    "Normandie": [17, 11, 7, 14, 0],
    "Nouvelle-Aquitaine": [30, 19, 13, 31, 0],
    "Occitanie": [22, 23, 17, 30, 0],
    "Pays de la Loire": [13, 17, 7, 20, 0],
    "Provence-Alpes-Côte d'Azur": [4, 11, 8, 55, 0],
    "Guadeloupe": [0, 1, 1, 4, 0],
    "Martinique": [0, 1, 1, 3, 0],
    "Guyane": [1, 1, 1, 1, 0],
    "La Réunion": [0, 1, 4, 7, 0],
}

AGE_REGION_TARGETS = {
    "18-24": [13, 4, 5, 4, 1, 8, 9, 18, 5, 10, 10, 6, 8, 1, 1, 0, 1],
    "25-34": [17, 6, 8, 6, 1, 12, 12, 26, 7, 13, 13, 8, 11, 1, 1, 1, 2],
    "35-49": [28, 10, 12, 9, 1, 19, 20, 42, 12, 22, 22, 13, 19, 1, 1, 1, 3],
    "50-64": [29, 10, 13, 9, 1, 20, 21, 44, 12, 23, 22, 14, 19, 1, 1, 1, 3],
    "65+": [33, 11, 14, 10, 2, 23, 24, 49, 13, 25, 25, 16, 21, 2, 1, 1, 3],
}


def validate_targets() -> None:
    """Fail early if a hand-edited target table no longer balances."""

    if sum(SEX_AGE_TARGETS.values()) != SAMPLE_SIZE:
        raise ValueError("sex x age targets must sum to 1,000")
    for name, targets in (
        ("csp", CSP_TARGETS),
        ("region", REGION_TARGETS),
        ("urban area", URBAN_AREA_TARGETS),
    ):
        if sum(targets.values()) != SAMPLE_SIZE:
            raise ValueError(f"{name} targets must sum to 1,000")

    age_totals = [
        sum(count for (sex, group), count in SEX_AGE_TARGETS.items() if group == age_group)
        for age_group in AGE_GROUPS
    ]
    if [sum(AGE_CSP_TARGETS[group]) for group in AGE_GROUPS] != age_totals:
        raise ValueError("age x csp targets must match age-group totals")
    if [sum(AGE_REGION_TARGETS[group]) for group in AGE_GROUPS] != age_totals:
        raise ValueError("age x region targets must match age-group totals")
    if [sum(REGION_CSP_TARGETS[region]) for region in REGION_TARGETS] != list(
        REGION_TARGETS.values()
    ):
        raise ValueError("region x csp targets must match region totals")
    if [sum(REGION_URBAN_TARGETS[region]) for region in REGION_TARGETS] != list(
        REGION_TARGETS.values()
    ):
        raise ValueError("region x urban targets must match region totals")
    if [
        sum(AGE_CSP_TARGETS[group][index] for group in AGE_GROUPS)
        for index in range(len(CSP_TARGETS))
    ] != list(CSP_TARGETS.values()):
        raise ValueError("age x csp targets must match national CSP totals")
    if [
        sum(REGION_CSP_TARGETS[region][index] for region in REGION_TARGETS)
        for index in range(len(CSP_TARGETS))
    ] != list(CSP_TARGETS.values()):
        raise ValueError("region x csp targets must match national CSP totals")
    if [
        sum(REGION_URBAN_TARGETS[region][index] for region in REGION_TARGETS)
        for index in range(len(URBAN_AREA_TARGETS))
    ] != list(URBAN_AREA_TARGETS.values()):
        raise ValueError("region x urban targets must match national urban totals")


def solve_joint_csp_counts() -> np.ndarray:
    """Find integer age x region x CSP cells with all pairwise targets exact."""

    age_count = len(AGE_GROUPS)
    region_names = list(REGION_TARGETS)
    csp_count = len(CSP_TARGETS)
    region_count = len(region_names)
    cell_count = age_count * region_count * csp_count
    variable_count = cell_count * 3

    def cell_index(age_index: int, region_index: int, csp_index: int) -> int:
        return (age_index * region_count + region_index) * csp_count + csp_index

    constraints: list[np.ndarray] = []
    lower: list[float] = []
    upper: list[float] = []

    def add_exact(indices: list[int], value: int) -> None:
        row = np.zeros(variable_count)
        row[indices] = 1
        constraints.append(row)
        lower.append(value)
        upper.append(value)

    age_totals = [
        sum(count for (sex, group), count in SEX_AGE_TARGETS.items() if group == age_group)
        for age_group in AGE_GROUPS
    ]
    for age_index, total in enumerate(age_totals):
        add_exact(
            [
                cell_index(age_index, region_index, csp_index)
                for region_index in range(region_count)
                for csp_index in range(csp_count)
            ],
            total,
        )
    for region_index, region in enumerate(region_names):
        add_exact(
            [
                cell_index(age_index, region_index, csp_index)
                for age_index in range(age_count)
                for csp_index in range(csp_count)
            ],
            REGION_TARGETS[region],
        )
    for age_index, age_group in enumerate(AGE_GROUPS):
        for csp_index in range(csp_count):
            add_exact(
                [
                    cell_index(age_index, region_index, csp_index)
                    for region_index in range(region_count)
                ],
                AGE_CSP_TARGETS[age_group][csp_index],
            )
    for region_index, region in enumerate(region_names):
        for csp_index in range(csp_count):
            add_exact(
                [
                    cell_index(age_index, region_index, csp_index)
                    for age_index in range(age_count)
                ],
                REGION_CSP_TARGETS[region][csp_index],
            )

    for age_index, age_group in enumerate(AGE_GROUPS):
        for region_index in range(region_count):
            add_exact(
                [
                    cell_index(age_index, region_index, csp_index)
                    for csp_index in range(csp_count)
                ],
                AGE_REGION_TARGETS[age_group][region_index],
            )

    age_region = np.array([AGE_REGION_TARGETS[group] for group in AGE_GROUPS])
    csp_totals = np.array(list(CSP_TARGETS.values()))
    expected = np.zeros(cell_count)
    for age_index in range(age_count):
        for region_index in range(region_count):
            for csp_index in range(csp_count):
                expected[cell_index(age_index, region_index, csp_index)] = (
                    age_region[age_index, region_index]
                    * csp_totals[csp_index]
                    / SAMPLE_SIZE
                )

    for index, value in enumerate(expected):
        row = np.zeros(variable_count)
        row[index] = 1
        row[cell_count + index] = -1
        row[2 * cell_count + index] = 1
        constraints.append(row)
        lower.append(value)
        upper.append(value)

    objective = np.zeros(variable_count)
    objective[cell_count:] = 1
    integrality = np.zeros(variable_count)
    integrality[:cell_count] = 1
    result = milp(
        objective,
        integrality=integrality,
        bounds=Bounds(np.zeros(variable_count), np.full(variable_count, np.inf)),
        constraints=LinearConstraint(np.array(constraints), lower, upper),
        options={"time_limit": 60},
    )
    if not result.success:
        raise RuntimeError(f"could not solve joint population allocation: {result.message}")
    return np.rint(result.x[:cell_count]).astype(int).reshape(
        age_count, region_count, csp_count
    )


def build_rows() -> list[dict[str, object]]:
    validate_targets()
    rng = random.Random(SEED)

    rows: list[dict[str, object]] = []
    for (sex, age_group), count in SEX_AGE_TARGETS.items():
        for _ in range(count):
            rows.append({"sex": sex, "age_group": age_group})

    joint_counts = solve_joint_csp_counts()
    region_names = list(REGION_TARGETS)
    csp_names = list(CSP_TARGETS)
    for age_index, age_group in enumerate(AGE_GROUPS):
        age_positions = [
            index for index, row in enumerate(rows) if row["age_group"] == age_group
        ]
        assignments: list[tuple[str, str]] = []
        for region_index, region in enumerate(region_names):
            for csp_index, csp in enumerate(csp_names):
                assignments.extend(
                    [(region, csp)] * joint_counts[age_index, region_index, csp_index]
                )
        rng.shuffle(age_positions)
        rng.shuffle(assignments)
        for position, (region, csp) in zip(age_positions, assignments):
            rows[position]["region"] = region
            rows[position]["csp"] = csp

    for region, targets in REGION_URBAN_TARGETS.items():
        positions = [index for index, row in enumerate(rows) if row["region"] == region]
        values: list[str] = []
        for urban_area_size, count in zip(URBAN_AREA_TARGETS, targets):
            values.extend([urban_area_size] * count)
        rng.shuffle(positions)
        rng.shuffle(values)
        for position, value in zip(positions, values):
            rows[position]["urban_area_size"] = value

    for row in rows:
        low, high = AGE_RANGES[row["age_group"]]
        row["age"] = rng.randint(low, high)

    rng.shuffle(rows)
    for index, row in enumerate(rows, start=1):
        row["persona_id"] = f"fr_{index:04d}"

    return rows


def write_csv(output_path: Path) -> None:
    rows = build_rows()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("population_sample.csv"),
        help="destination CSV path",
    )
    args = parser.parse_args()
    write_csv(args.output)
    print(f"Wrote {SAMPLE_SIZE} personas to {args.output}")


if __name__ == "__main__":
    main()
