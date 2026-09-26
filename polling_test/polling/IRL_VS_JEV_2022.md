# 2022 first-round results: IRL versus JEV

> Historical note: this file records the original run before the null-ballot
> option was added. The corrected 2022 run, plus the 2012/2017 and INSEE
> benchmarks, is maintained in [`BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md).

This note records the comparison for the question in
[`q3_presidential_2022.txt`](../questions/q3_presidential_2022.txt) and the
1,000-persona result in the timestamped CSV under [`../results/`](../results/).

The relevant real-world election is the first round of the French presidential
election on 10 April 2022. The official Ministry of the Interior archive reports
both percentages of registered voters (`% inscrits`) and percentages of
expressed votes (`% exprimés`):

[Official 2022 first-round results](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php)

## Comparison

JEV values below are the mean probability across the 1,000 personas. The IRL
column uses `% inscrits`, which is the closest denominator because the JEV
question includes both an abstention option and a blank-ballot option.

| Option | JEV mean probability | IRL `% inscrits` | Difference (JEV - IRL) |
|---|---:|---:|---:|
| Philippe POUTOU | 0.15% | 0.55% | -0.40 pp |
| Nathalie ARTHAUD | 0.02% | 0.40% | -0.38 pp |
| Fabien ROUSSEL | 1.64% | 1.65% | -0.01 pp |
| Jean-Luc MELENCHON | 4.43% | 15.82% | -11.39 pp |
| Anne HIDALGO | 3.48% | 1.26% | +2.22 pp |
| Yannick JADOT | 7.51% | 3.34% | +4.17 pp |
| Emmanuel MACRON | 18.70% | 20.07% | -1.37 pp |
| Valérie PECRESSE | 11.24% | 3.44% | +7.80 pp |
| Jean LASSALLE | 8.55% | 2.26% | +6.29 pp |
| Nicolas DUPONT-AIGNAN | 2.18% | 1.49% | +0.69 pp |
| Marine LE PEN | 2.38% | 16.69% | -14.31 pp |
| Éric ZEMMOUR | 0.22% | 5.10% | -4.88 pp |
| Vous voteriez blanc | 3.88% | 1.12% | +2.76 pp |
| Vous n'iriez pas voter | 35.54% | 26.31% | +9.23 pp |

The official first-round result also reports 0.51% of registered voters casting
null ballots. The current JEV question has no null-ballot option, so the table
cannot align all categories exactly. If exact accounting is required, add
`Vous voteriez nul` as a separate option and rerun the poll; alternatively,
combine blank and null ballots in both datasets.

## What calibration can and cannot do

Reweighting can change the influence of existing personas while leaving every
persona's JEV probabilities and selected answer untouched. It cannot create
missing types of personas or correct a systematic JEV response bias that is
present in every subgroup. It is therefore useful as a benchmark-alignment
layer, not as evidence that the underlying individual answers became more true.

For this experiment, calibrating directly to the 2022 election would be a
post-hoc fit. It is reasonable as a diagnostic, but too early to call it a
general calibration method from one question and one election. A stronger test
would use several historical questions with known outcomes, fit weights on a
training set, and evaluate on held-out questions or a held-out election/wave.
The questions should include different topics and different turnout levels.

## Recommended optimization formulation

Use the probability columns, rather than only `selected_answer`, because the
probabilities retain more information and make the aggregate constraints smooth.
Let:

- `p[i, c]` be persona `i`'s JEV probability for option `c`;
- `w[i]` be that persona's calibration weight;
- `t[c]` be the IRL target share for option `c` on the same denominator;
- `N` be the number of personas.

A minimal-change calibration can solve:

```text
minimize    sum_i (w[i] - 1)^2
subject to  sum_i w[i] = N
            sum_i w[i] * p[i, c] = N * t[c]  for every calibrated option c
            lower_bound <= w[i] <= upper_bound
```

The objective keeps weights close to their original value of `1`. The sum
constraint preserves the original nominal sample size. Bounds prevent a small
number of personas from carrying the whole result. Start with a conservative
range such as `0.5 <= w[i] <= 2.0`, then inspect whether the targets are
feasible. Always report the effective sample size:

```text
ESS = (sum_i w[i])^2 / sum_i w[i]^2
```

If exact matching is too restrictive, replace the equality constraints with
small tolerances or add a penalty for target error. That is preferable to
silently accepting extreme weights.

## Python library recommendation

Use **CVXPY** for the first implementation. It makes variables, bounds, linear
constraints, and convex objectives explicit. Its `kl_div` atom is documented as
convex, so an entropy-style objective is also available:

```python
w = cp.Variable(n)
objective = cp.Minimize(cp.sum(cp.kl_div(w, np.ones(n))))
constraints = [
    w >= 0.5,
    w <= 2.0,
    cp.sum(w) == n,
    probabilities.T @ w == n * targets,
]
problem = cp.Problem(objective, constraints)
problem.solve()
```

The quadratic objective above is easier to explain; the KL objective is a good
second variant when preserving the original weighting distribution in an
entropy-balancing sense matters. CVXPY documents `kl_div` as convex and supports
convex optimization modeling directly: [CVXPY functions](https://www.cvxpy.org/tutorial/functions/index.html).

**SciPy** is a good lighter-weight alternative if we only need this one smooth
problem: `scipy.optimize.minimize` supports bounds, and `LinearConstraint` can
express the equality constraints. The official documentation covers both
interfaces: [`minimize`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html)
and [`LinearConstraint`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.LinearConstraint.html).
I would choose CVXPY first because it makes feasibility and convexity easier to
audit; I would use OR-Tools only if we later need discrete/integer weights or
other combinatorial constraints.

## Suggested validation sequence

1. Add the null-ballot option, or explicitly combine blank and null.
2. Fit weights to this question only as a diagnostic and report weight bounds,
   maximum weight, minimum weight, and ESS.
3. Repeat for several historical questions before choosing a production
   weighting rule.
4. Use leave-one-question-out or leave-one-election-out validation.
5. Compare unweighted and weighted results; keep the weighting only if it
   improves held-out error without materially collapsing ESS.
