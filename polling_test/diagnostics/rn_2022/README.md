# RN diagnostic: current personas versus the 2022 first round

Analysis completed 5 October 2026, using the 4 October poll of the new 1,000-person
population. No new paid inference calls were made. All percentages below concern
Marine Le Pen alone unless explicitly stated otherwise.

## Finding

The principal discrepancy is within-group vote estimation, rather than simply an
incorrect rural/urban population mix. JEV predicts 2.68% RN among candidate votes,
versus the official 23.15%. The equivalent official share for our geographic scope
(metropolitan France and four DOM, excluding Mayotte, collectivities and citizens
abroad) is 23.41%. Adding Zemmour does not resolve the gap: 2.94% simulated versus
30.23% nationally. These are retrospective diagnostic comparisons, not forecasts.

## Geography

Official municipal first-round results, divided by valid candidate votes:

| Commune | Le Pen | Zemmour | Combined |
|---|---:|---:|---:|
| Paris | 5.54% | 8.16% | 13.70% |
| Rennes | 7.29% | 4.48% | 11.77% |
| Nantes | 8.13% | 6.15% | 14.28% |
| Lyon | 8.99% | 7.65% | 16.64% |
| Lille | 11.77% | 4.42% | 16.20% |
| Roubaix | 14.51% | 3.24% | 17.75% |
| Marseille | 20.89% | 11.10% | 31.99% |
| Nice | 22.44% | 14.28% | 36.72% |
| Perpignan | 27.38% | 9.61% | 36.99% |
| Béziers | 31.08% | 10.61% | 41.69% |
| Calais | 39.65% | 5.54% | 45.20% |
| Hénin-Beaumont | 51.32% | 4.41% | 55.73% |

These deliberately contrasting examples are not a representative sample of cities.
Urbanity alone does not determine municipal support. Aggregate votes cannot establish
which individual residents voted RN. There is no commune field in the personas:
none of the city rows above has a corresponding simulated municipal result.

The matched comparison uses the INSEE 2020 urban-unit classification in 2022 geography,
with population-size categories based on 2017 population. The current INSEE historical
download includes corrections published in 2025. “Rural” here means outside an urban
unit; it is not the separate INSEE density-grid rural definition. Paris urban unit
contains 407 communes in this crosswalk, and is distinct from both Paris city and
Île-de-France.

| Comparable category | Personas | Official RN | JEV RN |
|---|---:|---:|---:|
| Paris urban unit | 162 | 11.14% | 1.02% |
| Other urban units, 100,000–1,999,999 | 309 | 20.90% | 2.79% |
| Urban units, 20,000–99,999 | 141 | 24.81% | 2.72% |
| Urban units under 20,000 | 180 | 27.26% | 3.33% |
| Outside urban units | 208 | 29.38% | 3.50% |

The model gets the broad rural/Paris direction right, while understating support
everywhere. Replacing the distribution of candidate-vote mass across these five
categories with the official distribution, keeping simulated category RN rates
fixed, gives only 2.82%. This is an accounting counterfactual, not a causal estimate.

Regional ordering also fails in places. Bretagne is 19.53% official / 3.61% JEV;
PACA 27.60% / 2.43%; Hauts-de-France 33.34% / 4.70%; Île-de-France 12.97% / 1.22%.
See all 17 comparisons in `region.csv`. Tiny regional samples (e.g. Corse: six
personas; Guyane: four) should not support detailed regional inference.

## Demographics and turnout

Ipsos/Sopra Steria's 2022 survey finds RN support of 36% among workers and employees,
12% among managers, 24% among intermediate professions, and 17% among retirees.
Our corresponding estimates are 5.24%, 2.45%, 0.54%, 1.16%, and 3.90%. CSP mapping
is approximate: our category can describe a current or previous social group.

Matched age bands show a wrong gradient: ages 50–59 have 30% survey / 2.93% JEV;
ages 70+ have 13% / 4.04%. The survey's education contrast is 35% below bac versus
13% at bac+3 or above. Education is completely absent from our personas. Household
income and prior voting history are also absent. These are associations, not
evidence that changing one characteristic causes a person to vote RN.

The survey consists of 4,000 registered adults, online fieldwork 6–9 April 2022,
quota sampling. It is pre-election survey evidence, not administrative demographic
vote counts; sampling and measurement uncertainty applies. Its percentages describe
support within each group, not the composition of the RN electorate.

