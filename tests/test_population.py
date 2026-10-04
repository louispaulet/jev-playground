"""Offline regressions for quotas, scenario coherence, and population portability."""

import copy
import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from polling_test.population.create_population_sample import (
    apportion,
    build_rows,
    write_csv,
)
from polling_test.population.personas import render_bio, validate_persona
from polling_test.population.population_profile import load_profile, validate_profile
from polling_test.population.validate_population_sample import validate


class PopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_profile()
        cls.rows = build_rows()

    def test_default_matches_all_reference_quotas_and_has_unique_bios(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "population.csv"
            write_csv(path)
            frame = validate(path)
            self.assertEqual(len(frame), 1000)
            self.assertEqual(frame.bio.nunique(), 1000)
            self.assertTrue(
                all(item["delta_pp"] == 0 for item in frame.attrs["margin_deviations"])
            )
            self.assertTrue(path.with_suffix(".manifest.json").exists())

    def test_seed_reproduces_population_and_changes_scenarios(self):
        self.assertEqual(self.rows, build_rows())
        different = build_rows(seed=91)
        self.assertNotEqual(self.rows, different)
        for rows in (self.rows, different):
            self.assertEqual(sum(row["csp"] == "retired" for row in rows), 278)

    def test_nonreference_sizes_preserve_structural_zeros_and_validate(self):
        with TemporaryDirectory() as directory:
            for size in (1, 37, 1250, 2000):
                path = Path(directory) / f"population_{size}.csv"
                write_csv(path, size=size)
                frame = validate(path)
                self.assertEqual(len(frame), size)
                self.assertTrue(
                    frame.loc[frame.urban_area_size.eq("paris_urban_unit"), "region"]
                    .eq("Île-de-France")
                    .all()
                )

    def test_country_and_prose_are_profile_data(self):
        profile = copy.deepcopy(self.profile)
        profile.update(
            country="Example country", profile_id="example_v1", id_prefix="xx"
        )
        profile["context"]["bio_templates"] = [
            "Aged {age}; lives in {region}; activity {activity_status}; likes {interest}."
        ]
        rows = build_rows(size=12, profile=profile)
        self.assertTrue(
            all(
                row["country"] == "Example country"
                and row["persona_id"].startswith("xx_")
                for row in rows
            )
        )
        self.assertTrue(all(row["bio"].startswith("Aged ") for row in rows))

    def test_impossible_retirement_and_occupation_are_rejected(self):
        retired = next(row for row in self.rows if row["csp"] == "retired")
        for updates in (
            {"activity_status": "working"},
            {"age": 55, "age_group": "50-64"},
            {"occupation": "invented job"},
        ):
            with self.assertRaises(ValueError):
                validate_persona({**retired, **updates}, self.profile)

    def test_incompatible_household_and_transport_are_rejected(self):
        old = next(row for row in self.rows if row["age"] >= 65)
        with self.assertRaises(ValueError):
            validate_persona(
                {**old, "household": "parents", "housing": "le logement familial"},
                self.profile,
            )
        rural = next(
            row
            for row in self.rows
            if row["urban_area_size"] == "rural_outside_urban_unit"
        )
        with self.assertRaises(ValueError):
            validate_persona(
                {**rural, "transport": "les transports en commun"}, self.profile
            )

    def test_validator_detects_population_corruption(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "population.csv"
            write_csv(path)
            with path.open(newline="", encoding="utf-8") as source:
                reader = csv.DictReader(source)
                fields, rows = reader.fieldnames, list(reader)
            rows[0]["persona_id"] = rows[1]["persona_id"]
            with path.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(target, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaisesRegex(ValueError, "not unique"):
                validate(path)

    def test_profile_rejects_unbalanced_column_and_unknown_order(self):
        profile = copy.deepcopy(self.profile)
        profile["age_region_targets"]["18-24"][0] += 1
        profile["age_region_targets"]["18-24"][1] -= 1
        with self.assertRaisesRegex(ValueError, "do not balance"):
            validate_profile(profile)

    def test_apportionment_preserves_zeros_and_total(self):
        self.assertEqual(apportion([0, 1, 1], 5), [0, 3, 2])
        self.assertEqual(apportion([0, 0], 0), [0, 0])
        for weights, size in (([0, 0], 1), ([1, -1], 2), ([1], -1)):
            with self.assertRaises(ValueError):
                apportion(weights, size)

    def test_bio_uses_only_scenario_values(self):
        row = self.rows[0]
        text = render_bio(row, self.profile)
        for field in (
            "age",
            "region",
            "housing",
            "transport",
            "routine",
            "interest",
            "tradeoff",
        ):
            self.assertIn(str(row[field]), text)

    def test_prose_changes_do_not_resample_demographics(self):
        profile = copy.deepcopy(self.profile)
        profile["context"]["bio_templates"] = ["Age {age}; home {region}."]
        changed = build_rows(profile=profile)
        for before, after in zip(self.rows, changed):
            for field in (
                "persona_id",
                "sex",
                "age",
                "age_group",
                "csp",
                "region",
                "urban_area_size",
            ):
                self.assertEqual(before[field], after[field])

    def test_professions_requiring_training_respect_age(self):
        for row in self.rows:
            if row["activity_status"] in {"working", "job_seeking"}:
                minimum = self.profile["context"]["occupation_min_ages"].get(
                    row["occupation"], 18
                )
                self.assertGreaterEqual(row["age"], minimum)
                self.assertLessEqual(row["age"], 79)


if __name__ == "__main__":
    unittest.main()
