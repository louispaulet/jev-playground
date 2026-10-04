"""Prevent historical experiment data from being joined to new personas."""

import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from polling_test.polling.calibrate_weights import solve_weights
from polling_test.polling.compare_benchmarks import find_result, load_weights
from polling_test.polling.poll_population import make_population_hash, write_results


class BenchmarkTests(unittest.TestCase):
    def test_new_population_cannot_use_old_poll_with_identical_ids(self):
        old = [{"persona_id": "fr_1", "bio": "Old biography"}]
        new = [{"persona_id": "fr_1", "bio": "New biography"}]
        answers = [
            {
                "selected_answer": "Yes",
                "confidence": 0.9,
                "probabilities": {"Yes": 0.9, "No": 0.1},
            }
        ]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "question.csv"
            write_results(path, old, answers, ("Yes", "No"), question="Question?")
            self.assertEqual(
                find_result(Path(directory), "Question?", ("Yes", "No"), old), path
            )
            with self.assertRaises(FileNotFoundError):
                find_result(Path(directory), "Question?", ("Yes", "No"), new)

    def test_weights_must_match_population_and_order(self):
        personas = [{"persona_id": "fr_1", "bio": "Current"}]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "weights.csv"
            with path.open("w", newline="") as target:
                writer = csv.DictWriter(
                    target, fieldnames=["persona_id", "weight", "population_sha256"]
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "persona_id": "fr_1",
                        "weight": 1,
                        "population_sha256": make_population_hash(personas),
                    }
                )
            self.assertEqual(load_weights(path, personas), {"fr_1": 1.0})
            with self.assertRaises(ValueError):
                load_weights(path, [{"persona_id": "fr_1", "bio": "Changed"}])

    def test_calibration_still_solves_a_known_feasible_target(self):
        probabilities = np.array([[0.1], [0.9]])
        result = solve_weights(probabilities, np.array([0.6]), 0.2, 2.0, hard=True)
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.x.sum(), 2)
        self.assertAlmostEqual((probabilities.T @ result.x / 2).item(), 0.6)


if __name__ == "__main__":
    unittest.main()
