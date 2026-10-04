import csv
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from polling_test.polling.poll_population import (
    ask_jev_batch,
    find_cached_result,
    load_personas,
    normalize_answer,
    parse_numbered_options,
    persona_state,
    poll_with_checkpoint,
    result_path,
    slugify_question,
    unique_options,
    validate_answer,
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

    def test_matching_csv_is_reused_as_a_cache(self):
        personas = [{"persona_id": "fr_0001"}]
        responses = [
            {
                "selected_answer": "Option A",
                "confidence": 0.8,
                "probabilities": {"Option A": 0.8, "Option B": 0.2},
            }
        ]
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "20260926T193004123456Z_question.csv"
            write_results(
                output_path,
                personas,
                responses,
                ("Option A", "Option B"),
                question="Question?",
                question_id="question",
            )
            cached = find_cached_result(
                "Question?", ("Option A", "Option B"), personas, Path(directory)
            )
            self.assertEqual(cached, output_path)

    def test_changed_persona_state_does_not_reuse_a_cached_result(self):
        personas = [{"persona_id": "fr_0001", "bio": "Original bio"}]
        responses = [
            {
                "selected_answer": "Option A",
                "confidence": 0.8,
                "probabilities": {"Option A": 0.8, "Option B": 0.2},
            }
        ]
        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "20260926T193004123456Z_question.csv"
            write_results(
                output_path,
                personas,
                responses,
                ("Option A", "Option B"),
                question="Question?",
                question_id="question",
            )
            changed_personas = [{"persona_id": "fr_0001", "bio": "Updated bio"}]
            cached = find_cached_result(
                "Question?",
                ("Option A", "Option B"),
                changed_personas,
                Path(directory),
            )
            self.assertIsNone(cached)

    def test_jev_receives_separate_demographics_and_fiction(self):
        persona = {
            "persona_id": "fr_0001",
            "country": "France",
            "age": "40",
            "bio": "Fiction",
            "interest": "Cinema",
            "context_version": "v2",
            "batch_id": "private job id",
        }
        state = persona_state(persona)
        self.assertEqual(
            state["persona"]["demographics"], {"country": "France", "age": "40"}
        )
        self.assertEqual(
            state["persona"]["fictional_context"],
            {"bio": "Fiction", "interest": "Cinema"},
        )
        self.assertNotIn("private job id", str(state))
        self.assertNotIn("fr_0001", str(state))
        client = Mock()
        answer = SimpleNamespace(
            choice="Yes", confidence=0.6, probabilities={"Yes": 0.6, "No": 0.4}
        )
        client.system_one.return_value = SimpleNamespace(
            choices={"one": answer, "two": answer}
        )
        result = ask_jev_batch(
            client,
            persona,
            [
                {"id": name, "question": "Question?", "options": ("Yes", "No")}
                for name in ("one", "two")
            ],
        )
        client.system_one.assert_called_once()
        self.assertEqual(result["two"]["probabilities"], {"Yes": 0.6, "No": 0.4})

    def test_demographic_baseline_has_a_separate_cache(self):
        full = [{"persona_id": "fr_0001", "age": "40", "bio": "Fiction"}]
        responses = [
            {
                "selected_answer": "Yes",
                "confidence": 0.6,
                "probabilities": {"Yes": 0.6, "No": 0.4},
            }
        ]
        with TemporaryDirectory() as directory:
            output = Path(directory) / "question.csv"
            write_results(output, full, responses, ("Yes", "No"), question="Question?")
            baseline = [{"persona_id": "fr_0001", "age": "40"}]
            self.assertIsNone(
                find_cached_result(
                    "Question?", ("Yes", "No"), baseline, Path(directory)
                )
            )

    def test_duplicate_or_malformed_personas_are_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv"
            for content in (
                "persona_id,age\nfr_1,40\nfr_1,41\n",
                "persona_id,age\n,40\n",
                "persona_id,age\nfr_1,40,unexpected\n",
            ):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    load_personas(path, 0)

    def test_missing_responses_cannot_be_silently_dropped(self):
        with TemporaryDirectory() as directory, self.assertRaises(ValueError):
            write_results(
                Path(directory) / "poll.csv",
                [{"persona_id": "fr_1"}],
                [],
                ("Yes", "No"),
            )

    def test_invalid_distributions_are_rejected(self):
        base = {"selected_answer": "Yes", "confidence": 0.6}
        for probabilities in (
            {"Yes": 0.9},
            {"Yes": 1.1, "No": -0.1},
            {"Yes": 0.2, "No": 0.3},
            {"Yes": float("nan"), "No": 0.4},
        ):
            with self.assertRaises(ValueError):
                validate_answer({**base, "probabilities": probabilities}, ("Yes", "No"))

    def test_rounded_service_probabilities_are_normalized_with_raw_sum(self):
        response = {
            "selected_answer": "A",
            "confidence": 0.4,
            "probabilities": {"A": 0.33, "B": 0.33, "C": 0.33},
        }
        normalized = normalize_answer(response, ("A", "B", "C"))
        self.assertAlmostEqual(normalized["raw_probability_sum"], 0.99)
        self.assertAlmostEqual(sum(normalized["probabilities"].values()), 1)
        self.assertEqual(response["probabilities"]["A"], 0.33)
        with self.assertRaises(ValueError):
            normalize_answer(
                {**response, "probabilities": {"A": 0.1, "B": 0.1, "C": 0.1}},
                ("A", "B", "C"),
            )

    def test_failed_poll_resumes_without_repolling_completed_personas(self):
        personas = [{"persona_id": "fr_1"}, {"persona_id": "fr_2"}]
        specs = [{"id": "q", "question": "Question?", "options": ("A", "B", "C")}]
        response = {
            "q": {
                "selected_answer": "A",
                "confidence": 0.4,
                "probabilities": {"A": 0.33, "B": 0.33, "C": 0.33},
            }
        }
        with TemporaryDirectory() as directory:
            with (
                patch(
                    "polling_test.polling.poll_population.ask_jev_batch",
                    side_effect=[response, RuntimeError("network interruption")],
                ),
                self.assertRaises(RuntimeError),
            ):
                poll_with_checkpoint(None, personas, specs, Path(directory))
            with patch(
                "polling_test.polling.poll_population.ask_jev_batch",
                return_value=response,
            ) as ask:
                results = poll_with_checkpoint(None, personas, specs, Path(directory))
                self.assertEqual(ask.call_count, 1)
                self.assertEqual(ask.call_args.args[1]["persona_id"], "fr_2")
                self.assertEqual(len(results["q"]), 2)
            checkpoint = next(Path(directory).glob("checkpoint_*.jsonl"))
            self.assertEqual(len(checkpoint.read_text().splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
