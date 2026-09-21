#!/usr/bin/env python3
"""Print the first links from a Wikipedia article."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


API_URL = "https://en.wikipedia.org/w/api.php"
ARTICLE_URL = "https://en.wikipedia.org/wiki/"
USER_AGENT = "jev-playground/0.1 (Wikipedia link explorer)"
SUGGESTION_LIMIT = 5
API_MAX_RETRIES = 2
MAX_RETRY_DELAY_SECONDS = 30.0


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


def _api_json(params: dict[str, str]) -> dict[str, object]:
    query = urlencode(params)
    request = Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": USER_AGENT},
    )
    for attempt in range(API_MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=20) as response:
                data = json.load(response)
            return data if isinstance(data, dict) else {}
        except HTTPError as error:
            if error.code != 429 or attempt == API_MAX_RETRIES:
                if error.code == 429:
                    raise RuntimeError(
                        "Wikipedia API rate limit (HTTP 429) persisted after "
                        f"{API_MAX_RETRIES} retries; wait a moment and rerun."
                    ) from error
                raise

            retry_after = error.headers.get("Retry-After")
            delay: float | None = None
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(retry_after)
                        if retry_at.tzinfo is None:
                            retry_at = retry_at.replace(tzinfo=timezone.utc)
                        delay = (
                            retry_at - datetime.now(timezone.utc)
                        ).total_seconds()
                    except (TypeError, ValueError, OverflowError):
                        delay = None

            if delay is None:
                delay = float(2**attempt)
            time.sleep(min(max(delay, 0.0), MAX_RETRY_DELAY_SECONDS))


def _find_article_title(title: str) -> str | None:
    data = _api_json(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "titles": title,
            "redirects": "1",
        }
    )
    pages = data.get("query", {}).get("pages", [])
    if not isinstance(pages, list) or not pages:
        return None

    page = pages[0]
    if not isinstance(page, dict) or "missing" in page or "invalid" in page:
        return None
    resolved_title = page.get("title")
    return resolved_title if isinstance(resolved_title, str) else None


def _suggest_article_titles(title: str, limit: int = SUGGESTION_LIMIT) -> list[str]:
    data = _api_json(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "list": "search",
            "srnamespace": "0",
            "srsearch": title,
            "srlimit": str(limit),
            "srinfo": "suggestion",
        }
    )
    query = data.get("query", {})
    if not isinstance(query, dict):
        return []

    suggestions: list[str] = []
    search_info = query.get("searchinfo", {})
    if isinstance(search_info, dict):
        suggestion = search_info.get("suggestion")
        if isinstance(suggestion, str) and suggestion.strip():
            suggestions.append(suggestion.strip())

    search_results = query.get("search", [])
    if isinstance(search_results, list):
        for result in search_results:
            if not isinstance(result, dict):
                continue
            result_title = result.get("title")
            if isinstance(result_title, str) and result_title.strip():
                suggestions.append(result_title.strip())

    unique_suggestions: list[str] = []
    seen = {_title_key(title)}
    for suggestion in suggestions:
        key = _title_key(suggestion)
        if key in seen:
            continue
        seen.add(key)
        unique_suggestions.append(suggestion)
        if len(unique_suggestions) == limit:
            break
    return unique_suggestions


def validate_article_titles(start: str, target: str) -> tuple[str, str]:
    """Confirm both race endpoints and return their canonical Wikipedia titles."""
    resolved_titles: list[str] = []
    errors: list[str] = []

    for label, article in (("Start", start), ("Target", target)):
        try:
            title = article_title(article)
        except ValueError as error:
            errors.append(f"{label} article is invalid: {error}")
            continue

        resolved_title = _find_article_title(title)
        if resolved_title is None:
            suggestions = _suggest_article_titles(title)
            message = f"{label} Wikipedia article not found: {title}"
            if suggestions:
                message += "\n  Suggested titles:\n" + "\n".join(
                    f"    - {suggestion}" for suggestion in suggestions
                )
            errors.append(message)
            continue
        resolved_titles.append(resolved_title)

    if errors:
        raise ValueError(
            "\n".join(errors)
            + "\nCopy a suggested title and rerun the command."
        )

    return resolved_titles[0], resolved_titles[1]


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
    data = _api_json(
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
    except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    for link in links:
        print(link)


if __name__ == "__main__":
    main()
