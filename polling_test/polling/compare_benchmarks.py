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


def load_weights(weights_path: Path) -> dict[str, float]:
    with weights_path.open(newline="", encoding="utf-8") as csv_file:
        return {row["persona_id"]: float(row["weight"]) for row in csv.DictReader(csv_file)}


def percent(value: float) -> str:
    return f"{value:.2f}%"


def build_report(
    question_dir: Path,
    result_dir: Path,
    persona_csv: Path,
    weights_path: Path | None = None,
) -> str:
    personas = load_personas(persona_csv)
    weights = load_weights(weights_path) if weights_path else None
    ordered_weights = [weights[persona_id] for persona_id in personas] if weights else None
    lines = [
        "# JEV benchmark results versus IRL targets",
        "",
        "This report compares the cached JEV probability distributions with known",
        "French election results, INSEE-controlled margins, and independent INSEE",
        "Camme opinion balances. All benchmark questions were batched into one JEV",
        "request per persona, and each question's response was saved as its own CSV.",
        "",
        "JEV values are mean probabilities across the personas. Differences are",
        "JEV minus IRL, in percentage points. Election targets use registered voters",
        "as the denominator, so abstention, blank and null options remain comparable.",
        "",
    ]
    if ordered_weights:
        effective_sample_size = sum(ordered_weights) ** 2 / sum(weight**2 for weight in ordered_weights)
        lines.extend(
            [
                f"A weighted diagnostic is also shown using [`{weights_path.name}`]({weights_path.name}).",
                f"Weight range: `{min(ordered_weights):.3f}`–`{max(ordered_weights):.3f}`; effective sample size: `{effective_sample_size:.1f}`.",
                "",
            ]
        )

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
        weighted_averages = (
            {
                option: sum(
                    weight * float(row[columns[option]])
                    for weight, row in zip(ordered_weights, rows)
                )
                / sum(ordered_weights)
                * 100
                for option in options
            }
            if ordered_weights
            else None
        )
        lines.extend(
            [
                f"## {target_info['label']}",
                "",
                f"- Question file: `{question_filename}`",
                f"- JEV CSV: [`{result_path.name}`](../results/{result_path.name})",
                f"- Rows: `{len(rows)}`",
                f"- Denominator: {target_info['denominator']}",
                f"- Source: [{target_info['source']}]({target_info['source']})",
            ]
        )
        if target_info.get("reference_period"):
            lines.append(f"- Reference period: `{target_info['reference_period']}`")

        if "balance_target" in target_info:
            positive = set(target_info["positive_options"])
            negative = set(target_info["negative_options"])
            balance = sum(averages[option] for option in positive) - sum(
                averages[option] for option in negative
            )
            weighted_balance = (
                sum(weighted_averages[option] for option in positive)
                - sum(weighted_averages[option] for option in negative)
                if weighted_averages
                else None
            )
            lines.extend(
                [
                    "",
                    f"- Balance definition: {target_info['balance_definition']}",
                    "",
                    "| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |",
                    "|---|---:|---:|---:|---:|---:|",
                    f"| Opinion balance | {balance:+.2f} pp | "
                    f"{weighted_balance:+.2f} pp | "
                    f"{target_info['balance_target']:+.2f} pp | "
                    f"{balance - target_info['balance_target']:+.2f} pp | "
                    f"{weighted_balance - target_info['balance_target']:+.2f} pp |"
                    if weighted_balance is not None
                    else f"| Opinion balance | {balance:+.2f} pp | n/a | "
                    f"{target_info['balance_target']:+.2f} pp | "
                    f"{balance - target_info['balance_target']:+.2f} pp | n/a |",
                    "",
                    "JEV response probabilities:",
                    "",
                    "| Option | JEV mean | JEV weighted |",
                    "|---|---:|---:|",
                ]
            )
            for option in options:
                lines.append(
                    f"| {option} | {percent(averages[option])} | "
                    f"{percent(weighted_averages[option]) if weighted_averages else 'n/a'} |"
                )
            lines.append("")
            continue

        actual = target_info["targets_percent"]
        lines.extend(
            [
                "",
                "| Option | JEV mean | IRL / target | Difference |",
                "|---|---:|---:|---:|",
            ]
        )
        if weighted_averages:
            lines[-2:] = [
                "| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        for option in options:
            difference = averages[option] - actual[option]
            if weighted_averages:
                weighted_difference = weighted_averages[option] - actual[option]
                lines.append(
                    f"| {option} | {percent(averages[option])} | {percent(weighted_averages[option])} | "
                    f"{percent(actual[option])} | {difference:+.2f} pp | {weighted_difference:+.2f} pp |"
                )
            else:
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
            "The INSEE-controlled demographic sections are profile-reading checks:",
            "the correct answer is already present in each persona row, while the",
            "aggregate target comes from the documented INSEE quota. They test",
            "whether JEV consumes the provided profile coherently; they are not",
            "independent opinion polls.",
            "",
            "The INSEE Camme sections are independent opinion benchmarks. INSEE's",
            "July 2026 release publishes opinion balances rather than every raw",
            "response share, so the report compares the same positive-minus-negative",
            "balance computed from JEV probabilities with the published balance.",
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
    parser.add_argument("--weights", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = build_report(args.question_dir, args.result_dir, args.persona_csv, args.weights)
    args.output.write_text(report.rstrip() + "\n", encoding="utf-8")
    print(f"Wrote benchmark report to {args.output}")


if __name__ == "__main__":
    main()
