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
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gender_guesser.detector import Detector
from typesafe_sdk import AsyncTypeSafeClient, Choice


DEFAULT_SAMPLE_SIZE = 1000
DEFAULT_UNISEX_COUNT = 4
DEFAULT_SEED = 20260925
DEFAULT_CONCURRENCY = 12
DEFAULT_MIN_GEO_SUPPORT = 400
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
REGION_COUNTRIES = {
    "Europe": {
        "great_britain",
        "ireland",
        "italy",
        "malta",
        "portugal",
        "spain",
        "france",
        "belgium",
        "luxembourg",
        "the_netherlands",
        "east_frisia",
        "germany",
        "austria",
        "swiss",
        "iceland",
        "denmark",
        "norway",
        "sweden",
        "finland",
        "estonia",
        "latvia",
        "lithuania",
        "poland",
        "czech_republic",
        "slovakia",
        "hungary",
        "romania",
        "bulgaria",
        "bosniaand",
        "croatia",
        "kosovo",
        "macedonia",
        "montenegro",
        "serbia",
        "slovenia",
        "albania",
        "greece",
        "russia",
        "belarus",
        "moldova",
        "ukraine",
    },
    "North America": {"usa"},
    "Caucasus": {"armenia", "azerbaijan", "georgia"},
    "Central Asia": {"the_stans"},
    "Middle East": {"turkey", "arabia", "israel"},
    "Asia": {"china", "india", "japan", "korea", "vietnam"},
    "Other": {"other_countries"},
}
COUNTRY_TO_REGION = {
    country: region
    for region, countries in REGION_COUNTRIES.items()
    for country in countries
}
REGION_ORDER = tuple(REGION_COUNTRIES) + ("Mixed/ambiguous", "Unspecified")
SUPPORTED_GEO_REGIONS = (
    "Europe",
    "North America",
    "Middle East",
    "Asia",
    "Mixed/ambiguous",
)


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
    library_geo_region: str = "Unspecified"
    library_geo_countries: str = ""
    library_geo_signal_count: int = 0


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


def region_support_gaps(
    results: list[BenchmarkResult], min_geo_support: int
) -> dict[str, int]:
    """Return missing evaluated rows for the regions supported by the dataset."""
    if min_geo_support < 1:
        raise ValueError("min_geo_support must be positive")
    support = region_support_counts(results)
    return {
        region: max(0, min_geo_support - support[region])
        for region in SUPPORTED_GEO_REGIONS
    }


def region_support_counts(results: list[BenchmarkResult]) -> Counter[str]:
    """Count evaluated rows in the regions supported by the dataset."""
    return Counter(
        result.library_geo_region
        for result in results
        if not result.error and result.library_geo_region in SUPPORTED_GEO_REGIONS
    )


