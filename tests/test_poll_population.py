import csv
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from polling_test.polling.poll_population import (
    parse_numbered_options,
    result_path,
    slugify_question,
    unique_options,
    write_results,
)


class PollPopulationTests(unittest.TestCase):
    def test_numbered_options_are_extracted_and_duplicates_removed(self):
        question = """Q3. Question ?
1. Option A
2) Option B
3. Option A
"""
        self.assertEqual(parse_numbered_options(question), ("Option A", "Option B"))

    def test_explicit_options_are_trimmed_and_deduplicated(self):
        self.assertEqual(
            unique_options(("Option A", " Option B ", "Option A", "")),
            ("Option A", "Option B"),
        )

    def test_result_path_is_timestamped_and_slugged(self):
        question = "Élection présidentielle : pour qui voteriez-vous ?"
        path = result_path(
            question,
            Path("results"),
            datetime(2026, 9, 26, 19, 30, 4, 123456, tzinfo=timezone.utc),
        )
        self.assertEqual(
            path.name,
            "20260926T193004123456Z_election-presidentielle-pour-qui-voteriez-vous.csv",
        )
        self.assertLessEqual(len(slugify_question("a" * 500)), 200)

    def test_results_keep_persona_key_and_probability_columns(self):
        personas = [{"persona_id": "fr_0001"}]
        responses = [
            {
                "selected_answer": "Option A",
                "confidence": 0.8,
                "probabilities": {"Option A": 0.8, "Option B": 0.2},
            }
        ]
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "poll.csv"
            write_results(output_path, personas, responses, ("Option A", "Option B"))
            with output_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(rows[0]["persona_id"], "fr_0001")
            self.assertEqual(rows[0]["selected_answer"], "Option A")
            self.assertEqual(rows[0]["probability_option-a"], "0.8")
            self.assertEqual(rows[0]["probability_option-b"], "0.2")


if __name__ == "__main__":
    unittest.main()
