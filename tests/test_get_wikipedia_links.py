import io
import json
import unittest
from unittest.mock import patch

from scripts.get_wikipedia_links import article_title, get_wikipedia_links, wikipedia_url


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
    def test_get_wikipedia_links_returns_main_namespace_urls(self, mock_urlopen):
        payload = {
            "query": {
                "pages": [
                    {
                        "pageid": 1,
                        "title": "Beaver",
                        "links": [
                            {"title": "Canada"},
                            {"title": "North America"},
                        ],
                    }
                ]
            }
        }
        response = io.BytesIO(json.dumps(payload).encode())
        response.__enter__ = lambda: response
        response.__exit__ = lambda *args: None
        mock_urlopen.return_value = response

        self.assertEqual(
            get_wikipedia_links("Beaver"),
            [
                "https://en.wikipedia.org/wiki/Canada",
                "https://en.wikipedia.org/wiki/North_America",
            ],
        )
        request = mock_urlopen.call_args.args[0]
        self.assertIn("pllimit=50", request.full_url)
        self.assertIn("plnamespace=0", request.full_url)


if __name__ == "__main__":
    unittest.main()
