import io
import json
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from urllib.error import HTTPError
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

    @patch("scripts.get_wikipedia_links.random.shuffle", side_effect=lambda items: None)
    @patch("scripts.get_wikipedia_links.urlopen")
    def test_get_wikipedia_links_filters_self_visited_and_duplicates(
        self, mock_urlopen, mock_shuffle
    ):
        del mock_shuffle
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

    @patch("scripts.get_wikipedia_links.random.shuffle", side_effect=lambda items: items.reverse())
    @patch("scripts.get_wikipedia_links.urlopen")
    def test_get_wikipedia_links_shuffles_after_following_continuation(
        self, mock_urlopen, mock_shuffle
    ):
        del mock_shuffle
        mock_urlopen.side_effect = [
            api_response(
                {
                    "query": {
                        "pages": [{"title": "Beaver", "links": [{"title": "Alpha"}]}]
                    },
                    "continue": {"continue": "-||", "plcontinue": "next"},
                }
            ),
            api_response(
                {
                    "query": {
                        "pages": [
                            {
                                "title": "Beaver",
                                "links": [{"title": "Beta"}, {"title": "Gamma"}],
                            }
                        ]
                    }
                }
            ),
        ]

        self.assertEqual(
            get_wikipedia_links("Beaver", limit=2),
            [
                "https://en.wikipedia.org/wiki/Gamma",
                "https://en.wikipedia.org/wiki/Beta",
            ],
        )
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("scripts.get_wikipedia_links.random.shuffle", side_effect=lambda items: None)
    @patch("scripts.get_wikipedia_links.urlopen")
    def test_get_wikipedia_links_can_return_all_links(
        self, mock_urlopen, mock_shuffle
    ):
        del mock_shuffle
        titles = [f"Page {index}" for index in range(501)]
        mock_urlopen.return_value = api_response(
            {
                "query": {
                    "pages": [
                        {
                            "title": "Beaver",
                            "links": [{"title": title} for title in titles],
                        }
                    ]
                }
            }
        )

        links = get_wikipedia_links("Beaver", limit=None)

        self.assertEqual(len(links), 501)
        self.assertEqual(
            links,
            [wikipedia_url(title) for title in titles],
        )

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

    @patch("scripts.get_wikipedia_links.time.sleep")
    @patch("scripts.get_wikipedia_links.urlopen")
    def test_api_retries_rate_limit_and_honors_retry_after(
        self, mock_urlopen, mock_sleep
    ):
        rate_limit = HTTPError(
            "https://en.wikipedia.org/w/api.php",
            429,
            "Too Many Requests",
            {"Retry-After": "3"},
            io.BytesIO(),
        )
        mock_urlopen.side_effect = [
            rate_limit,
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
        ]

        self.assertEqual(
            validate_article_titles("Camembert", "Camembert"),
            ("Camembert", "Camembert"),
        )
        mock_sleep.assert_called_once_with(3.0)
        rate_limit.close()

    @patch("scripts.get_wikipedia_links.time.sleep")
    @patch("scripts.get_wikipedia_links.urlopen")
    def test_api_does_not_cap_retry_after(
        self, mock_urlopen, mock_sleep
    ):
        rate_limit = HTTPError(
            "https://en.wikipedia.org/w/api.php",
            429,
            "Too Many Requests",
            {"Retry-After": "90"},
            io.BytesIO(),
        )
        mock_urlopen.side_effect = [
            rate_limit,
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
        ]

        self.assertEqual(
            validate_article_titles("Camembert", "Camembert"),
            ("Camembert", "Camembert"),
        )
        mock_sleep.assert_called_once_with(90.0)
        rate_limit.close()

    @patch("scripts.get_wikipedia_links.time.sleep")
    @patch("scripts.get_wikipedia_links.urlopen")
    @patch("scripts.get_wikipedia_links.datetime")
    def test_api_honors_http_date_retry_after(
        self, mock_datetime, mock_urlopen, mock_sleep
    ):
        now = datetime(2030, 1, 1, tzinfo=timezone.utc)
        mock_datetime.now.return_value = now
        rate_limit = HTTPError(
            "https://en.wikipedia.org/w/api.php",
            429,
            "Too Many Requests",
            {"Retry-After": format_datetime(now + timedelta(seconds=45), usegmt=True)},
            io.BytesIO(),
        )
        mock_urlopen.side_effect = [
            rate_limit,
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
            api_response({"query": {"pages": [{"title": "Camembert"}]}}),
        ]

        self.assertEqual(
            validate_article_titles("Camembert", "Camembert"),
            ("Camembert", "Camembert"),
        )
        mock_sleep.assert_called_once_with(45.0)
        rate_limit.close()


if __name__ == "__main__":
    unittest.main()
