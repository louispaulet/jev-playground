# jev-playground

A minimal example of using the TypeSafe/JEV API from Python.

## Setup

Install [uv](https://docs.astral.sh/uv/) if needed, then set up the project:

```bash
make install
```

Create a local `.env` file with your TypeSafe API key:

```bash
TYPESAFE_API_KEY="your-api-key"
```

The `.env` file is ignored by Git and must not be committed.

## Run

```bash
make test-choice
```

The script repeatedly prompts for surnames, sends each one to JEV as the state, and predicts one of `male`, `female`, or `unisex`. It prints the selected choice, probabilities, and confidence. Press Ctrl+C to exit.

## Wikipedia links

Print up to 50 links from an English Wikipedia article:

```bash
python scripts/get_wikipedia_links.py Beaver
python scripts/get_wikipedia_links.py "https://en.wikipedia.org/wiki/Apollo_11"
python scripts/get_wikipedia_links.py Beaver --visited Canada --visited "North America"
```

The script removes the current page, visited pages, duplicate links, and non-article namespaces before returning links in Wikipedia API order. It fetches a larger pool so the default output is up to 50 useful links. It does not rank them by relevance yet; that is the next step for the JEV experiment. Use `--limit` to request a different number, up to 500, and repeat `--visited` for pages to exclude.

## Wikipedia JEV beam search

Run a batched beam search from one article to another:

```bash
make wikipedia-race START=Beaver END="Apollo 11"
```

The default configuration keeps 3 paths, uses 200 candidates per JEV Choice, keeps 5 winners per batch, stops after 6 hops, and limits uncached JEV calls to 40. Decisions are cached in `.wikipedia_jev_cache.json`, which is ignored by Git. The script reports response token usage and an estimated cost using TypeSafe's published `$0.042 / 1M input tokens` rate; cached decisions add no new cost. Tune the search with `--beam-width`, `--batch-size`, `--per-batch`, `--max-hops`, `--call-budget`, and `--cache`. The Make target accepts `MAX_HOPS` and `CALL_BUDGET` overrides, for example `make wikipedia-race START=Jacques_Chirac END="Bonnie Blue" MAX_HOPS=20 CALL_BUDGET=400`.

The race writes standard `INFO`, `WARNING`, and `ERROR` records to `.wikipedia_jev.log`, which is ignored by Git. Use `--log PATH` to choose another file and `--log-level DEBUG` for more detail when diagnosing a run.
