#!/usr/bin/env python3
"""Benchmark JEV Choice against the gender-guesser Python library."""

from __future__ import annotations

import argparse
import asyncio
import csv
import html
import json
import random
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gender_guesser.detector import Detector
from typesafe_sdk import AsyncTypeSafeClient, Choice


DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_UNISEX_COUNT = 4
DEFAULT_SEED = 20260925
DEFAULT_CONCURRENCY = 12
DEFAULT_CSV_PATH = Path("gender_benchmark_results.csv")
DEFAULT_HTML_PATH = Path("gender_benchmark.html")
CHOICES = ("male", "female", "unisex")
LIBRARY_TO_LABEL = {
    "male": "male",
    "mostly_male": "male",
    "female": "female",
    "mostly_female": "female",
    "andy": "unisex",
}


@dataclass
class BenchmarkCase:
    index: int
    name: str
    library_gender: str


@dataclass
class BenchmarkResult:
    index: int
    name: str
    library_gender: str
    expected_gender: str
    predicted_gender: str
    male_probability: float
    female_probability: float
    unisex_probability: float
    confidence: float
    correct: bool
    error: str = ""


def build_sample(
    detector: Detector,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    unisex_count: int = DEFAULT_UNISEX_COUNT,
    seed: int = DEFAULT_SEED,
) -> list[BenchmarkCase]:
    """Build a random sample with a balanced binary subset and a few unisex names."""
    if sample_size < 1:
        raise ValueError("sample_size must be positive")
    if not 0 <= unisex_count < sample_size:
        raise ValueError("unisex_count must be between 0 and sample_size - 1")

    eligible: dict[str, list[str]] = {label: [] for label in CHOICES}
    for name in detector.names:
        library_gender = detector.get_gender(name)
        expected_gender = LIBRARY_TO_LABEL.get(library_gender)
        if expected_gender is not None:
            eligible[expected_gender].append(name)

    binary_count = sample_size - unisex_count
    male_count = binary_count // 2
    female_count = binary_count - male_count
    if len(eligible["male"]) < male_count:
        raise ValueError("gender-guesser does not contain enough male names")
    if len(eligible["female"]) < female_count:
        raise ValueError("gender-guesser does not contain enough female names")
    if len(eligible["unisex"]) < unisex_count:
        raise ValueError("gender-guesser does not contain enough unisex names")

    rng = random.Random(seed)
    cases = [
        BenchmarkCase(index=0, name=name, library_gender=detector.get_gender(name))
        for name in rng.sample(eligible["male"], male_count)
    ]
    cases.extend(
        BenchmarkCase(index=0, name=name, library_gender=detector.get_gender(name))
        for name in rng.sample(eligible["female"], female_count)
    )
    cases.extend(
        BenchmarkCase(index=0, name=name, library_gender=detector.get_gender(name))
        for name in rng.sample(eligible["unisex"], unisex_count)
    )
    rng.shuffle(cases)
    return [
        BenchmarkCase(index=index, name=case.name, library_gender=case.library_gender)
        for index, case in enumerate(cases, start=1)
    ]


def _choice_question() -> Choice:
    """Return the same Choice question used by the interactive example."""
    return Choice(
        instructions="Based only on the surname, what is the gender of this person?",
        criteria={
            "male": "male",
            "female": "female",
            "unisex": "unisex",
        },
    )


async def _classify_case(
    client: AsyncTypeSafeClient,
    case: BenchmarkCase,
    semaphore: asyncio.Semaphore,
) -> BenchmarkResult:
    async with semaphore:
        try:
            response = await client.system_one(
                state=case.name,
                questions={"gender": _choice_question()},
            )
            answer = response.answers["gender"]
            probabilities = answer.probabilities
            predicted_gender = str(answer.choice)
            return BenchmarkResult(
                index=case.index,
                name=case.name,
                library_gender=case.library_gender,
                expected_gender=LIBRARY_TO_LABEL[case.library_gender],
                predicted_gender=predicted_gender,
                male_probability=float(probabilities.get("male", 0.0)),
                female_probability=float(probabilities.get("female", 0.0)),
                unisex_probability=float(probabilities.get("unisex", 0.0)),
                confidence=float(answer.confidence),
                correct=(predicted_gender == LIBRARY_TO_LABEL[case.library_gender]),
            )
        except Exception as error:  # Keep one transient failure from losing the run.
            return BenchmarkResult(
                index=case.index,
                name=case.name,
                library_gender=case.library_gender,
                expected_gender=LIBRARY_TO_LABEL[case.library_gender],
                predicted_gender="error",
                male_probability=0.0,
                female_probability=0.0,
                unisex_probability=0.0,
                confidence=0.0,
                correct=False,
                error=f"{type(error).__name__}: {error}",
            )


