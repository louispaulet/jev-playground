# Synthetic population, version 2

The checked-in CSV contains 1,000 fictional **adult residents of France excluding
Mayotte**. Its demographic quotas are controlled. Its life stories are conditional
scenarios, not measured characteristics of the French population. Richer stories
make the experiment inspectable; they do not establish better opinion predictions.

## Generate and inspect

From the repository root, without an API key or an API request:

```bash
make generate-population
make validate-population

# A separate population at another size and seed
make generate-population SIZE=5000 SEED=42 CSV=/tmp/france_5000.csv
make validate-population CSV=/tmp/france_5000.csv
.venv/bin/python -m polling_test.population.validate_population_sample \
  /tmp/france_5000.csv --report /tmp/france_margin_deviations.csv

# Offline regressions (some other tests/ files are interactive API demos)
.venv/bin/python -m unittest tests.test_population tests.test_poll_population tests.test_poll_benchmarks
```

The legacy `generate_bios_batch.py` still targets the earlier demographic-only
schema. Use the local generator for v2 populations; the optional OpenAI rewriter
has not yet been migrated to preserve the new context fields.

Generation also writes a `.manifest.json` beside the CSV, containing the full
profile, source links, seed, size, schema version and modeling assumptions. Keep
it with exported CSVs. Validation uses that profile and size, or explicit
`--profile` / `--size` arguments when no manifest is available.

## Demographic controls and evidence

The profile is [profiles/france.json](profiles/france.json). Category order matters
for matrix columns and is validated before allocation.

