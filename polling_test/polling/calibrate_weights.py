#!/usr/bin/env python3
"""Find minimally changed persona weights with SciPy linear constraints."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, OptimizeResult, lsq_linear, minimize

from benchmark_targets import QUESTION_FILES, TARGETS
from compare_benchmarks import find_result
from poll_population import (
    parse_numbered_options,
    probability_columns,
    read_question,
    unique_options,
)


DEFAULT_QUESTION_DIR = Path(__file__).resolve().parents[1] / "questions"
DEFAULT_RESULT_DIR = Path(__file__).resolve().parents[1] / "results"
DEFAULT_PERSONA_CSV = Path(__file__).resolve().parents[1] / "population" / "population_sample.csv"
DEFAULT_OUTPUT = Path(__file__).with_name("calibrated_weights.csv")


def load_personas(persona_csv: Path) -> list[dict[str, str]]:
    with persona_csv.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def load_probabilities(
    result_path: Path,
    options: tuple[str, ...],
    persona_ids: list[str],
) -> np.ndarray:
    columns = probability_columns(options)
    with result_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if [row["persona_id"] for row in rows] != persona_ids:
        raise ValueError(f"Persona order does not match: {result_path}")
    matrix = np.array(
        [[float(row[columns[option]]) for option in options] for row in rows],
        dtype=float,
    )
    row_sums = matrix.sum(axis=1)
    if np.any(row_sums <= 0):
        raise ValueError(f"Non-positive probability row in: {result_path}")
    return matrix / row_sums[:, None]


def build_constraints(
    question_dir: Path,
    result_dir: Path,
    persona_ids: list[str],
    question_filenames: tuple[str, ...],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    constraint_columns: list[np.ndarray] = []
    constraint_targets: list[float] = []
    labels: list[str] = []
    for question_filename in question_filenames:
        question_id = Path(question_filename).stem
        target_info: dict[str, Any] = TARGETS[question_id]
        question_path = Path(question_filename)
        if not question_path.is_absolute() and not question_path.exists():
            question_path = question_dir / question_path
        question = read_question(question_path)
        options = unique_options(parse_numbered_options(question))
        result_path = find_result(result_dir, question)
        matrix = load_probabilities(result_path, options, persona_ids)
        if "balance_target" in target_info:
            positive = set(target_info["positive_options"])
            negative = set(target_info["negative_options"])
            balance = sum(
                (matrix[:, options.index(option)] for option in positive),
                start=np.zeros(len(persona_ids)),
            ) - sum(
                (matrix[:, options.index(option)] for option in negative),
                start=np.zeros(len(persona_ids)),
            )
            constraint_columns.append(balance)
            constraint_targets.append(float(target_info["balance_target"]) / 100.0)
            labels.append(f"{question_id}:balance")
            continue

        targets = target_info["targets_percent"]
        if set(options) != set(targets):
            raise ValueError(f"Target choices do not match question: {question_id}")
        normalized_targets = np.array([targets[option] for option in options], dtype=float)
        normalized_targets /= normalized_targets.sum()

        # The final option is redundant because each probability row and target
        # distribution sums to one. Dropping it avoids a dependent constraint.
        for index, option in enumerate(options[:-1]):
            constraint_columns.append(matrix[:, index])
            constraint_targets.append(float(normalized_targets[index]))
            labels.append(f"{question_id}:{option}")

    return (
        np.column_stack(constraint_columns),
        np.array(constraint_targets, dtype=float),
        labels,
    )


def solve_weights(
    probabilities: np.ndarray,
    targets: np.ndarray,
    lower: float,
    upper: float,
    hard: bool = False,
    penalty: float = 1_000_000.0,
) -> Any:
    """Minimize weight movement with soft targets or exact constraints."""
    count = probabilities.shape[0]
    normalized_constraints = np.vstack(
        [np.ones(count) / count, probabilities.T / count]
    )
    normalized_targets = np.concatenate(([1.0], targets))
    if not hard:
        scale = np.sqrt(penalty)
        return lsq_linear(
            np.vstack([np.eye(count), scale * normalized_constraints]),
            np.concatenate([np.ones(count), scale * normalized_targets]),
            bounds=(lower, upper),
            lsmr_tol="auto",
            max_iter=1000,
            verbose=0,
        )

    constraint_matrix = np.vstack([np.ones(count), probabilities.T])
    constraint_targets = np.concatenate(([count], count * targets))
    correction = constraint_targets - constraint_matrix @ np.ones(count)
    unconstrained = np.ones(count) + constraint_matrix.T @ np.linalg.pinv(
        constraint_matrix @ constraint_matrix.T
    ) @ correction
    if np.all(unconstrained >= lower - 1e-9) and np.all(unconstrained <= upper + 1e-9):
        return OptimizeResult(
            x=unconstrained,
            success=True,
            message="Solved by the equality-constrained minimum-norm projection",
        )

    objective = lambda weights: 0.5 * np.sum((weights - 1.0) ** 2)
    gradient = lambda weights: weights - 1.0
    constraints = [
        LinearConstraint(np.ones((1, count)), count, count),
        LinearConstraint(probabilities.T, count * targets, count * targets),
    ]
    return minimize(
        objective,
        np.clip(unconstrained, lower, upper),
        jac=gradient,
        method="SLSQP",
        bounds=Bounds(lower, upper),
        constraints=constraints,
        options={"ftol": 1e-10, "maxiter": 2000, "disp": False},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question-dir", type=Path, default=DEFAULT_QUESTION_DIR)
    parser.add_argument("--result-dir", type=Path, default=DEFAULT_RESULT_DIR)
    parser.add_argument("--persona-csv", type=Path, default=DEFAULT_PERSONA_CSV)
    parser.add_argument("--question-file", action="append", dest="question_files")
    parser.add_argument("--lower", type=float, default=0.5)
    parser.add_argument("--upper", type=float, default=2.0)
    parser.add_argument(
        "--hard",
        action="store_true",
        help="Require exact aggregate targets; default uses a bounded soft calibration.",
    )
    parser.add_argument(
        "--penalty",
        type=float,
        default=1_000_000.0,
        help="Soft target penalty (default: 1000000).",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not 0 < args.lower <= 1 <= args.upper:
        raise ValueError("Require 0 < LOWER <= 1 <= UPPER")

    question_filenames = tuple(args.question_files or QUESTION_FILES)
    personas = load_personas(args.persona_csv)
    persona_ids = [row["persona_id"] for row in personas]
    probabilities, targets, labels = build_constraints(
        args.question_dir, args.result_dir, persona_ids, question_filenames
    )
    result = solve_weights(
        probabilities,
        targets,
        args.lower,
        args.upper,
        hard=args.hard,
        penalty=args.penalty,
    )
    if not result.success:
        raise RuntimeError(
            f"SciPy could not find feasible weights: {result.message}. "
            "Try fewer calibration questions, wider bounds, or soft constraints."
        )

    weights = result.x
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=["persona_id", "weight"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(
            {"persona_id": persona_id, "weight": f"{weight:.12g}"}
            for persona_id, weight in zip(persona_ids, weights)
        )

    effective_sample_size = weights.sum() ** 2 / np.sum(weights**2)
    residuals = probabilities.T @ weights / len(weights) - targets
    print(f"Wrote weights to {args.output}")
    mode = "hard" if args.hard else f"soft (penalty={args.penalty:g})"
    print(f"Questions: {len(question_filenames)} | constraints: {len(labels)} | mode: {mode}")
    print(f"min_weight={weights.min():.6f} max_weight={weights.max():.6f} ESS={effective_sample_size:.2f}")
    print(f"max_absolute_target_residual={np.max(np.abs(residuals)):.12f}")


if __name__ == "__main__":
    main()
