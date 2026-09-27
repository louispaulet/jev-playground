# Fresh JEV run comparison: updated population

This comparison covers the complete 11-question benchmark on 1,000 personas.

- Previous run: the complete `20260926T2035`/`20260926T2049` result set, run before the latest population and bio update.
- Fresh run: the `20260927T2011` result set, forced against the current `population_sample.csv` with the updated characteristics and bios.
- Model: `jev-latest`, with all 11 independent questions sent together for each persona.
- Election error: mean absolute error across answer options, in percentage points of registered voters.
- Camme error: absolute error on the published opinion balance, in percentage points.

The full fresh-run distributions and IRL target for every option are in
[`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md).

## Summary

| Benchmark | Previous error | Fresh error | Change |
|---|---:|---:|---:|
| 2012 first round | 4.75 pp | 3.51 pp | **-1.24 pp** |
| 2017 first round | 4.62 pp | 3.12 pp | **-1.50 pp** |
| 2022 first round | 4.17 pp | 3.22 pp | **-0.95 pp** |
| Mean across elections | 4.51 pp | 3.28 pp | **-1.23 pp (-27%)** |
| Camme: personal finances | 21.01 pp | 15.12 pp | **-5.89 pp** |
| Camme: major purchases | 27.50 pp | 40.43 pp | +12.93 pp |
| Camme: unemployment | 47.70 pp | 37.83 pp | **-9.88 pp** |
| Mean Camme balance error | 32.07 pp | 31.12 pp | **-0.95 pp** |

The five profile-reading checks went from 9.8%–49.4% selected-answer accuracy
in the previous run to 100.0% in the fresh run. These are coherence checks, not
independent opinion benchmarks: the answer is explicitly present in the persona
profile, and the new bios restate the updated attributes more faithfully.

## Election results: fresh run versus IRL

The fresh run improved the aggregate distribution error in all three elections,
but it still has substantial systematic bias.

| Election | Fresh JEV leading option | IRL leading option | Fresh JEV | IRL |
|---|---|---|---:|---:|
| 2012 | François HOLLANDE | François HOLLANDE | 41.86% | 22.32% |
| 2017 | Emmanuel MACRON | Vous n'iriez pas voter | 35.93% | 22.23% |
| 2022 | Vous n'iriez pas voter | Vous n'iriez pas voter | 34.14% | 26.31% |

Notable movements versus the previous run:

- 2012: Marine LE PEN rose from 4.31% to 7.87% toward the 13.95% IRL result; François HOLLANDE fell from 47.55% to 41.86%, but remains 19.54 pp too high.
- 2017: Emmanuel MACRON fell from 45.75% to 35.93% toward 18.19%; Marine LE PEN rose from 9.75% to 17.52% against 16.14% IRL; abstention rose from 13.53% to 16.62% against 22.23% IRL.
- 2022: Marine LE PEN rose from 2.83% to 7.09% toward 16.69%, and Jean-Luc MELENCHON rose from 4.19% to 6.24% toward 15.82%; both remain materially underpredicted.

The official first-round targets are taken from the French Ministry of the
Interior archives for [2012](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php),
[2017](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php),
and [2022](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php).

## INSEE Camme results: fresh run versus July 2026

| Question balance | Fresh JEV | INSEE target | Error |
|---|---:|---:|---:|
| Personal financial situation: improve − deteriorate | +1.12 pp | -14.00 pp | +15.12 pp |
| Opportunity for major purchases: favorable − unfavorable | -76.43 pp | -36.00 pp | -40.43 pp |
| Unemployment: increase − decrease | +17.18 pp | +55.00 pp | -37.83 pp |

The targets are the July 2026 INSEE balances, not raw response percentages;
the fresh report applies the same balance definitions to JEV probabilities.

## Bottom line

The new population and bios moved JEV materially closer to the historical
election distributions: the mean election error fell by 27%, and every election
improved. The update also fixed profile-reading coherence. It did not solve the
main opinion calibration problem: JEV still over-concentrates on a few plausible
options, especially Hollande in 2012, Macron in 2017, and abstention in 2022;
the major-purchases balance also moved farther from INSEE.

The INSEE reference is [the July 2026 household confidence release](https://www.insee.fr/fr/statistiques/9031846).
