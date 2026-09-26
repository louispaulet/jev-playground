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
persona_id, sex, age, age_group, csp, region, urban_area_size, bio
```

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

## What is sent to JEV?

For each CSV row, the script builds this state:

```python
{
    "persona": {
        "sex": "male",
        "age": "50",
        "age_group": "50-64",
        "csp": "worker",
        "region": "Auvergne-Rhône-Alpes",
        "urban_area_size": "urban_unit_100k_to_1_999_999",
        "bio": "...",
    }
}
```

The `persona_id` field is not included. The question is sent as a typed Choice:

```python
Choice(
    instructions="Votre question ici",
    criteria={
        "Answer A": None,
        "Answer B": None,
        "Answer C": None,
    },
)
```

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

The replacement CSV must contain a `persona_id` column. All other columns are passed through as persona context.

## Resuming tests later

When continuing this work, start from the project root and run:

```bash
export TYPESAFE_API_KEY="your-key-here"
./.venv/bin/python polling_test/polling/poll_population.py --limit 5
```

Then change only the question and options as needed. Keep `persona_id` out of the model state, and treat the returned probabilities as model judgments to inspect and validate, not as measured survey results.

For the current SDK request shape, see the [TypeSafe Python SDK documentation](https://docs.typesafe.ai/sdk/python.md) and the [Choice primitive documentation](https://docs.typesafe.ai/primitives/choice.md).