def build_region_augmentation_sample(
    results: list[BenchmarkResult],
    detector: Detector,
    min_geo_support: int = DEFAULT_MIN_GEO_SUPPORT,
    seed: int = DEFAULT_SEED,
) -> list[BenchmarkCase]:
    """Build only the missing binary cases needed to reach regional support."""
    gaps = region_support_gaps(results, min_geo_support)
    existing_names = {result.name.casefold() for result in results}
    eligible: dict[str, dict[str, list[tuple[str, str]]]] = {
        region: {label: [] for label in ("male", "female")}
        for region in SUPPORTED_GEO_REGIONS
    }
    for name in detector.names:
        if name.casefold() in existing_names:
            continue
        library_gender = detector.get_gender(name)
        expected_gender = LIBRARY_TO_LABEL.get(library_gender)
        if expected_gender not in {"male", "female"}:
            continue
        region, _ = geo_metadata(detector, name)
        if region in eligible:
            eligible[region][expected_gender].append((name, library_gender))

    rng = random.Random(seed)
    selected: list[tuple[str, str]] = []
    for region in SUPPORTED_GEO_REGIONS:
        gap = gaps[region]
        male_count = gap // 2
        female_count = gap - male_count
        for label, count in (("male", male_count), ("female", female_count)):
            pool = sorted(eligible[region][label], key=lambda item: item[0].casefold())
            if len(pool) < count:
                raise ValueError(
                    f"gender-guesser does not contain {count} unused {label} names "
                    f"for {region}; found {len(pool)}"
                )
            selected.extend(rng.sample(pool, count))

    rng.shuffle(selected)
    first_index = max((result.index for result in results), default=0) + 1
    return [
        BenchmarkCase(index=index, name=name, library_gender=library_gender)
        for index, (name, library_gender) in enumerate(selected, start=first_index)
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


def geo_metadata(detector: Detector, name: str) -> tuple[str, list[str]]:
    """Return broad regions and country signals encoded by gender-guesser."""
    countries = [
        country
        for country in detector.COUNTRIES
        if detector.get_gender(name, country) not in {"andy", "unknown"}
    ]
    regions = {
        COUNTRY_TO_REGION[country]
        for country in countries
        if country in COUNTRY_TO_REGION
    }
    if not regions:
        region = "Unspecified"
    elif len(regions) == 1:
        region = next(iter(regions))
    else:
        region = "Mixed/ambiguous"
    return region, countries


def add_geo_metadata(
    results: list[BenchmarkResult], detector: Detector
) -> list[BenchmarkResult]:
    """Add country-specific library signals without making new JEV requests."""
    annotated = []
    for result in results:
        region, countries = geo_metadata(detector, result.name)
        annotated.append(
            replace(
                result,
                library_geo_region=region,
                library_geo_countries="|".join(countries),
                library_geo_signal_count=len(countries),
            )
        )
    return annotated


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


def _label_metrics(
    evaluated: list[BenchmarkResult], label: str
) -> dict[str, int | float]:
    true_positive = sum(
        result.expected_gender == label and result.predicted_gender == label
        for result in evaluated
    )
    false_positive = sum(
        result.expected_gender != label and result.predicted_gender == label
        for result in evaluated
    )
    false_negative = sum(
        result.expected_gender == label and result.predicted_gender != label
        for result in evaluated
    )
    support = sum(result.expected_gender == label for result in evaluated)
    precision_percent = (
        100 * true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )
    recall_percent = (
        100 * true_positive / support if support else 0.0
    )
    return {
        "count": support,
        "correct": true_positive,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "accuracy_percent": 100 * true_positive / support if support else 0.0,
        "precision_percent": precision_percent,
        "recall_percent": recall_percent,
    }


def _metrics(results: list[BenchmarkResult]) -> dict[str, Any]:
    evaluated = [result for result in results if not result.error]
    correct = sum(result.correct for result in evaluated)
    by_expected: dict[str, dict[str, int | float]] = {}
    for label in CHOICES:
        by_expected[label] = _label_metrics(evaluated, label)
    by_geo_region: dict[str, dict[str, int | float]] = {}
    regions = sorted(
        {result.library_geo_region for result in results},
        key=lambda region: REGION_ORDER.index(region)
        if region in REGION_ORDER
        else len(REGION_ORDER),
    )
    for region in regions:
        region_results = [
            result for result in evaluated if result.library_geo_region == region
        ]
        region_labels = [_label_metrics(region_results, label) for label in CHOICES]
        by_geo_region[region] = {
            "count": len(region_results),
            "correct": sum(result.correct for result in region_results),
            "accuracy_percent": (
                100 * sum(result.correct for result in region_results) / len(region_results)
                if region_results
                else 0.0
            ),
            "macro_precision_percent": sum(
                item["precision_percent"] for item in region_labels
            )
            / len(region_labels),
            "macro_recall_percent": sum(
                item["recall_percent"] for item in region_labels
            )
            / len(region_labels),
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
        "by_geo_region": by_geo_region,
    }


def write_csv(path: Path, results: list[BenchmarkResult]) -> None:
    """Write one inspectable row per benchmark request."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(results[0])) if results else list(BenchmarkResult.__annotations__)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(result) for result in results)


def load_csv(path: Path, detector: Detector | None = None) -> list[BenchmarkResult]:
    """Load benchmark results without making any new JEV requests."""
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if rows and (
        "library_geo_region" not in rows[0]
        or "library_geo_countries" not in rows[0]
    ):
        detector = detector or Detector(case_sensitive=False)
    results = []
    for row in rows:
        geo_region = row.get("library_geo_region", "")
        geo_countries = row.get("library_geo_countries", "")
        if detector and not geo_region:
            geo_region, countries = geo_metadata(detector, row["name"])
            geo_countries = "|".join(countries)
        geo_signal_count = int(row.get("library_geo_signal_count") or len(
            [country for country in geo_countries.split("|") if country]
        ))
        results.append(
            BenchmarkResult(
                index=int(row["index"]),
                name=row["name"],
                library_gender=row["library_gender"],
                expected_gender=row["expected_gender"],
                predicted_gender=row["predicted_gender"],
                male_probability=float(row["male_probability"]),
                female_probability=float(row["female_probability"]),
                unisex_probability=float(row["unisex_probability"]),
                confidence=float(row["confidence"]),
                correct=row["correct"].casefold() == "true",
                error=row.get("error", ""),
                library_geo_region=geo_region or "Unspecified",
                library_geo_countries=geo_countries,
                library_geo_signal_count=geo_signal_count,
            )
        )
    return results


def _format_percent(value: float) -> str:
    return f"{value:.1f}%"


def write_html(
    path: Path,
    results: list[BenchmarkResult],
    *,
    seed: int,
    unisex_count: int,
    concurrency: int,
    elapsed_seconds: float | None,
    run_note: str = "",
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
            "<td>{geo_region}</td><td>{geo_countries}</td>"
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
                geo_region=html.escape(result.library_geo_region),
                geo_countries=html.escape(result.library_geo_countries.replace("|", ", "))
                or "—",
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
    expected_counts = metrics["expected_counts"]
    male_count = expected_counts.get("male", 0)
    female_count = expected_counts.get("female", 0)
    actual_unisex_count = expected_counts.get("unisex", unisex_count)
    report_metadata = (
        f"Sample: {male_count} male + {female_count} female, plus "
        f"{actual_unisex_count} library-labeled unisex names · seed {seed}"
    )
    if elapsed_seconds is not None:
        report_metadata += (
            f" · concurrency {concurrency} · elapsed {elapsed_seconds:.1f}s"
        )
    if run_note:
        report_metadata += f" · {html.escape(run_note)}"
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
            "elapsed_seconds": (
                round(elapsed_seconds, 2) if elapsed_seconds is not None else None
            ),
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
  <p class="lede">JEV was asked to classify {metrics['total']:,} names from the <code>gender-guesser</code> Python library using the same three-way Choice question as the interactive example.</p>
  <p class="meta">{report_metadata} · <a href="gender_benchmark_results.csv">raw CSV</a></p>
  <section class="cards">
    <div class="card"><div class="eyebrow">Overall accuracy</div><div class="metric">{_format_percent(metrics['accuracy_percent'])}</div><div class="muted">{metrics['correct']} / {metrics['evaluated']} evaluated</div></div>
    {summary_cards}
  </section>
  <h2>Precision &amp; recall by gender</h2>
  <div class="panel"><table><thead><tr><th>Gender</th><th>Support</th><th>Precision</th><th>Recall</th><th>True positives</th><th>False positives</th><th>False negatives</th></tr></thead><tbody>{''.join(
      f"<tr><td>{label.title()}</td><td>{by_expected[label]['count']}</td>"
      f"<td>{_format_percent(by_expected[label]['precision_percent'])}</td>"
      f"<td>{_format_percent(by_expected[label]['recall_percent'])}</td>"
      f"<td>{by_expected[label]['true_positive']}</td>"
      f"<td>{by_expected[label]['false_positive']}</td>"
      f"<td>{by_expected[label]['false_negative']}</td></tr>"
      for label in CHOICES
  )}</tbody></table></div>
  <h2>Precision, recall &amp; accuracy by region</h2>
  <p class="muted">Precision and recall are macro-averaged across male, female, and unisex. Regions come from country-specific gender-guesser signals; multiple regions are labeled mixed/ambiguous, and no signal is unspecified. These are name-dataset segments, not claims about a person's origin.</p>
  <div class="panel"><table><thead><tr><th>Region</th><th>Support</th><th>Accuracy</th><th>Macro precision</th><th>Macro recall</th><th>Correct</th></tr></thead><tbody>{''.join(
      f"<tr><td>{html.escape(region)}</td><td>{values['count']}</td>"
      f"<td>{_format_percent(values['accuracy_percent'])}</td>"
      f"<td>{_format_percent(values['macro_precision_percent'])}</td>"
      f"<td>{_format_percent(values['macro_recall_percent'])}</td>"
      f"<td>{values['correct']}</td></tr>"
      for region, values in metrics['by_geo_region'].items()
  )}</tbody></table></div>
  <h2>Results</h2>
  <div class="controls"><input id="search" type="search" placeholder="Filter by name or label…"><select id="status"><option value="all">All results</option><option value="correct">Correct</option><option value="incorrect">Incorrect</option><option value="error">Errors</option></select><span class="muted" id="count"></span></div>
  <div class="panel"><table><thead><tr><th>#</th><th>Name</th><th>Library result</th><th>Geo region</th><th>Country signals</th><th>Expected</th><th>JEV guess</th><th>P male</th><th>P female</th><th>P unisex</th><th>Confidence</th><th>Status</th></tr></thead><tbody id="results">{''.join(escaped_rows)}</tbody></table></div>
  <footer>Ground truth is the label returned by gender-guesser 0.4.0: male/female include the library's mostly_male/mostly_female labels, andy is treated as unisex. Country signals are the countries where gender-guesser returns a gender-specific value rather than andy; they do not establish a person's actual gender or geographic origin.</footer>
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
    parser.add_argument(
        "--augment-regions",
        action="store_true",
        help="call JEV only for names missing from the supported regional targets",
    )
    parser.add_argument(
        "--min-geo-support",
        type=int,
        default=DEFAULT_MIN_GEO_SUPPORT,
        help="minimum evaluated rows per supported region when augmenting",
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="regenerate the HTML from --csv without making JEV requests",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    if args.report_only and args.augment_regions:
        raise SystemExit("--report-only and --augment-regions cannot be combined")

    detector = Detector(case_sensitive=False)
    if args.report_only:
        results = add_geo_metadata(load_csv(args.csv, detector), detector)
        write_csv(args.csv, results)
        write_html(
            args.html,
            results,
            seed=args.seed,
            unisex_count=args.unisex_count,
            concurrency=args.concurrency,
            elapsed_seconds=None,
            run_note="report regenerated from the existing CSV; no benchmark requests made",
        )
        metrics = _metrics(results)
        print(
            f"Regenerated {args.html} from {args.csv}; "
            f"accuracy={metrics['accuracy_percent']:.1f}% "
            f"({metrics['correct']}/{metrics['evaluated']}), errors={metrics['errors']}"
        )
        return

    if args.augment_regions:
        existing_results = add_geo_metadata(load_csv(args.csv, detector), detector)
        gaps = region_support_gaps(existing_results, args.min_geo_support)
        cases = build_region_augmentation_sample(
            existing_results,
            detector,
            min_geo_support=args.min_geo_support,
            seed=args.seed,
        )
        support = region_support_counts(existing_results)
        print(
            "Existing evaluated regional support: "
            + ", ".join(
                f"{region}={support[region]} (+{gaps[region]} needed)"
                for region, gap in gaps.items()
            )
        )
        print(
            f"Running {len(cases)} additional JEV Choice requests with "
            f"concurrency={args.concurrency}…"
        )
        started = time.perf_counter()
        additions = await run_benchmark(cases, concurrency=args.concurrency)
        retry_cases = [
            BenchmarkCase(
                index=result.index,
                name=result.name,
                library_gender=result.library_gender,
            )
            for result in additions
            if result.error
        ]
        if retry_cases:
            print(f"Retrying {len(retry_cases)} failed incremental requests…")
            retry_results = await run_benchmark(
                retry_cases, concurrency=args.concurrency
            )
            by_index = {result.index: result for result in additions}
            by_index.update({result.index: result for result in retry_results})
            additions = [by_index[index] for index in sorted(by_index)]
        elapsed_seconds = time.perf_counter() - started
        results = add_geo_metadata(existing_results + additions, detector)
        write_csv(args.csv, results)
        write_html(
            args.html,
            results,
            seed=args.seed,
            unisex_count=args.unisex_count,
            concurrency=args.concurrency,
            elapsed_seconds=elapsed_seconds,
            run_note=(
                f"incremental regional enrichment; {len(cases)} new names requested "
                f"(target >= {args.min_geo_support} support in five viable regions)"
            ),
        )
        metrics = _metrics(results)
        print(
            f"Saved {args.csv} and {args.html}; "
            f"accuracy={metrics['accuracy_percent']:.1f}% "
            f"({metrics['correct']}/{metrics['evaluated']}), errors={metrics['errors']}"
        )
        return

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
    results = add_geo_metadata(results, detector)
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
