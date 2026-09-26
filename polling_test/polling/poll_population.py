#!/usr/bin/env python3
"""Ask JEV for a survey-answer distribution for CSV personas."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from typesafe_sdk import Choice, TypeSafeClient


DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[1] / "population" / "population_sample.csv"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "results"
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
NUMBERED_OPTION_RE = re.compile(r"^\s*\d+\s*[.)]\s*(?P<label>\S.*)\s*$")


def load_personas(csv_path: Path, limit: int) -> list[dict[str, str]]:
    """Load the first ``limit`` persona rows, or all rows when limit is zero."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")

    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")
        if PERSONA_ID_FIELD not in reader.fieldnames:
            raise ValueError(f"CSV is missing {PERSONA_ID_FIELD!r}: {csv_path}")
        personas = []
        for row in reader:
            if limit and len(personas) >= limit:
                break
            personas.append({key: value or "" for key, value in row.items()})
    if limit and len(personas) < limit:
        raise ValueError(f"CSV contains only {len(personas)} persona rows")
    if not personas:
        raise ValueError(f"CSV contains no persona rows: {csv_path}")
    return personas


def read_question(question_file: Path) -> str:
    """Read and validate a question text file."""
    question = question_file.read_text(encoding="utf-8").strip()
    if not question:
        raise ValueError(f"Question file is empty: {question_file}")
    return question


def parse_numbered_options(question: str) -> tuple[str, ...]:
    """Extract unique numbered answer choices from a question."""
    options: list[str] = []
    for line in question.splitlines():
        match = NUMBERED_OPTION_RE.match(line)
        if match:
            label = match.group("label").strip()
            if label and label not in options:
                options.append(label)
    return tuple(options)


def unique_options(options: Iterable[str]) -> tuple[str, ...]:
    """Remove repeated answer labels without changing their order."""
    unique: list[str] = []
    for option in options:
        label = option.strip()
        if label and label not in unique:
            unique.append(label)
    return tuple(unique)


def slugify_question(question: str, max_length: int = 200) -> str:
    """Create a filesystem-safe slug from the first ``max_length`` characters."""
    if max_length < 1:
        raise ValueError("max_length must be at least 1")
    excerpt = question[:max_length]
    ascii_excerpt = unicodedata.normalize("NFKD", excerpt).encode(
        "ascii", "ignore"
    ).decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_excerpt.lower()).strip("-")
    return (slug or "question")[:max_length].rstrip("-")


def result_path(
    question: str, output_dir: Path, timestamp: datetime | None = None
) -> Path:
    """Return a timestamp-prefixed, sortable result path."""
    moment = timestamp or datetime.now(timezone.utc)
    timestamp_text = moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return output_dir / f"{timestamp_text}_{slugify_question(question)}.csv"


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
) -> dict[str, Any]:
    """Return the Choice answer and probability mapping for one persona."""
    result = client.system_one(
        state=persona_state(persona),
        questions={
            "answer": Choice(
                instructions=question,
                criteria={option: None for option in options},
            )
        },
    )
    answer = result.choices["answer"]
    probabilities: Any = answer.probabilities
    return {
        "selected_answer": str(answer.choice),
        "confidence": float(answer.confidence),
        "probabilities": {
            str(option): float(probability)
            for option, probability in probabilities.items()
        },
    }


def probability_columns(options: Iterable[str]) -> dict[str, str]:
    """Map answer labels to stable, readable CSV column names."""
    columns: dict[str, str] = {}
    used: set[str] = set()
    for option in options:
        base = f"probability_{slugify_question(option, max_length=120)}"
        column = base
        suffix = 2
        while column in used:
            column = f"{base}_{suffix}"
            suffix += 1
        columns[option] = column
        used.add(column)
    return columns


def write_results(
    output_path: Path,
    personas: list[dict[str, str]],
    responses: list[dict[str, Any]],
    options: tuple[str, ...],
) -> None:
    """Write one joinable CSV row per persona."""
    columns = probability_columns(options)
    fieldnames = [PERSONA_ID_FIELD, "selected_answer", "confidence", *columns.values()]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for persona, response in zip(personas, responses):
            probabilities = response["probabilities"]
            row: dict[str, Any] = {
                PERSONA_ID_FIELD: persona[PERSONA_ID_FIELD],
                "selected_answer": response["selected_answer"],
                "confidence": response["confidence"],
            }
            row.update({columns[option]: probabilities.get(option, 0.0) for option in options})
            writer.writerow(row)


def print_results(
    personas: list[dict[str, str]], results: list[dict[str, Any]], question: str
) -> None:
    """Print personas and answer distributions as readable table rows."""
    print(f"Question: {question}")
    print()
    print("persona_id | persona context | answer probabilities")
    print("-" * 120)
    for persona, result in zip(personas, results):
        context = {
            key: value for key, value in persona.items() if key != PERSONA_ID_FIELD
        }
        context_text = json.dumps(context, ensure_ascii=False, separators=(", ", ": "))
        probability_text = json.dumps(
            result["probabilities"], ensure_ascii=False, separators=(", ", ": ")
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
        help="Number of rows to evaluate; use 0 for all rows (default: 5)",
    )
    parser.add_argument(
        "--question-file",
        type=Path,
        help="UTF-8 text file containing the question and optional numbered choices.",
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
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for timestamped result CSVs (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write to this exact CSV path instead of a timestamped path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the human-readable persona table.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.limit < 0:
        raise ValueError("--limit must be zero or greater")
    if not os.getenv("TYPESAFE_API_KEY"):
        raise RuntimeError("Set TYPESAFE_API_KEY before running this script")

    question = read_question(args.question_file) if args.question_file else args.question
    options = unique_options(args.options or parse_numbered_options(question) or DEFAULT_OPTIONS)
    if len(options) < 2:
        raise ValueError("Provide at least two answer choices")

    personas = load_personas(args.csv, args.limit)
    responses: list[dict[str, Any]] = []
    with TypeSafeClient(model="jev-latest") as client:
        for index, persona in enumerate(personas, start=1):
            responses.append(ask_jev(client, persona, question, options))
            if index == 1 or index % 25 == 0 or index == len(personas):
                print(f"Polled {index}/{len(personas)} personas", file=sys.stderr)

    output_path = args.output or result_path(question, args.output_dir)
    write_results(output_path, personas, responses, options)
    if not args.quiet:
        print_results(personas, responses, question)
    print(f"Wrote poll results to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
