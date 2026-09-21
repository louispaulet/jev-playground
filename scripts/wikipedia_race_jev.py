#!/usr/bin/env python3
"""Navigate from one Wikipedia article to another with batched JEV beam search."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

from scripts.get_wikipedia_links import (
    _title_key,
    article_title,
    get_wikipedia_links,
    validate_article_titles,
)


MAX_CHOICES = 255
MAX_LINKS = 500
EPSILON = 1e-9
INPUT_COST_PER_MILLION_TOKENS = 0.042


def _split_batches(items: list[str], batch_size: int) -> list[list[str]]:
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def _path_score(log_probability: float, decisions: int) -> float:
    if not decisions:
        return 1.0
    return math.exp(log_probability / decisions)


def _load_cache(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_cache(path: Path, cache: dict[str, dict[str, float]]) -> None:
    path.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")


def _cache_key(current: str, target: str, candidates: list[str]) -> str:
    return json.dumps(
        {"current": current, "target": target, "candidates": candidates},
        separators=(",", ":"),
        sort_keys=True,
    )


def _choose_distribution(
    client: TypeSafeClient,
    current: str,
    target: str,
    candidates: list[str],
    cache: dict[str, dict[str, float]],
    cache_path: Path,
    stats: dict[str, int | float],
    call_budget: int,
) -> dict[str, float]:
    if len(candidates) == 1:
        return {candidates[0]: 1.0}

    key = _cache_key(current, target, candidates)
    if key in cache:
        stats["cache_hits"] += 1
        return cache[key]

    if stats["calls"] >= call_budget:
        raise RuntimeError(f"JEV call budget exhausted at {call_budget} calls")

    criteria = {f"c{index}": candidate for index, candidate in enumerate(candidates)}
    question = Choice(
        instructions=(
            "Which candidate Wikipedia article should we visit next to get closer "
            "to the target article? Choose the candidate with the strongest likely "
            "progress toward the target, not merely the most famous or alphabetical."
        ),
        criteria=criteria,
    )
    state = f"Current Wikipedia article: {current}\nTarget Wikipedia article: {target}"
    response = client.system_one(state=state, questions={"next_article": question})
    answer = response.answers["next_article"]
    input_tokens = response.usage.input_tokens or 0
    output_tokens = response.usage.output_tokens or 0
    stats["input_tokens"] += input_tokens
    stats["output_tokens"] += output_tokens
    stats["estimated_cost_usd"] += (
        input_tokens / 1_000_000 * INPUT_COST_PER_MILLION_TOKENS
    )
    probabilities = {
        criteria[key]: float(answer.probabilities.get(key, 0.0)) for key in criteria
    }

    cache[key] = probabilities
    _save_cache(cache_path, cache)
    stats["calls"] += 1
    return probabilities


def _choose_next(
    client: TypeSafeClient,
    current: str,
    target: str,
    candidates: list[str],
    batch_size: int,
    per_batch: int,
    beam_width: int,
    cache: dict[str, dict[str, float]],
    cache_path: Path,
    stats: dict[str, int | float],
    call_budget: int,
) -> list[tuple[str, float]]:
    batches = _split_batches(candidates, batch_size)
    if len(batches) == 1:
        probabilities = _choose_distribution(
            client,
            current,
            target,
            batches[0],
            cache,
            cache_path,
            stats,
            call_budget,
        )
        return sorted(probabilities.items(), key=lambda item: item[1], reverse=True)[
            :beam_width
        ]

    # Keep the final reranking Choice safely below the 255-choice limit.
    keep_per_batch = min(per_batch, max(1, MAX_CHOICES // len(batches)))
    finalists: list[str] = []
    for batch in batches:
        probabilities = _choose_distribution(
            client,
            current,
            target,
            batch,
            cache,
            cache_path,
            stats,
            call_budget,
        )
        finalists.extend(
            candidate
            for candidate, _ in sorted(
                probabilities.items(), key=lambda item: item[1], reverse=True
            )[:keep_per_batch]
        )

    final_probabilities = _choose_distribution(
        client,
        current,
        target,
        finalists,
        cache,
        cache_path,
        stats,
        call_budget,
    )
    return sorted(
        final_probabilities.items(), key=lambda item: item[1], reverse=True
    )[:beam_width]


def run_search(
    start: str,
    target: str,
    beam_width: int = 3,
    batch_size: int = 200,
    per_batch: int = 5,
    max_hops: int = 6,
    call_budget: int = 40,
    cache_path: Path = Path(".wikipedia_jev_cache.json"),
    _validated_titles: tuple[str, str] | None = None,
) -> dict[str, object]:
    """Run a title-only Wikipedia graph search and return its result."""
    if not 1 <= beam_width <= 20:
        raise ValueError("beam_width must be between 1 and 20")
    if not 2 <= batch_size <= MAX_CHOICES:
        raise ValueError(f"batch_size must be between 2 and {MAX_CHOICES}")
    if not 1 <= per_batch <= MAX_CHOICES:
        raise ValueError(f"per_batch must be between 1 and {MAX_CHOICES}")
    if max_hops < 1 or call_budget < 1:
        raise ValueError("max_hops and call_budget must be positive")

    if _validated_titles is None:
        start_title, target_title = validate_article_titles(start, target)
    else:
        start_title, target_title = _validated_titles
    cache = _load_cache(cache_path)
    stats: dict[str, int | float] = {
        "calls": 0,
        "cache_hits": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    beam = [{"pages": [start_title], "log_probability": 0.0, "decisions": 0}]

    if _title_key(start_title) == _title_key(target_title):
        return {"pages": [start_title], "found": True, "stats": stats}

    client = TypeSafeClient()

    for _ in range(max_hops):
        next_paths: dict[tuple[str, ...], dict[str, object]] = {}

        for path in beam:
            pages = path["pages"]
            current = pages[-1]
            links = get_wikipedia_links(current, limit=MAX_LINKS, visited=pages)
            candidates = [article_title(link) for link in links]
            target_key = _title_key(target_title)

            for candidate in candidates:
                if _title_key(candidate) == target_key:
                    return {
                        "pages": [*pages, candidate],
                        "found": True,
                        "stats": stats,
                    }

            candidates = [
                candidate
                for candidate in candidates
                if _title_key(candidate) not in {_title_key(page) for page in pages}
            ]
            if not candidates:
                continue

            choices = _choose_next(
                client,
                current,
                target_title,
                candidates,
                batch_size,
                per_batch,
                beam_width,
                cache,
                cache_path,
                stats,
                call_budget,
            )
            for candidate, probability in choices:
                candidate_key = _title_key(candidate)
                if candidate_key in {_title_key(page) for page in pages}:
                    continue
                new_pages = [*pages, candidate]
                new_path = {
                    "pages": new_pages,
                    "log_probability": path["log_probability"]
                    + math.log(max(probability, EPSILON)),
                    "decisions": path["decisions"] + 1,
                }
                next_paths[tuple(new_pages)] = new_path

        if not next_paths:
            break

        beam = sorted(
            next_paths.values(),
            key=lambda path: _path_score(path["log_probability"], path["decisions"]),
            reverse=True,
        )[:beam_width]

    best_path = max(
        beam,
        key=lambda path: _path_score(path["log_probability"], path["decisions"]),
    )
    return {"pages": best_path["pages"], "found": False, "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a batched JEV beam search on Wikipedia.")
    parser.add_argument("start", help="starting Wikipedia page name or URL")
    parser.add_argument("target", help="target Wikipedia page name or URL")
    parser.add_argument("--beam-width", type=int, default=3, help="paths to retain (default: 3)")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=200,
        help="maximum candidates per JEV Choice, from 2 to 255 (default: 200)",
    )
    parser.add_argument(
        "--per-batch",
        type=int,
        default=5,
        help="candidates retained from each batch before reranking (default: 5)",
    )
    parser.add_argument("--max-hops", type=int, default=6, help="maximum hops (default: 6)")
    parser.add_argument(
        "--call-budget",
        type=int,
        default=40,
        help="maximum uncached JEV calls (default: 40)",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".wikipedia_jev_cache.json"),
        help="JSON cache path (default: .wikipedia_jev_cache.json)",
    )
    args = parser.parse_args()

    if not 1 <= args.beam_width <= 20:
        parser.error("--beam-width must be between 1 and 20")
    if not 2 <= args.batch_size <= MAX_CHOICES:
        parser.error(f"--batch-size must be between 2 and {MAX_CHOICES}")
    if not 1 <= args.per_batch <= MAX_CHOICES:
        parser.error(f"--per-batch must be between 1 and {MAX_CHOICES}")
    if not 1 <= args.max_hops or not 1 <= args.call_budget:
        parser.error("--max-hops and --call-budget must be positive")

    try:
        validated_titles = validate_article_titles(args.start, args.target)
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))

    started_at = time.perf_counter()
    try:
        result = run_search(
            args.start,
            args.target,
            beam_width=args.beam_width,
            batch_size=args.batch_size,
            per_batch=args.per_batch,
            max_hops=args.max_hops,
            call_budget=args.call_budget,
            cache_path=args.cache,
            _validated_titles=validated_titles,
        )
    except (OSError, RuntimeError, ValueError) as error:
        parser.error(str(error))
    elapsed_seconds = time.perf_counter() - started_at

    pages = result["pages"]
    stats = result["stats"]
    print(f"{'Found' if result['found'] else 'Best path'} in {len(pages) - 1} hops:")
    print(" -> ".join(pages))
    print(f"JEV calls: {stats['calls']} | cache hits: {stats['cache_hits']}")
    print(
        f"Tokens: {stats['input_tokens']:,} input + {stats['output_tokens']:,} output"
    )
    print(
        f"Estimated API cost this run: ${stats['estimated_cost_usd']:.6f} "
        f"(input at ${INPUT_COST_PER_MILLION_TOKENS:.3f}/M; output currently free)"
    )
    print(f"Elapsed time: {elapsed_seconds:.2f} seconds")


if __name__ == "__main__":
    main()
