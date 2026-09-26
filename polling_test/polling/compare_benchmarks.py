#!/usr/bin/env python3
"""Compare cached JEV benchmark CSVs with election and INSEE targets."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from benchmark_targets import QUESTION_FILES, TARGETS
from poll_population import parse_numbered_options, probability_columns, read_question, slugify_question, unique_options


DEFAULT_PERSONA_CSV = Path(__file__).resolve().parents[1] / "population" / "population_sample.csv"
DEFAULT_QUESTION_DIR = Path(__file__).resolve().parents[1] / "questions"
DEFAULT_RESULT_DIR = Path(__file__).resolve().parents[1] / "results"
DEFAULT_REPORT = Path(__file__).with_name("BENCHMARK_RESULTS.md")


def find_result(result_dir: Path, question: str) -> Path:
    """Find the newest CSV for a question slug."""
    matches = sorted(
        (path for path in result_dir.glob("*.csv") if slugify_question(question) in path.name),
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(f"No cached result CSV found for: {question}")
    return matches[0]


def load_rows(result_path: Path) -> list[dict[str, str]]:
    with result_path.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def load_personas(persona_csv: Path) -> dict[str, dict[str, str]]:
    with persona_csv.open(newline="", encoding="utf-8") as csv_file:
        return {row["persona_id"]: row for row in csv.DictReader(csv_file)}


def percent(value: float) -> str:
    return f"{value:.2f}%"


def build_report(
    question_dir: Path,
    result_dir: Path,
    persona_csv: Path,
) -> str:
    personas = load_personas(persona_csv)
    lines = [
        "# JEV benchmark results versus IRL targets",
        "",
        "This report compares the cached JEV probability distributions with known",
        "French election results and the INSEE-controlled margins used to build the",
        "synthetic population. All benchmark questions were batched into one JEV",
        "request per persona, and each question's response was saved as its own CSV.",
        "",
        "JEV values are mean probabilities across the personas. Differences are",
        "JEV minus IRL, in percentage points. Election targets use registered voters",
        "as the denominator, so abstention, blank and null options remain comparable.",
        "",
    ]

    for question_filename in QUESTION_FILES:
        question_id = Path(question_filename).stem
        target_info = TARGETS[question_id]
        question_path = question_dir / question_filename
        question = read_question(question_path)
        options = unique_options(parse_numbered_options(question))
        result_path = find_result(result_dir, question)
        rows = load_rows(result_path)
        columns = probability_columns(options)
        averages = {
            option: sum(float(row[columns[option]]) for row in rows) / len(rows) * 100
            for option in options
        }
        actual = target_info["targets_percent"]

        lines.extend(
            [
                f"## {target_info['label']}",
                "",
                f"- Question file: `{question_filename}`",
                f"- JEV CSV: [`{result_path.name}`](../results/{result_path.name})",
                f"- Rows: `{len(rows)}`",
                f"- Denominator: {target_info['denominator']}",
                f"- Source: [{target_info['source']}]({target_info['source']})",
                "",
                "| Option | JEV mean | IRL / target | Difference |",
                "|---|---:|---:|---:|",
            ]
        )
        for option in options:
            difference = averages[option] - actual[option]
            lines.append(
                f"| {option} | {percent(averages[option])} | {percent(actual[option])} | {difference:+.2f} pp |"
            )

        truth_field = target_info.get("truth_field")
        if truth_field:
            correct = sum(
                row["selected_answer"] == personas[row["persona_id"]][truth_field]
                for row in rows
            )
            lines.extend(
                [
                    "",
                    f"Persona-level selected-answer accuracy against the supplied `{truth_field}` field: "
                    f"`{correct / len(rows):.2%}`.",
                ]
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "The INSEE sections are profile-reading checks: the correct answer is",
            "already present in each persona row, while the aggregate target comes",
            "from the documented INSEE quota. They test whether JEV consumes the",
            "provided profile coherently; they are not independent opinion polls.",
            "",
            "The election sections are aggregate historical benchmarks. They are useful",
            "for measuring model/population mismatch, but fitting weights directly to",
            "one election can overfit. Use the SciPy calibration script only after",
            "checking weight bounds, effective sample size, and held-out questions or",
            "elections.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question-dir", type=Path, default=DEFAULT_QUESTION_DIR)
    parser.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--persona-csv", type=Path, default=DEFAULT_PERSONA_CSV)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = build_report(args.question_dir, args.result_dir, args.persona_csv)
    args.output.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote benchmark report to {args.output}")


if __name__ == "__main__":
    main()