| Control | Reference | Qualification |
| --- | --- | --- |
| Sex × adult age group; adult region totals | [INSEE estimates, 1 January 2025](https://www.insee.fr/fr/statistiques/8331297) | 18–19 approximated as 2/5 of 15–19; Mayotte excluded |
| National CSP and regional CSP | [INSEE RP2022 current or previous social group](https://www.insee.fr/fr/statistiques/2012701) | Published 15+ population is a proxy for 18+ |
| National urban-unit size | [INSEE urban units](https://www.insee.fr/fr/statistiques/5039853) | 2017 all-age counts, 2020 geography; contextual proxy |
| Age × CSP, age × region, region × CSP, region × urbanity | Existing experiment's balanced integer controls, retained in the profile | Derived/adjusted controls, not a complete observed joint population; see [the earlier audit](joint_distribution_comparison.md) |
| Individual age within an adult band | INSEE 2025 workbook, sheet `2025`, regional male/female five-year counts | Drawn conditionally on region and sex, uniform within a five-year band; 95+ represented by 95 |

The source workbook for age detail is
[estim-pop-nreg-sexe-aq-1975-2025.xlsx](https://www.insee.fr/fr/statistiques/fichier/8331297/estim-pop-nreg-sexe-aq-1975-2025.xlsx).
`age_band_counts` stores 17 counts per region and sex, from 15–19 to 95+.
For men these are source columns Z–AP; for women AU–BK. The source label
`Centre-Val-de-Loire` is normalized to the existing CSV label `Centre-Val de Loire`.
Keeping this snapshot makes generation offline and independent of future source edits.

The integer solver fits age × region × CSP to the retained pairwise tables. Its
starting point is conditional independence of age and region within CSP. It does
not recover unobserved higher-order relationships. Sex is allocated within age
bands; sex × CSP and sex × region are not controlled.

At the reference size (1,000), all five pairwise controls are exact. At other
sizes, largest-remainder allocation scales the fitted cells within age groups,
then scales sex within age and urbanity within region. Sample size and structural
zeros are preserved, but every source margin cannot be promised exact after
rounding. The validator checks the effective allocations and reports one-way
percentage-point deviations from the reference profile. Small samples may omit
rare groups entirely. No sampling-error confidence intervals are implied.

## Persona schema and fictional life details

The first seven columns preserve the original join and demographic fields:
`persona_id`, `sex`, `age`, `age_group`, `csp`, `region`, `urban_area_size`.
`country`, `population_profile` and `context_version` identify the scenario.

| Added field | Role | Coherence rule |
| --- | --- | --- |
| `activity_status` | Working, looking for work, retired, student, inactive | Distinct from current/previous CSP; retirement and studies have explicit scenario age rules |
| `occupation` | Current or previous professional domain | Drawn within CSP; retirees get a fictional former occupation; students/inactive use `not_applicable` |
| `household`, `housing` | Household arrangement and tenure situation | Parental household/colocation/children at home have configured age ranges; housing comes from household-compatible options |
| `transport` | Usual transport | Drawn from settlement-specific options; no assumption of urban transit in rural scenarios |
| `routine` | Concrete weekly constraint | Drawn from activity-specific situations |
| `interest` | Personal leisure interest | Shared pool across sexes and social groups to avoid prescribing demographic tastes |
| `tradeoff` | Everyday tension in organizing time or spending | Shared pool; no invented party, vote, religion or political stance |
| `bio` | French paragraph describing those exact fields | Rendered locally from profile templates; structured fields remain authoritative |

**All context probabilities are illustrative.** Working/job-search scenarios use
92/8 weights in occupational CSPs. Young other-inactive scenarios use 75/25
student/inactive weights up to age 29. Compatible households, housing, transport,
routines, interests and tradeoffs are selected uniformly. Former occupational
domains of retirees use the active CSP quotas as illustrative weights, not an
estimate of actual former occupations. These settings are editable in the profile.

Additional scenario restrictions: retirement begins at 60; occupational CSPs are
restricted to ages up to 79; professions with long training have minimum ages
(e.g. general medicine 28). These deliberately simplify reality and are **not
legal retirement rules or demographic estimates**. They also condition the
within-band age draws, which are not independently quota-controlled. Real people
can fall outside these restrictions; future data-backed profiles should replace
them with appropriate joint distributions.

Random streams for demographics and context are separate. Changing a biography
template cannot alter the demographic draws. Reproducibility assumes the same
profile, seed and solver version; integer optima may have ties across solver versions.
Persona IDs are stable only within one generated population. A population hash,
rather than the ID alone, identifies an experiment.

## Adapting to another population

Copy the JSON profile and supply it via `PROFILE=path/to/profile.json` or
`--profile`. Replace the country, scope, source links, category labels, balanced
reference counts, age ranges, conditional occupation/activity/household rules,
settlement descriptions, location phrases and biography templates. Optional
`age_band_counts` follows the five-year format above; omit it to use uniform
within-band ages. Category keys and array ordering must agree across all tables.
The sampler and renderer contain no French prose or hard-coded region names.
The initial schema still describes adults with social groups, regions and
urbanity; extending the dimensions themselves requires a deliberate schema change.

## Polling and evaluating assumptions

The poller sends demographics and fictional context in separately named JSON
fields, using [TypeSafe's structured state](https://docs.typesafe.ai/concepts/state)
and [Choice](https://docs.typesafe.ai/primitives/choice). Identifiers and batch
metadata stay outside persona state. Survey instructions ask for the persona's
perspective without inventing prior votes or party identity.

Compare full-context predictions with the demographic-only baseline:

```bash
make benchmark-poll CSV=polling_test/population/population_sample.csv
make compare-benchmarks
make benchmark-poll DEMOGRAPHICS_ONLY=1 OUTPUT_DIR=/tmp/demographic_polls
make compare-benchmarks DEMOGRAPHICS_ONLY=1 OUTPUT_DIR=/tmp/demographic_polls
```

These commands make paid JEV requests when matching caches are absent. No new
live opinion benchmark was run as part of regenerating the local CSV. Historical
results and calibration weights remain historical artifacts: the tools reject
results or weights that do not match the current population/context mode.
Changing the polling instruction version also invalidates cached results.

This frame contains residents, not registered voters. Nationality, eligibility,
turnout, income and education are absent; historical election comparisons remain
exploratory diagnostics with a denominator mismatch. Neither the bios nor JEV
probabilities are observations of human opinion. Assess added context on held-out
surveys and across seeds, without fitting persona stories to benchmark answers.
