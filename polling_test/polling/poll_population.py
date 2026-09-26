#!/usr/bin/env python3
"""Ask JEV for a survey-answer distribution for CSV personas."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
QUESTION_HASH_FIELD = "question_sha256"
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


def make_question_hash(question: str, options: tuple[str, ...]) -> str:
    """Return a stable cache key for a question and its answer choices."""
    payload = json.dumps(
        {"question": question, "options": options},
        ensure_ascii=False,
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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


def answer_record(answer: Any) -> dict[str, Any]:
    """Convert a TypeSafe Choice answer to the CSV-friendly representation."""
    probabilities: Any = answer.probabilities
    return {
        "selected_answer": str(answer.choice),
        "confidence": float(answer.confidence),
        "probabilities": {
            str(option): float(probability)
            for option, probability in probabilities.items()
        },
    }


def ask_jev_batch(
    client: TypeSafeClient,
    persona: dict[str, str],
    question_specs: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Ask all independent benchmark questions in one paid API call."""
    questions = {
        spec["id"]: Choice(
            instructions=spec["question"],
            criteria={option: None for option in spec["options"]},
        )
        for spec in question_specs
    }
    result = client.system_one(
        state=persona_state(persona),
        questions=questions,
    )
    return {
        spec["id"]: answer_record(result.choices[spec["id"]])
        for spec in question_specs
    }


def ask_jev(
    client: TypeSafeClient,
    persona: dict[str, str],
    question: str,
    options: tuple[str, ...],
) -> dict[str, Any]:
    """Return one Choice answer, retaining the original helper API."""
    return ask_jev_batch(
        client,
        persona,
        [{"id": "answer", "question": question, "options": options}],
    )["answer"]


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
    question: str | None = None,
    question_id: str | None = None,
) -> None:
    """Write one joinable CSV row per persona."""
    columns = probability_columns(options)
    metadata_fields = ["question_id", QUESTION_HASH_FIELD] if question else []
    fieldnames = [PERSONA_ID_FIELD, *metadata_fields, "selected_answer", "confidence", *columns.values()]
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
            if question:
                row["question_id"] = question_id or "question"
                row[QUESTION_HASH_FIELD] = make_question_hash(question, options)
            row.update({columns[option]: probabilities.get(option, 0.0) for option in options})
            writer.writerow(row)


def find_cached_result(
    question: str,
    options: tuple[str, ...],
    personas: list[dict[str, str]],
    output_dir: Path,
    exact_path: Path | None = None,
) -> Path | None:
    """Find a complete prior CSV so rerunning a paid poll costs nothing."""
    candidates = [exact_path] if exact_path else sorted(output_dir.glob("*.csv"), reverse=True)
    expected_hash = make_question_hash(question, options)
    expected_columns = set(probability_columns(options).values())
    expected_ids = [persona[PERSONA_ID_FIELD] for persona in personas]
    for candidate in candidates:
        if candidate is None or not candidate.exists():
            continue
        if not exact_path and slugify_question(question) not in candidate.name:
            continue
        try:
            with candidate.open(newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                if not reader.fieldnames or not expected_columns.issubset(reader.fieldnames):
                    continue
                rows = list(reader)
        except (OSError, csv.Error, UnicodeError):
            continue
        if len(rows) != len(expected_ids):
            continue
        if [row.get(PERSONA_ID_FIELD) for row in rows] != expected_ids:
            continue
        if any(row.get(QUESTION_HASH_FIELD) != expected_hash for row in rows):
            continue
        return candidate
    return None


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
        dest="question_files",
        type=Path,
        action="append",
        help="UTF-8 question file; repeat to batch independent questions in one API call.",
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore matching cached CSVs and pay to run the questions again.",
    )
    return parser.parse_args()


def question_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Build validated question specifications from CLI arguments."""
    if args.question_files:
        if args.options and len(args.question_files) != 1:
            raise ValueError("--option can only be used with one --question-file")
        specs = []
        seen_ids: set[str] = set()
        for question_file in args.question_files:
            question = read_question(question_file)
            options = unique_options(
                args.options if args.options else parse_numbered_options(question)
            )
            if len(options) < 2:
                raise ValueError(f"Question has fewer than two choices: {question_file}")
            question_id = question_file.stem
            if question_id in seen_ids:
                raise ValueError(f"Duplicate question file stem: {question_id}")
            seen_ids.add(question_id)
            specs.append({"id": question_id, "question": question, "options": options})
        return specs

    options = unique_options(args.options or DEFAULT_OPTIONS)
    if len(options) < 2:
        raise ValueError("Provide at least two answer choices")
    return [{"id": "question", "question": args.question, "options": options}]


def main() -> None:
    args = parse_args()
    if args.limit < 0:
        raise ValueError("--limit must be zero or greater")
    specs = question_specs(args)
    personas = load_personas(args.csv, args.limit)
    cached_paths: dict[str, Path] = {}
    pending_specs: list[dict[str, Any]] = []
    for spec in specs:
        exact_path = args.output if len(specs) == 1 else None
        cached = None if args.force else find_cached_result(
            spec["question"], spec["options"], personas, args.output_dir, exact_path
        )
        if cached:
            cached_paths[spec["id"]] = cached
            print(f"Reusing cached poll results from {cached}", file=sys.stderr)
        else:
            pending_specs.append(spec)

    if pending_specs:
        if not os.getenv("TYPESAFE_API_KEY"):
            raise RuntimeError("Set TYPESAFE_API_KEY before running this script")
        responses_by_id = {spec["id"]: [] for spec in pending_specs}
        with TypeSafeClient(model="jev-latest") as client:
            for index, persona in enumerate(personas, start=1):
                batch = ask_jev_batch(client, persona, pending_specs)
                for spec in pending_specs:
                    responses_by_id[spec["id"]].append(batch[spec["id"]])
                if index == 1 or index % 25 == 0 or index == len(personas):
                    print(f"Polled {index}/{len(personas)} personas ({len(pending_specs)} questions in one call)", file=sys.stderr)

        if args.output and len(specs) != 1:
            raise ValueError("--output can only be used with one question")
        for spec in pending_specs:
            output_path = args.output or result_path(spec["question"], args.output_dir)
            write_results(
                output_path,
                personas,
                responses_by_id[spec["id"]],
                spec["options"],
                question=spec["question"],
                question_id=spec["id"],
            )
            print(f"Wrote poll results to {output_path}", file=sys.stderr)

    if not args.quiet and len(specs) == 1 and specs[0]["id"] not in cached_paths:
        print(f"Question: {specs[0]['question']}")


if __name__ == "__main__":
    main()
