import io
import json
import unittest
from unittest.mock import patch

from scripts.get_wikipedia_links import (
    article_title,
    get_wikipedia_links,
    validate_article_titles,
    wikipedia_url,
)


def api_response(payload):
    response = io.BytesIO(json.dumps(payload).encode())
    response.__enter__ = lambda: response
    response.__exit__ = lambda *args: None
    return response


class WikipediaLinksTests(unittest.TestCase):
    def test_article_title_accepts_name_and_url(self):
        self.assertEqual(article_title("Apollo_11"), "Apollo 11")
        self.assertEqual(
            article_title("https://en.wikipedia.org/wiki/Apollo_11"),
            "Apollo 11",
        )
        self.assertEqual(
            article_title("https://en.wikipedia.org/w/index.php?title=Apollo_11"),
            "Apollo 11",
        )

    def test_wikipedia_url_encodes_title(self):
        self.assertEqual(
            wikipedia_url("Apollo 11"),
            "https://en.wikipedia.org/wiki/Apollo_11",
        )

    @patch("scripts.get_wikipedia_links.urlopen")
    def test_get_wikipedia_links_filters_self_visited_and_duplicates(self, mock_urlopen):
        payload = {
            "query": {
                "pages": [
                    {
                        "pageid": 1,
                        "title": "Beaver",
                        "links": [
                            {"title": "Beaver"},
                            {"title": "Canada"},
                            {"title": "Canada"},
                            {"title": "North America"},
                            {"title": "Science"},
                        ],
                    }
                ]
            }
        }
        mock_urlopen.return_value = api_response(payload)

        self.assertEqual(
            get_wikipedia_links(
                "Beaver",
                limit=2,
                visited=["https://en.wikipedia.org/wiki/Canada"],
            ),
            [
                "https://en.wikipedia.org/wiki/North_America",
                "https://en.wikipedia.org/wiki/Science",
            ],
        )
        request = mock_urlopen.call_args.args[0]
        self.assertIn("pllimit=500", request.full_url)
        self.assertIn("plnamespace=0", request.full_url)

    @patch("scripts.get_wikipedia_links.urlopen")
    def test_validate_article_titles_returns_canonical_titles(self, mock_urlopen):
        mock_urlopen.side_effect = [
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
            api_response({"query": {"pages": [{"title": "Apollo 13"}]}}),
        ]

        self.assertEqual(
            validate_article_titles("Camembert", "Apollo 13"),
            ("Camembert", "Apollo 13"),
        )

    @patch("scripts.get_wikipedia_links.urlopen")
    def test_validate_article_titles_suggests_missing_titles(self, mock_urlopen):
        mock_urlopen.side_effect = [
            api_response({"query": {"pages": [{"title": "Camenbert", "missing": True}]}}),
            api_response(
                {
                    "query": {
                        "searchinfo": {"suggestion": "Camembert"},
                        "search": [{"title": "Camembert"}, {"title": "Cheese"}],
                    }
                }
            ),
            api_response({"query": {"pages": [{"title": "Apollo 13", "missing": True}]}}),
            api_response(
                {
                    "query": {
                        "search": [{"title": "Apollo program"}],
                    }
                }
            ),
        ]

        with self.assertRaisesRegex(ValueError, "Start Wikipedia article not found: Camenbert") as context:
            validate_article_titles("Camenbert", "Apollo 13")

        message = str(context.exception)
        self.assertIn("- Camembert", message)
        self.assertIn("Target Wikipedia article not found: Apollo 13", message)
        self.assertIn("- Apollo program", message)
        self.assertIn("Copy a suggested title and rerun the command.", message)


if __name__ == "__main__":
    unittest.main()
