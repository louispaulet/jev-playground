"""Conditional fictional life details and faithful, local biography rendering."""

from __future__ import annotations

import random
from typing import Any


def sample_age(row: dict[str, Any], profile: dict[str, Any], rng: random.Random) -> int:
    low, high = profile["age_ranges"][row["age_group"]]
    context = profile["context"]
    if row["csp"] == context["retired_csp"]:
        low = max(low, context["retirement_min_age"])
    if row["csp"] in context["occupations"]:
        high = min(high, context["occupational_age_max"])
        low = max(
            low,
            min(
                context["occupation_min_ages"].get(job, 18)
                for job in context["occupations"][row["csp"]]
            ),
        )
    if low > high:
        raise ValueError("occupation quota contradicts age restrictions")
    ages = list(range(low, high + 1))
    # Optional INSEE five-year counts start at 15-19 and end in 95+.
    # Uniform within each five-year band; 95+ is represented by age 95.
    counts = profile.get("age_band_counts", {}).get(row["region"], {}).get(row["sex"])
    weights = (
        [counts[(age - 15) // 5] / (1 if age == 95 else 5) for age in ages]
        if counts
        else None
    )
    return rng.choices(ages, weights=weights, k=1)[0]


def choose_weighted(values: dict[str, float], rng: random.Random) -> str:
    return rng.choices(list(values), weights=list(values.values()), k=1)[0]


def enrich_persona(
    row: dict[str, Any], profile: dict[str, Any], rng: random.Random
) -> None:
    context = profile["context"]
    csp = row["csp"]
    if csp == context["retired_csp"]:
        activity = "retired"
        # Previous occupation is an illustrative scenario, not a recovered fact.
        previous = choose_weighted(
            {key: profile["csp_targets"][key] for key in context["occupations"]}, rng
        )
        occupation = rng.choice(context["occupations"][previous])
    elif csp == context["inactive_csp"]:
        activity = (
            choose_weighted(context["inactive_young_weights"], rng)
            if row["age"] <= context["student_max_age"]
            else "inactive"
        )
        occupation = "not_applicable"
    else:
        activity = choose_weighted(context["activity_weights"], rng)
        occupation = rng.choice(
            [
                job
                for job in context["occupations"][csp]
                if row["age"] >= context["occupation_min_ages"].get(job, 18)
            ]
        )
    households = [
        key
        for key, value in context["households"].items()
        if value["min_age"] <= row["age"] <= value["max_age"]
    ]
    household = rng.choice(households)
    row.update(
        {
            "country": profile["country"],
            "population_profile": profile["profile_id"],
            "context_version": context["version"],
            "activity_status": activity,
            "occupation": occupation,
            "household": household,
            "housing": rng.choice(context["households"][household]["housing"]),
            "transport": rng.choice(
                context["settlements"][row["urban_area_size"]]["transport"]
            ),
            "routine": rng.choice(context["activity_routines"][activity]),
            "interest": rng.choice(context["interests"]),
            "tradeoff": rng.choice(context["tradeoffs"]),
        }
    )
    row["bio"] = render_bio(row, profile, rng.randrange(len(context["bio_templates"])))
    validate_persona(row, profile)


def render_bio(
    row: dict[str, Any], profile: dict[str, Any], template_index: int = 0
) -> str:
    context = profile["context"]
    text = context["bio_templates"][template_index].format(
        **row,
        location=context["locations"][row["region"]],
        settlement=context["settlements"][row["urban_area_size"]]["description"],
        household_description=context["households"][row["household"]]["description"],
        activity_description=context["activity_descriptions"][
            row["activity_status"]
        ].format(**row),
    )

    return text[:1].upper() + text[1:]


def validate_persona(row: dict[str, Any], profile: dict[str, Any]) -> None:
    """Enforce scenario coherence independently of marginal validation."""
    context = profile["context"]
    age = int(row["age"])
    if str(age) != str(row["age"]):
        raise ValueError("age must be an integer")
    low, high = profile["age_ranges"][row["age_group"]]
    if not low <= age <= high:
        raise ValueError("age outside age_group")
    if row["sex"] not in profile["sex_age_targets"]:
        raise ValueError("unknown sex")
    for field, key in (
        ("csp", "csp_targets"),
        ("region", "region_targets"),
        ("urban_area_size", "urban_area_targets"),
    ):
        if row[field] not in profile[key]:
            raise ValueError(f"unknown {field}")
    urban_index = list(profile["urban_area_targets"]).index(row["urban_area_size"])
    if profile["region_urban_targets"][row["region"]][urban_index] == 0:
        raise ValueError("urban class impossible in region")
    activity, csp = row["activity_status"], row["csp"]
    if csp == context["retired_csp"]:
        if activity != "retired" or age < context["retirement_min_age"]:
            raise ValueError("incoherent retirement")
        occupations = [job for jobs in context["occupations"].values() for job in jobs]
    elif csp == context["inactive_csp"]:
        if activity not in {"student", "inactive"} or (
            activity == "student" and age > context["student_max_age"]
        ):
            raise ValueError("incoherent inactivity/studies")
        occupations = ["not_applicable"]
    else:
        if activity not in context["activity_weights"]:
            raise ValueError("activity contradicts occupational group")
        if age > context["occupational_age_max"]:
            raise ValueError("occupation contradicts scenario age limit")
        occupations = [
            job
            for job in context["occupations"][csp]
            if age >= context["occupation_min_ages"].get(job, 18)
        ]
    if row["occupation"] not in occupations:
        raise ValueError("occupation contradicts CSP")
    household = context["households"][row["household"]]
    if (
        not household["min_age"] <= age <= household["max_age"]
        or row["housing"] not in household["housing"]
    ):
        raise ValueError("household/housing contradicts scenario rules")
    if (
        row["transport"]
        not in context["settlements"][row["urban_area_size"]]["transport"]
    ):
        raise ValueError("transport contradicts settlement")
    if row["routine"] not in context["activity_routines"][activity]:
        raise ValueError("routine contradicts activity")
    if (
        row["interest"] not in context["interests"]
        or row["tradeoff"] not in context["tradeoffs"]
    ):
        raise ValueError("unknown fictional context")
    if (
        row["country"] != profile["country"]
        or row["population_profile"] != profile["profile_id"]
        or row["context_version"] != context["version"]
    ):
        raise ValueError("profile provenance mismatch")
    if not str(row["bio"]).strip():
        raise ValueError("empty biography")
