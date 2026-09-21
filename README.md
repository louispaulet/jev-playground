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
make test
```

The script repeatedly prompts for surnames, sends each one to JEV as the state, and predicts one of `male`, `female`, or `unisex`. It prints the selected choice, probabilities, and confidence. Press Ctrl+C to exit.