async def run_benchmark(
    cases: list[BenchmarkCase], concurrency: int = DEFAULT_CONCURRENCY
) -> list[BenchmarkResult]:
    """Run one JEV Choice request per sampled name."""
    if concurrency < 1:
        raise ValueError("concurrency must be positive")
    semaphore = asyncio.Semaphore(concurrency)
    async with AsyncTypeSafeClient() as client:
        results = await asyncio.gather(
            *(_classify_case(client, case, semaphore) for case in cases)
        )
    return sorted(results, key=lambda result: result.index)


def _metrics(results: list[BenchmarkResult]) -> dict[str, Any]:
    evaluated = [result for result in results if not result.error]
    correct = sum(result.correct for result in evaluated)
    by_expected: dict[str, dict[str, int]] = {}
    for label in CHOICES:
        label_results = [result for result in evaluated if result.expected_gender == label]
        label_correct = sum(result.correct for result in label_results)
        by_expected[label] = {
            "count": len(label_results),
            "correct": label_correct,
            "accuracy_percent": (
                100 * label_correct / len(label_results) if label_results else 0.0
            ),
        }
    return {
        "total": len(results),
        "evaluated": len(evaluated),
        "errors": len(results) - len(evaluated),
        "correct": correct,
        "accuracy_percent": 100 * correct / len(evaluated) if evaluated else 0.0,
        "expected_counts": dict(Counter(result.expected_gender for result in results)),
        "prediction_counts": dict(Counter(result.predicted_gender for result in results)),
        "by_expected": by_expected,
    }


