#!/usr/bin/env python3
"""Print the first links from a Wikipedia article."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen


API_URL = "https://en.wikipedia.org/w/api.php"
ARTICLE_URL = "https://en.wikipedia.org/wiki/"
USER_AGENT = "jev-playground/0.1 (Wikipedia link explorer)"


def article_title(article: str) -> str:
    """Convert a page name or Wikipedia article URL into a page title."""
    article = article.strip()
    if not article:
        raise ValueError("article cannot be empty")

    parsed = urlparse(article)
    if parsed.scheme and parsed.netloc:
        if not parsed.netloc.lower().endswith("wikipedia.org"):
            raise ValueError("URL must point to wikipedia.org")

        if parsed.path.startswith("/wiki/"):
            title = parsed.path.removeprefix("/wiki/")
        elif parsed.path == "/w/index.php":
            title = parse_qs(parsed.query).get("title", [""])[0]
        else:
            raise ValueError("URL must be a Wikipedia article URL")
        title = title.replace("_", " ")
    else:
        title = article.replace("_", " ")

    title = title.strip()
    if not title:
        raise ValueError("could not find an article title")
    return title


def wikipedia_url(title: str) -> str:
    """Build a readable URL for an English Wikipedia article title."""
    encoded_title = quote(title.replace(" ", "_"), safe="()'!,;:@&=+$-._~/")
    return f"{ARTICLE_URL}{encoded_title}"


def get_wikipedia_links(article: str, limit: int = 50) -> list[str]:
    """Return up to ``limit`` article URLs linked from a Wikipedia page."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    title = article_title(article)
    query = urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": title,
            "prop": "links",
            "plnamespace": "0",
            "pllimit": str(limit),
            "pldir": "ascending",
            "redirects": "1",
        }
    )
    request = Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": USER_AGENT},
    )

    with urlopen(request, timeout=20) as response:
        data = json.load(response)

    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        raise ValueError(f"Wikipedia article not found: {title}")

    return [wikipedia_url(link["title"]) for link in pages[0].get("links", [])]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print up to 50 main-namespace links from a Wikipedia article."
    )
    parser.add_argument(
        "article",
        nargs="+",
        help="Wikipedia page name or URL, for example 'Beaver'",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="number of links to print, from 1 to 500 (default: 50)",
    )
    args = parser.parse_args()

    try:
        links = get_wikipedia_links(" ".join(args.article), limit=args.limit)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        parser.error(str(error))

    for link in links:
        print(link)


if __name__ == "__main__":
    main()
