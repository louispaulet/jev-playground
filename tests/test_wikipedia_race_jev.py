import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from scripts.wikipedia_race_jev import _choose_next, _path_score, _split_batches


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
            answers={"next_article": SimpleNamespace(probabilities=probabilities)}
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
        stats = {"calls": 0, "cache_hits": 0}
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
        self.assertEqual([candidate for candidate, _ in result], ["A", "C"])


if __name__ == "__main__":
    unittest.main()
