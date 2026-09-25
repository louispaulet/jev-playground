import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from gender_guesser.detector import Detector

from scripts.benchmark_gender import (
    CHOICES,
    BenchmarkResult,
    _metrics,
    build_sample,
    write_csv,
    write_html,
)


class GenderBenchmarkTests(unittest.TestCase):
    def test_sample_is_balanced_and_reproducible(self):
        detector = Detector(case_sensitive=False)
        first = build_sample(detector, sample_size=100, unisex_count=4, seed=42)
        second = build_sample(detector, sample_size=100, unisex_count=4, seed=42)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 100)
        self.assertEqual([case.index for case in first], list(range(1, 101)))
        labels = [
            {"male", "mostly_male"} & {case.library_gender}
            for case in first
        ]
        self.assertEqual(sum(bool(label) for label in labels), 48)
        self.assertEqual(sum(case.library_gender == "andy" for case in first), 4)

    def test_metrics_and_artifacts_are_written(self):
        results = [
            BenchmarkResult(1, "Alex", "andy", "unisex", "unisex", 0.1, 0.1, 0.8, 0.8, True),
            BenchmarkResult(2, "James", "male", "male", "female", 0.2, 0.7, 0.1, 0.7, False),
        ]
        metrics = _metrics(results)
        self.assertEqual(metrics["accuracy_percent"], 50.0)
        self.assertEqual(metrics["expected_counts"], {"unisex": 1, "male": 1})
        self.assertEqual(set(metrics["prediction_counts"]), {"unisex", "female"})

        with TemporaryDirectory() as directory:
            csv_path = Path(directory) / "results.csv"
            html_path = Path(directory) / "report.html"
            write_csv(csv_path, results)
            write_html(
                html_path,
                results,
                seed=42,
                unisex_count=1,
                concurrency=2,
                elapsed_seconds=1.25,
            )
            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["name"], "Alex")
            document = html_path.read_text(encoding="utf-8")
            self.assertIn("JEV gender Choice benchmark", document)
            self.assertIn("Alex", document)
            self.assertIn("gender_benchmark_results.csv", document)


if __name__ == "__main__":
    unittest.main()
