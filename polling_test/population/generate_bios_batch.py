"""Generate short persona biographies with the OpenAI Batch API."""

from __future__ import annotations

import argparse
import csv
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = Path(__file__).with_name("population_sample.csv")
DEFAULT_OUTPUT = Path(__file__).with_name("bio_results.csv")
DEFAULT_MODEL = "gpt-4o-mini"


def load_env_file(env_path: Path) -> None:
    """Load simple KEY=VALUE entries without overwriting shell variables."""

    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def build_prompt(persona: dict[str, str]) -> str:
    """Create the per-person prompt from all persona attributes."""

    return (
        "Write a concise, fictional two-line biography in English about a "
        f"{persona['sex']} person who is {persona['age']} years old "
        f"({persona['age_group']}) and lives in {persona['region']}. "
        f"They are classified as {persona['csp']} and live in an area classified "
        f"as {persona['urban_area_size']}. Use only facts supported by these "
        "attributes. Return exactly two lines, one complete sentence per line, "
        "with no heading, bullets, quotation marks, names, or invented specific facts."
    )


def read_personas(csv_path: Path, limit: int) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        required_fields = {
            "persona_id",
            "sex",
            "age",
            "age_group",
            "csp",
            "region",
            "urban_area_size",
        }
        missing_fields = required_fields - set(reader.fieldnames or [])
        if missing_fields:
            raise ValueError(f"CSV is missing required fields: {sorted(missing_fields)}")

        personas = [
            {field: row[field] or "" for field in required_fields}
            for row in reader
        ]

    if not personas:
        raise ValueError(f"CSV contains no personas: {csv_path}")
    if limit < 1:
        raise ValueError("--limit must be at least 1")
    return personas[:limit]


def write_batch_input(personas: list[dict[str, str]], model: str, path: Path) -> None:
    with path.open("w", encoding="utf-8") as batch_file:
        for persona in personas:
            request = {
                "custom_id": persona["persona_id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You write concise, grounded fictional biographies "
                                "from demographic attributes."
                            ),
                        },
                        {"role": "user", "content": build_prompt(persona)},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 120,
                },
            }
            batch_file.write(json.dumps(request, ensure_ascii=False) + "\n")


def normalize_bio(content: str) -> str:
    """Keep the requested two-line shape if the model adds extra blank lines."""

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) > 2:
        lines = lines[:2]
    return "\n".join(lines)


def submit_and_wait(
    client: OpenAI,
    input_path: Path,
    model: str,
    poll_seconds: int,
) -> tuple[str, dict[str, Any]]:
    with input_path.open("rb") as batch_file:
        uploaded_file = client.files.create(file=batch_file, purpose="batch")

    batch = client.batches.create(
        input_file_id=uploaded_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"source": input_path.name, "model": model},
    )
    print(f"Submitted batch: {batch.id}")

    while batch.status not in {"completed", "failed", "expired", "cancelled"}:
        time.sleep(poll_seconds)
        batch = client.batches.retrieve(batch.id)
        counts = batch.request_counts
        progress = ""
        if counts:
            progress = (
                f" ({counts.completed} completed, {counts.failed} failed, "
                f"{counts.total} total)"
            )
        print(f"Batch status: {batch.status}{progress}")

    batch_data = batch.model_dump()
    if batch.status != "completed":
        raise RuntimeError(
            f"Batch {batch.id} ended with status {batch.status}: "
            f"{json.dumps(batch_data.get('errors'), ensure_ascii=False)}"
        )
    if not batch.output_file_id:
        raise RuntimeError(f"Batch {batch.id} completed without an output file")
    return batch.id, batch_data


def collect_results(
    client: OpenAI,
    batch_id: str,
    batch_data: dict[str, Any],
    personas: list[dict[str, str]],
    output_path: Path | None,
) -> list[dict[str, str]]:
    output_content = client.files.content(batch_data["output_file_id"]).text
    results_by_id: dict[str, dict[str, str]] = {}

    for line in output_content.splitlines():
        result = json.loads(line)
        custom_id = result["custom_id"]
        response = result.get("response")
        if response and response.get("body"):
            choices = response["body"].get("choices", [])
            bio = normalize_bio(choices[0]["message"]["content"]) if choices else ""
            error = "" if bio else "No text returned by the model"
        else:
            error = json.dumps(result.get("error"), ensure_ascii=False)
            bio = ""
        results_by_id[custom_id] = {"bio": bio, "error": error}

    results: list[dict[str, str]] = []
    for persona in personas:
        result = {
            **persona,
            **results_by_id.get(
                persona["persona_id"],
                {"bio": "", "error": "No result returned for this persona"},
            ),
            "batch_id": batch_id,
        }
        results.append(result)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "persona_id",
            "sex",
            "age",
            "age_group",
            "csp",
            "region",
            "urban_area_size",
            "bio",
            "error",
            "batch_id",
        ]
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"Wrote results to {output_path}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="persona CSV path",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="number of personas to process (default: 5)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI chat model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV path for results; use --output /dev/null to skip useful persistence",
    )
    parser.add_argument(
        "--poll-seconds",
        type=int,
        default=10,
        help="seconds between batch status checks (default: 10)",
    )
    args = parser.parse_args()

    if args.poll_seconds < 1:
        raise ValueError("--poll-seconds must be at least 1")

    load_env_file(PROJECT_ROOT / ".env")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to .env or export it in the shell."
        )

    personas = read_personas(args.input, args.limit)
    client = OpenAI(api_key=api_key)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".jsonl",
        prefix="population_batch_",
        delete=False,
    ) as temporary_file:
        input_path = Path(temporary_file.name)

    try:
        write_batch_input(personas, args.model, input_path)
        batch_id, batch_data = submit_and_wait(
            client, input_path, args.model, args.poll_seconds
        )
        results = collect_results(client, batch_id, batch_data, personas, args.output)
    finally:
        input_path.unlink(missing_ok=True)

    print("\nResults:")
    for result in results:
        print(f"\n{result['persona_id']}")
        print(result["bio"] or f"ERROR: {result['error']}")


if __name__ == "__main__":
    main()
