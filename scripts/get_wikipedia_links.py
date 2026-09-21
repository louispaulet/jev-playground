#!/usr/bin/env python3
"""Print the first links from a Wikipedia article."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
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
        hostname = parsed.hostname or ""
        if hostname != "wikipedia.org" and not hostname.endswith(".wikipedia.org"):
            raise ValueError("URL must point to wikipedia.org")

        if parsed.path.startswith("/wiki/"):
            title = unquote(parsed.path.removeprefix("/wiki/"))
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


def _title_key(title: str) -> str:
    """Return a forgiving key for comparing page names and URLs."""
    return " ".join(title.replace("_", " ").split()).casefold()


def _filter_links(
    article: str,
    link_titles: list[str],
    visited: list[str],
    limit: int,
) -> list[str]:
    excluded = {_title_key(article), *(_title_key(page) for page in visited)}
    seen = set(excluded)
    useful_links = []

    for link_title in link_titles:
        key = _title_key(link_title)
        if not key or key in seen:
            continue
        seen.add(key)
        useful_links.append(wikipedia_url(link_title))
        if len(useful_links) == limit:
            break

    return useful_links


def get_wikipedia_links(
    article: str,
    limit: int = 50,
    visited: list[str] | None = None,
) -> list[str]:
    """Return up to ``limit`` useful article URLs linked from a Wikipedia page."""
    if not 1 <= limit <= 500:
        raise ValueError("limit must be between 1 and 500")

    title = article_title(article)
    visited_titles = [article_title(page) for page in (visited or [])]
    query = urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": title,
            "prop": "links",
            "plnamespace": "0",
            "pllimit": "500",
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

    link_titles = [link["title"] for link in pages[0].get("links", [])]
    return _filter_links(title, link_titles, visited_titles, limit)


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
    parser.add_argument(
        "--visited",
        action="append",
        default=[],
        help="page name or URL to exclude; repeat for multiple visited pages",
    )
    args = parser.parse_args()

    try:
        links = get_wikipedia_links(
            " ".join(args.article),
            limit=args.limit,
            visited=args.visited,
        )
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        parser.error(str(error))

    for link in links:
        print(link)


if __name__ == "__main__":
    main()
