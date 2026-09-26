"""Create a deterministic 1,000-person synthetic adult population sample."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


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
# population_sampling.md. The largest-remainder method is used for any future
# target recalculation; the checked-in values make this sample reproducible.
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


def validate_targets() -> None:
    """Fail early if a hand-edited target table no longer sums to 1,000."""

    if sum(SEX_AGE_TARGETS.values()) != SAMPLE_SIZE:
        raise ValueError("sex x age targets must sum to 1,000")
    for name, targets in (
        ("csp", CSP_TARGETS),
        ("region", REGION_TARGETS),
        ("urban area", URBAN_AREA_TARGETS),
    ):
        if sum(targets.values()) != SAMPLE_SIZE:
            raise ValueError(f"{name} targets must sum to 1,000")


def expanded_values(targets: dict[str, int]) -> list[str]:
    values: list[str] = []
    for label, count in targets.items():
        values.extend([label] * count)
    return values


def assign_balanced(
    rows: list[dict[str, object]],
    field: str,
    targets: dict[str, int],
    rng: random.Random,
) -> None:
    """Assign a marginal distribution to randomised row positions exactly."""

    positions = list(range(len(rows)))
    values = expanded_values(targets)
    rng.shuffle(positions)
    rng.shuffle(values)
    for position, value in zip(positions, values):
        rows[position][field] = value


def build_rows() -> list[dict[str, object]]:
    validate_targets()
    rng = random.Random(SEED)

    rows: list[dict[str, object]] = []
    for (sex, age_group), count in SEX_AGE_TARGETS.items():
        for _ in range(count):
            rows.append({"sex": sex, "age_group": age_group})

    assign_balanced(rows, "csp", CSP_TARGETS, rng)
    assign_balanced(rows, "region", REGION_TARGETS, rng)
    assign_balanced(rows, "urban_area_size", URBAN_AREA_TARGETS, rng)

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
