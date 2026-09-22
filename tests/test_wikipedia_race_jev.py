import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from scripts.wikipedia_race_jev import (
    _choose_next,
    _cache_key,
    _load_cache,
    _path_score,
    _save_cache,
    _split_batches,
    run_search,
)


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.states = []

    def system_one(self, state, questions):
        self.calls += 1
        self.states.append(state)
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

    def test_cache_uses_versioned_payload_and_ignores_legacy_entries(self):
        with TemporaryDirectory() as directory:
            cache_path = Path(directory) / "cache.json"
            cache_path.write_text('{"legacy-key": {"A": 1.0}}')
            self.assertEqual(_load_cache(cache_path), {})

            expected = {"current-key": {"A": 1.0}}
            _save_cache(cache_path, expected)
            self.assertEqual(_load_cache(cache_path), expected)

    def test_cache_key_changes_when_article_context_changes(self):
        state = {
            "starting_article": {"title": "Start", "abstract": "First topic."},
            "landing_article": {"title": "Target", "abstract": "Destination."},
            "current_article": {"title": "Current"},
            "candidate_articles": [{"title": "Candidate"}],
        }
        updated_state = {
            **state,
            "starting_article": {"title": "Start", "abstract": "Updated topic."},
        }

        self.assertNotEqual(_cache_key(state), _cache_key(updated_state))

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
                "Beaver",
                "Apollo 11",
                ["A", "B", "C", "D"],
                "Beavers are semiaquatic rodents.",
                "Apollo 11 was the first crewed mission to land on the Moon.",
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
        self.assertEqual(
            client.states[0]["starting_article"],
            {"title": "Beaver", "abstract": "Beavers are semiaquatic rodents."},
        )
        self.assertEqual(
            client.states[0]["landing_article"],
            {
                "title": "Apollo 11",
                "abstract": "Apollo 11 was the first crewed mission to land on the Moon.",
            },
        )
        self.assertEqual(
            client.states[0]["candidate_articles"], [{"title": "A"}, {"title": "B"}]
        )
        self.assertEqual(
            client.states[1]["starting_article"],
            client.states[0]["starting_article"],
        )

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
            ) as mock_get_links, patch(
                "scripts.wikipedia_race_jev.get_wikipedia_abstract",
                side_effect=["Start abstract", "Target abstract"],
            ) as mock_get_abstract:
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
        self.assertEqual(
            [call.args[0] for call in mock_get_abstract.call_args_list],
            ["Start", "Target"],
        )

        self.assertTrue(result["found"])
        self.assertEqual(result["pages"], ["Start", "Good link", "Target"])


if __name__ == "__main__":
    unittest.main()
