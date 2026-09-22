import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from scripts.wikipedia_race_jev import (
    _choose_next,
    _path_score,
    _split_batches,
    run_search,
)


class FakeClient:
    def __init__(self):
        self.calls = 0

    def system_one(self, state, questions):
        del state
        self.calls += 1
        question = questions["next_article"]
        keys = list(question.criteria)
        probabilities = {
            key: 0.9 if index == 0 else 0.1 / (len(keys) - 1)
            for index, key in enumerate(keys)
        }
        return SimpleNamespace(
            answers={"next_article": SimpleNamespace(probabilities=probabilities)},
            usage=SimpleNamespace(input_tokens=1_000_000, output_tokens=12),
        )


class WikipediaRaceHelpersTests(unittest.TestCase):
    def test_split_batches_respects_batch_size(self):
        self.assertEqual(
            _split_batches(["a", "b", "c", "d", "e"], 2),
            [["a", "b"], ["c", "d"], ["e"]],
        )

    def test_path_score_is_length_normalized(self):
        self.assertAlmostEqual(_path_score(2 * -0.2, 2), _path_score(-0.2, 1))

    def test_multiple_batches_are_reranked_with_a_final_choice(self):
        client = FakeClient()
        stats = {
            "calls": 0,
            "cache_hits": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
        with TemporaryDirectory() as directory:
            result = _choose_next(
                client,
                "Beaver",
                "Apollo 11",
                ["A", "B", "C", "D"],
                batch_size=2,
                per_batch=1,
                beam_width=2,
                cache={},
                cache_path=Path(directory) / "cache.json",
                stats=stats,
                call_budget=10,
            )

        self.assertEqual(client.calls, 3)
        self.assertEqual(stats["calls"], 3)
        self.assertEqual(stats["input_tokens"], 3_000_000)
        self.assertEqual(stats["output_tokens"], 36)
        self.assertAlmostEqual(stats["estimated_cost_usd"], 0.126)
        self.assertEqual([candidate for candidate, _ in result], ["A", "C"])

    def test_missing_linked_article_does_not_abort_search(self):
        client = FakeClient()

        def fake_links(article, limit):
            del limit
            if article == "Start":
                return [
                    "https://en.wikipedia.org/wiki/Missing_link",
                    "https://en.wikipedia.org/wiki/Good_link",
                ]
            if article == "Missing link":
                raise ValueError("Wikipedia article not found: Missing link")
            if article == "Good link":
                return ["https://en.wikipedia.org/wiki/Target"]
            raise AssertionError(f"unexpected article: {article}")

        with TemporaryDirectory() as directory:
            with patch(
                "scripts.wikipedia_race_jev.TypeSafeClient", return_value=client
            ), patch(
                "scripts.wikipedia_race_jev.get_wikipedia_links",
                side_effect=fake_links,
            ) as mock_get_links:
                result = run_search(
                    "Start",
                    "Target",
                    beam_width=2,
                    batch_size=2,
                    max_hops=2,
                    cache_path=Path(directory) / "cache.json",
                    _validated_titles=("Start", "Target"),
                )

        mock_get_links.assert_any_call("Start", limit=None)

        self.assertTrue(result["found"])
        self.assertEqual(result["pages"], ["Start", "Good link", "Target"])


if __name__ == "__main__":
    unittest.main()