A later Ipsos/Talan survey for the 2024 legislative first round corroborates the
worker/education patterns: RN and allies score 57% among workers, 21% among managers,
49% below bac and 22% at bac+3+. This is a different election and coalition; these
numbers are not calibration targets for the presidential question.

Simulated abstention is 45.90%, against 26.31% officially. Candidate-only normalization
already removes abstention and blank/null options, yet the RN discrepancy persists.
Holding the simulated conditional RN rate fixed and using the official valid-vote
participation rate yields 1.93% of registered voters, still far below the official
16.69%. Our original 1.23% of all personas has a different denominator from registered
voters, so it should not be presented as a direct electoral estimate.

## What the simulation lacks, and what to change next

1. **An election-specific frame.** The profile represents 2025 adult residents,
   not registered citizens in 2022. The 2022 question says “dimanche prochain” without
   a year, so current inference over old candidates is not a historical reconstruction.
   Define the election date, electorate, eligibility and relevant contemporary context.
2. **Local geography and joint social context.** Add INSEE commune identifiers,
   urban-unit and density definitions, education, income/financial pressure,
   employment status and prior occupation for retirees. Generate their joint
   distribution from evidence; independent demographic draws can produce false
   combinations. Validate finer age×CSP distributions: the existing sampler uses
   five-year INSEE counts, conditioned on occupational age restrictions, but only
   the broader age groups are quota-controlled. Keep geographic mappings and survey
   sources in configurable country profiles.
3. **Political heterogeneity.** Sample a sourced joint distribution of political
   attitudes and past behaviour where survey microdata permits; do not infer an
   individual's actual preferences from their address or occupation. A commuting
   routine or hobby provides little evidence for this missing variation.
4. **Validated vote and turnout models.** Treat eligibility, participation and
   conditional party choice separately. Test JEV against an empirical baseline and
   evaluate calibration by age, occupation, education and place. A scalar national
   RN correction would leave wrong age and regional relationships intact. Validate
   on held-out elections and locations; do not feed the held-out election's result
   into persona construction and then call matching it a prediction.
5. **A controlled biography check.** The fictional details are explicitly uncalibrated.
   Compare the same personas with demographics alone and with bios, then vary temporal
   framing separately. These diagnostics do not establish that hobbies, biographies,
   prompt wording or JEV training are the cause of the gap; those require experiments.

The existing quotas are useful population controls, but matching census marginals
does not validate synthetic political opinions. This diagnostic measures discrepancies;
it does not silently alter or calibrate the population or existing poll.

## Reproduce and inspect

```sh
.venv/bin/python polling_test/polling/diagnose_rn.py
```

`communes.csv` contains all 34,932 matched communes in the profile's geographic scope.
`selected_cities.csv`, `urban_area_size.csv`, `region.csv`, `age_survey.csv`, `csp.csv`
and `sex.csv` contain inspectable comparisons. `manifest.json` records input hashes,
source URLs, coverage and denominator definitions. The script verifies the cached
question/population fingerprint and joins personas one-to-one. It checks all 12
candidates sum to expressed votes in each official row; national totals match the
Ministry's figures; all scoped communes join to INSEE exactly once; and sums match
each official region. Every simulation cut uses sum(RN probabilities) /
sum(candidate probabilities), not argmax votes or mean individual ratios. No sampling
confidence intervals are attached to synthetic model judgments.

Raw sources are cached under ignored `.cache/rn_diagnostics`. The INSEE XLSX has an
invalid color stylesheet for openpyxl; the script reads its original cell-value XML,
without modifying the source. Normalized rounded model outputs are the archived
poll's exported probabilities. The run used `jev-latest`; a resolved model revision
was not recorded, limiting exact future inference reproduction.

Sources:

- [Official definitive first-round municipal and regional results](https://www.data.gouv.fr/fr/datasets/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour/)
- [Ministry national results](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php)
- [INSEE urban-unit crosswalks](https://www.insee.fr/fr/information/4802589)
- [Ipsos/Sopra Steria 2022 sociology](https://www.ipsos.com/fr-fr/presidentielle-2022/1er-tour-abstentionnistes-sociologie-electorat), PDF pages 4–9 for demographics
- [Ipsos/Talan 2024 sociology](https://www.ipsos.com/fr-fr/legislatives-2024/sociologie-des-electorats-legislatives-2024), PDF pages 6 and 8 for profession and education
- [Population profile](../../population/profiles/france.json) and [persona generation](../../population/personas.py)
- [Archived run](../../polling/PRESIDENTIAL_RUN_20261004.md)