def write_csv(path: Path, results: list[BenchmarkResult]) -> None:
    """Write one inspectable row per benchmark request."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(results[0])) if results else list(BenchmarkResult.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def write_html(
    path: Path,
    results: list[BenchmarkResult],
    *,
    seed: int,
    unisex_count: int,
    concurrency: int,
    elapsed_seconds: float,
) -> None:
    """Write a standalone report with summary cards, a confusion matrix, and rows."""
    metrics = _metrics(results)
    escaped_rows = []
    for result in results:
        status = "correct" if result.correct else "incorrect"
        if result.error:
            status = "error"
        escaped_rows.append(
            "<tr data-status={status} data-expected={expected} data-predicted={predicted}>"
            "<td>{index}</td><td>{name}</td><td>{library_gender}</td>"
            "<td>{expected}</td><td>{predicted}</td>"
            "<td>{male}</td><td>{female}</td><td>{unisex}</td><td>{confidence}</td>"
            "<td><span class='badge {status}'>{status}</span>"
            "{error}</td></tr>".format(
                status=html.escape(status),
                expected=html.escape(result.expected_gender),
                predicted=html.escape(result.predicted_gender),
                index=result.index,
                name=html.escape(result.name),
                library_gender=html.escape(result.library_gender),
                male=f"{result.male_probability:.3f}",
                female=f"{result.female_probability:.3f}",
                unisex=f"{result.unisex_probability:.3f}",
                confidence=f"{result.confidence:.3f}",
                error=(
                    f"<details><summary>details</summary>{html.escape(result.error)}</details>"
                    if result.error
                    else ""
                ),
            )
        )

    by_expected = metrics["by_expected"]
    summary_cards = "".join(
        f"<div class='card'><div class='eyebrow'>{label.title()} accuracy</div>"
        f"<div class='metric'>{_format_percent(by_expected[label]['accuracy_percent'])}</div>"
        f"<div class='muted'>{by_expected[label]['correct']} / {by_expected[label]['count']}</div></div>"
        for label in CHOICES
    )
    report_data = json.dumps(
        {
            "metrics": metrics,
            "seed": seed,
            "unisex_count": unisex_count,
            "concurrency": concurrency,
            "elapsed_seconds": round(elapsed_seconds, 2),
        },
        sort_keys=True,
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JEV gender Choice benchmark</title>
  <style>
    :root {{ color-scheme: light; --ink:#19202a; --muted:#687386; --line:#dce2ea; --blue:#315efb; --green:#12805c; --red:#b42318; --amber:#a15c00; --wash:#f5f7fb; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:#fff; font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
    main {{ max-width:1320px; margin:0 auto; padding:48px 28px 72px; }}
    h1 {{ margin:0 0 8px; font-size:clamp(28px,4vw,46px); letter-spacing:-.04em; }} h2 {{ margin:36px 0 12px; font-size:21px; }}
    .lede {{ max-width:760px; color:var(--muted); font-size:17px; }} .meta {{ color:var(--muted); font-size:13px; margin:18px 0 28px; }}
    .cards {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }} .card {{ border:1px solid var(--line); border-radius:14px; padding:18px; background:linear-gradient(150deg,#fff,#fafbfe); }}
    .eyebrow {{ color:var(--muted); text-transform:uppercase; font-size:11px; font-weight:700; letter-spacing:.08em; }} .metric {{ margin-top:5px; font-size:32px; font-weight:750; letter-spacing:-.04em; }} .muted {{ color:var(--muted); }}
    .panel {{ border:1px solid var(--line); border-radius:14px; overflow:auto; }} .controls {{ display:flex; gap:10px; flex-wrap:wrap; margin:14px 0; }}
    input,select {{ border:1px solid var(--line); border-radius:9px; padding:9px 11px; color:var(--ink); background:white; font:inherit; }} input {{ min-width:240px; }}
    table {{ width:100%; min-width:980px; border-collapse:collapse; }} th,td {{ padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; white-space:nowrap; }} th {{ position:sticky; top:0; background:var(--wash); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }} tbody tr:hover {{ background:#fafbff; }}
    .badge {{ display:inline-block; border-radius:999px; padding:2px 8px; font-size:12px; font-weight:700; }} .correct {{ color:var(--green); background:#e7f7f0; }} .incorrect {{ color:var(--red); background:#fdecea; }} .error {{ color:var(--amber); background:#fff3d6; }}
    details {{ white-space:normal; max-width:380px; color:var(--red); }} footer {{ margin-top:30px; color:var(--muted); font-size:13px; }}
    @media (max-width:760px) {{ main {{ padding:30px 16px 48px; }} .cards {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} }}
  </style>
</head>
<body>
<main>
  <div class="eyebrow">TypeSafe / JEV Choice mode</div>
  <h1>Gender guesser benchmark</h1>
  <p class="lede">JEV was asked to classify 1,000 random names from the <code>gender-guesser</code> Python library using the same three-way Choice question as the interactive example.</p>
  <p class="meta">Balanced binary sample: 498 male + 498 female, plus {unisex_count} library-labeled unisex names · seed {seed} · concurrency {concurrency} · elapsed {elapsed_seconds:.1f}s · <a href="gender_benchmark_results.csv">raw CSV</a></p>
  <section class="cards">
    <div class="card"><div class="eyebrow">Overall accuracy</div><div class="metric">{_format_percent(metrics['accuracy_percent'])}</div><div class="muted">{metrics['correct']} / {metrics['evaluated']} evaluated</div></div>
    {summary_cards}
  </section>
  <h2>Results</h2>
  <div class="controls"><input id="search" type="search" placeholder="Filter by name or label…"><select id="status"><option value="all">All results</option><option value="correct">Correct</option><option value="incorrect">Incorrect</option><option value="error">Errors</option></select><span class="muted" id="count"></span></div>
  <div class="panel"><table><thead><tr><th>#</th><th>Name</th><th>Library result</th><th>Expected</th><th>JEV guess</th><th>P male</th><th>P female</th><th>P unisex</th><th>Confidence</th><th>Status</th></tr></thead><tbody id="results">{''.join(escaped_rows)}</tbody></table></div>
  <footer>Ground truth is the label returned by gender-guesser 0.4.0: male/female include the library's mostly_male/mostly_female labels, andy is treated as unisex. This is a benchmark against that library, not a claim about a person's actual gender.</footer>
</main>
<script>
  const rows = [...document.querySelectorAll('#results tr')]; const search = document.querySelector('#search'); const status = document.querySelector('#status'); const count = document.querySelector('#count');
  function refresh() {{ const query = search.value.toLowerCase(); const selected = status.value; let visible = 0; rows.forEach(row => {{ const matchesText = row.textContent.toLowerCase().includes(query); const matchesStatus = selected === 'all' || row.dataset.status === selected; row.hidden = !(matchesText && matchesStatus); if (!row.hidden) visible++; }}); count.textContent = `${{visible}} of ${{rows.length}} shown`; }}
  search.addEventListener('input', refresh); status.addEventListener('change', refresh); refresh();
  window.BENCHMARK = {report_data};
</script>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--unisex-count", type=int, default=DEFAULT_UNISEX_COUNT)
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH)
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    detector = Detector(case_sensitive=False)
    cases = build_sample(
        detector,
        sample_size=args.sample_size,
        unisex_count=args.unisex_count,
        seed=args.seed,
    )
    print(f"Running {len(cases)} JEV Choice requests with concurrency={args.concurrency}…")
    started = time.perf_counter()
    results = await run_benchmark(cases, concurrency=args.concurrency)
    elapsed_seconds = time.perf_counter() - started
    write_csv(args.csv, results)
    write_html(
        args.html,
        results,
        seed=args.seed,
        unisex_count=args.unisex_count,
        concurrency=args.concurrency,
        elapsed_seconds=elapsed_seconds,
    )
    metrics = _metrics(results)
    print(
        f"Saved {args.csv} and {args.html}; "
        f"accuracy={metrics['accuracy_percent']:.1f}% "
        f"({metrics['correct']}/{metrics['evaluated']}), errors={metrics['errors']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
