#!/usr/bin/env python3
"""Ask JEV for a survey-answer distribution for CSV personas."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from typesafe_sdk import Choice, TypeSafeClient


DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[1] / "population" / "population_sample.csv"
)
DEFAULT_QUESTION = (
    "Vous personnellement, diriez-vous que vous êtes inquiet ou pas inquiet "
    "de la situation en Ukraine ?"
)
DEFAULT_OPTIONS = (
    "Très inquiet",
    "Plutôt inquiet",
    "Pas vraiment inquiet",
    "Pas du tout inquiet",
)
PERSONA_ID_FIELD = "persona_id"


def load_personas(csv_path: Path, limit: int) -> list[dict[str, str]]:
    """Load the first ``limit`` persona rows from the CSV file."""
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")
        if PERSONA_ID_FIELD not in reader.fieldnames:
            raise ValueError(f"CSV is missing {PERSONA_ID_FIELD!r}: {csv_path}")
        personas = []
        for row in reader:
            if len(personas) >= limit:
                break
            personas.append({key: value or "" for key, value in row.items()})
    if len(personas) < limit:
        raise ValueError(f"CSV contains only {len(personas)} persona rows")
    return personas


def persona_state(persona: dict[str, str]) -> dict[str, dict[str, str]]:
    """Build JEV state while excluding the identifier used only for display."""
    return {
        "persona": {
            key: value for key, value in persona.items() if key != PERSONA_ID_FIELD
        }
    }


def ask_jev(
    client: TypeSafeClient,
    persona: dict[str, str],
    question: str,
    options: tuple[str, ...],
) -> dict[str, float]:
    """Return the Choice probability mapping for one persona."""
    result = client.system_one(
        state=persona_state(persona),
        questions={
            "answer": Choice(
                instructions=question,
                criteria={option: None for option in options},
            )
        },
    )
    probabilities: Any = result.choices["answer"].probabilities
    return {str(option): float(probability) for option, probability in probabilities.items()}


def print_results(
    personas: list[dict[str, str]], results: list[dict[str, float]], question: str
) -> None:
    """Print personas and answer distributions as readable table rows."""
    print(f"Question: {question}")
    print()
    print("persona_id | persona context | answer probabilities")
    print("-" * 120)
    for persona, probabilities in zip(personas, results):
        context = {
            key: value for key, value in persona.items() if key != PERSONA_ID_FIELD
        }
        context_text = json.dumps(context, ensure_ascii=False, separators=(", ", ": "))
        probability_text = json.dumps(
            probabilities, ensure_ascii=False, separators=(", ", ": ")
        )
        print(f"{persona[PERSONA_ID_FIELD]} | {context_text} | {probability_text}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a TypeSafe Choice question for CSV personas."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Persona CSV path (default: {DEFAULT_CSV_PATH})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of rows to evaluate from the start of the CSV (default: 5)",
    )
    parser.add_argument(
        "--question",
        default=DEFAULT_QUESTION,
        help="Question sent to JEV.",
    )
    parser.add_argument(
        "--option",
        dest="options",
        action="append",
        help="Allowed answer choice; repeat for each choice.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit < 1:
        raise ValueError("--limit must be at least 1")
    if not os.getenv("TYPESAFE_API_KEY"):
        raise RuntimeError("Set TYPESAFE_API_KEY before running this script")

    options = tuple(args.options or DEFAULT_OPTIONS)
    if len(options) < 2:
        raise ValueError("Provide at least two answer choices")

    personas = load_personas(args.csv, args.limit)
    with TypeSafeClient(model="jev-latest") as client:
        results = [ask_jev(client, persona, args.question, options) for persona in personas]
    print_results(personas, results, args.question)


if __name__ == "__main__":
    main()
