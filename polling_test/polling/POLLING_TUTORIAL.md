# JEV polling tutorial

This example uses TypeSafe's JEV model to estimate a probability distribution over fixed survey answer choices for each persona in the population CSV.

The implementation is [`poll_population.py`](poll_population.py). It uses the TypeSafe Python SDK and the [`Choice`](https://docs.typesafe.ai/primitives/choice.md) primitive: JEV returns the most likely answer plus a probability for every allowed answer.

## Project files

```text
polling_test/
├── population/
│   └── population_sample.csv
└── polling/
    ├── poll_population.py
    └── POLLING_TUTORIAL.md
```

The CSV currently has these columns:

```text
persona_id, sex, age, age_group, csp, region, urban_area_size,
country, population_profile, context_version, activity_status, occupation,
household, housing, transport, routine, interest, tradeoff, bio
```

See [population model and assumptions](../population/population_sampling.md) for
local generation, validation, custom sizes and country profiles. The bios describe
explicit fictional scenarios, whose frequencies are not census-calibrated.

`persona_id` is used only to label the output. It is deliberately excluded from the context sent to JEV.

## Setup

Use Python 3.10 or newer and install the project dependencies if needed:

```bash
./.venv/bin/pip install -r requirements.txt
```

Set the API key in the environment. Do not put the key in this file or commit it:

```bash
export TYPESAFE_API_KEY="your-key-here"
```

The `make` targets also load a local `.env` file automatically. Keep that file
untracked and never commit an API key.

## Run the default example

From the project root:

```bash
./.venv/bin/python polling_test/polling/poll_population.py
```

The default run:

- reads the first five rows of `polling_test/population/population_sample.csv`;
- asks the Q7-style question about concern regarding the situation in Ukraine;
- uses these answer choices:

  ```text
  Très inquiet
  Plutôt inquiet
  Pas vraiment inquiet
  Pas du tout inquiet
  ```

- calls JEV once per persona;
- prints each persona context and its answer probability mapping.

Example output shape:

```text
persona_id | persona context | answer probabilities
fr_0001    | {"sex": "male", "age": "50", ...} | {"Plutôt inquiet": 0.81, "Très inquiet": 0.04, ...}
```

The probabilities are numbers from `0` to `1` and should sum to `1` for each persona.

## Run a question from a text file and write CSV results

Put the question and its numbered answer choices in a UTF-8 text file. The poller
uses the numbered lines as the `Choice` criteria, removes exact duplicate choices,
and writes one row per persona. The `persona_id` column remains available for a
later join, while each answer gets a `probability_*` column.

From the project root:

```bash
make poll \
  QUESTION_FILE=polling_test/questions/q3_presidential_2022.txt \
  LIMIT=1000
```

`LIMIT=0` evaluates every persona in the input CSV. Results are written under
`polling_test/results/` with a UTC timestamp followed by a slug made from the
first 200 characters of the question, for example:

```text
20260926T193004123456Z_q3-si-le-premier-tour-de-lelection-presidentielle....csv
```

Because the timestamp is the filename prefix, ordinary filename sorting orders
the result files chronologically. Override the input persona CSV with `CSV=...`
by invoking the Python script directly, or pass `OUTPUT_DIR=...` to `make poll`.

## Cost-aware historical and INSEE benchmark batch

Run the full benchmark set with:

```bash
make benchmark-poll LIMIT=1000
make compare-benchmarks
```

The batch contains the 2012, 2017 and 2022 first-round election questions,
five profile questions based on the INSEE-controlled fields in the synthetic
population, and three independent INSEE Camme opinion questions. The Camme
questions compare JEV-derived opinion balances with the published July 2026
INSEE balances. All uncached questions for one persona are sent in one
TypeSafe request. Each question still gets its own CSV, and the embedded
question and population hashes let later runs reuse matching CSVs without making
another paid request. The population hash covers the ordered input records for the chosen context mode,
so changing a characteristic or bio invalidates the old result automatically.

To deliberately rerun the complete benchmark after changing the population,
bios, or question files, use:

```bash
make validate-population
make benchmark-poll LIMIT=1000 FORCE=1
make compare-benchmarks
```

`FORCE=1` preserves older timestamped CSVs and writes a new result set. Without
it, matching cached results are reused. Older inference versions and older populations are treated as stale. Comparison
and calibration require matching fingerprints, so retained historical result files
cannot be joined to regenerated personas simply because their IDs match.

`make compare-benchmarks` is unweighted by default, which is the appropriate
baseline for comparing population changes. To inspect an explicit calibration,
first regenerate it for the current result set and opt in:

```bash
make calibrate-weights
make compare-benchmarks WEIGHTS=polling_test/polling/calibrated_weights_all.csv
```

Do not carry calibrated weights across a population or question change without
regenerating them; they are a diagnostic layer, not part of JEV inference.

The SciPy calibration diagnostic uses bounded soft constraints by default:

```bash
make calibrate-weights
```

It writes persona weights, reports the effective sample size, and keeps the
unweighted CSVs unchanged. Use `--hard` directly with
`polling_test/polling/calibrate_weights.py` only when exact constraints are
known to be feasible.

## What is sent to JEV?

For each CSV row, the script separates `persona.demographics` from
`persona.fictional_context` in structured state. A simulation-frame description
explains the status of those fields. `persona_id`, `population_profile`,
`context_version`, `batch_id` and `error` are excluded from the persona state.
Structured persona fields take precedence over prose.

Questions use a typed `Choice` with the original survey question and explicit
persona-perspective instructions. All independent questions share one state and
one request. Use `--demographics-only` (or `DEMOGRAPHICS_ONLY=1` with make) to
exclude fictional detail. This baseline has a separate cache fingerprint. Pass
the same flag to comparison and calibration scripts.

The code reads the returned distribution with:

```python
result.choices["answer"].probabilities
```

The key `answer` is an internal question name used by the Python code. It is not part of the persona context.

## Ask a different question

Use `--question` and repeat `--option` once per allowed answer:

```bash
./.venv/bin/python polling_test/polling/poll_population.py \
  --limit 5 \
  --question "Quel candidat choisirait probablement cette personne au premier tour ?" \
  --option "Philippe POUTOU" \
  --option "Jean-Luc MELENCHON" \
  --option "Emmanuel MACRON" \
  --option "Marine LE PEN" \
  --option "Éric ZEMMOUR" \
  --option "Vous voteriez blanc" \
  --option "Vous n'iriez pas voter"
```

Use at least two options. The question should describe one narrow choice, and the options should cover the answers you want JEV to compare.

## Change the number of personas

The default is five rows. To test ten rows:

```bash
./.venv/bin/python polling_test/polling/poll_population.py --limit 10
```

To evaluate the full CSV, first check its row count, then pass that count as `--limit`:

```bash
tail -n +2 polling_test/population/population_sample.csv | wc -l
./.venv/bin/python polling_test/polling/poll_population.py --limit N
```

Each persona causes one API request, so larger runs use more time and API quota.

## Use another CSV path

The path can be overridden with `--csv`:

```bash
./.venv/bin/python polling_test/polling/poll_population.py \
  --csv path/to/another_population.csv \
  --limit 5
```

The replacement CSV must contain a `persona_id` column. Demographic fields and fictional context are separated; operational metadata
is excluded. Extra user-defined columns become fictional context.

When testing a changed replacement CSV at the same persona IDs, add `--force`
to guarantee a fresh paid run. The normal cache check now fingerprints all
persona fields, including `bio`.

## Resuming tests later

When continuing this work, start from the project root and run:

```bash
export TYPESAFE_API_KEY="your-key-here"
./.venv/bin/python polling_test/polling/poll_population.py --limit 5
```

For a small fresh smoke test, add `--force`; for the full benchmark use the
`make benchmark-poll LIMIT=1000 FORCE=1` command above. Keep `persona_id` out of
the model state, and treat the returned probabilities as model judgments to
inspect and validate, not as measured survey results.

For the current SDK request shape, see the [TypeSafe Python SDK documentation](https://docs.typesafe.ai/sdk/python.md) and the [Choice primitive documentation](https://docs.typesafe.ai/primitives/choice.md).
