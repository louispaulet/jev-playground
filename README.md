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
