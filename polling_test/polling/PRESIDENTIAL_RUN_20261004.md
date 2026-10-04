# Presidential JEV run — 4 October 2026

Fresh full-context inference on the refactored French population: **1,000 personas, four questionnaires, 4,000 Choice distributions**. All four questions were grouped into one request per persona (1,000 successful persona requests). No calibration weights were applied.

Model requested: `jev-latest`. The existing runner does not retain the resolved model revision or token usage; these cannot be reconstructed from the result CSVs.

Population: [`population_sample.csv`](../population/population_sample.csv), profile `fr_adults_v2`, context `fr_daily_life_v2`.
Population fingerprint: `c84a91b29949b6cdfc8711fdf3eb866002cb11917b74dad5ac368dac377135d7`.
Input CSV SHA-256: `753e49276b8b1b5a7ba50b1c0146809149758af7580c69349ab302cd32b95899`.

An initial 1,000-person attempt failed during export because the validator required an exact probability total. A 10-person diagnostic identified rounded totals of 0.99. The validator was repaired and the full run repeated with per-person raw checkpoints. This report covers only that completed rerun; 2,010 successful logical persona requests were made across the initial attempt, diagnostic and rerun (transport retries and token usage are not retained).

## Main findings

The richer population does **not** yield a historically accurate election simulation in this run. Using all-persona shares, Hollande reaches 46.78% in the 2012 scenario versus 22.32% of registered voters in the official result; Macron reaches 36.32% in 2017 versus 18.19%. For the 2022 candidate list, Le Pen receives 1.23% versus 16.69%, while abstention reaches 45.90% versus 26.31%. The population-frame and question-wording differences above limit these comparisons, but the deviations remain large.

In the prospective scenario, abstention is 34.84% and “another candidate” is the largest candidate option at 15.76%. Gabriel Attal is the highest named option at 10.26%, followed by the grouped social-democratic primary option at 9.52%. These results give no basis for presenting the prospective scenario as a reliable forecast.

## How to read the results

JEV share is 100 × the unweighted mean probability across all 1,000 personas. It includes abstention, blank and null answers. Candidate-only shares divide each candidate’s mean probability by the sum over candidate options; they are **not** the shares among all personas. Selected-answer counts are not used for aggregation.

Historical reference columns are official first-round percentages of registered voters. Differences are JEV minus reference, in percentage points. This comparison has a population-frame mismatch: the synthetic sample represents current adult residents excluding Mayotte, not registered voters at each election. The 2012 and 2017 questions are explicitly hypothetical reruns; the 2022 file uses its candidate list with “Sunday next” wording. Present ages and fictional life details are not historical biographies.

The prospective questionnaire is the existing candidate scenario, including grouped alternatives. It is not a claim that those are declared candidates, a measured opinion poll, or a validated electoral forecast. The population scenarios and polling instructions also changed in the refactor, so this run alone cannot isolate the effect of richer biographies.

## French presidential election 2012, first round

Question: `presidential_2012_first_round.txt`.
Exported distributions (normalized): [20261004T192353700548Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv](../results/20261004_presidential_v2/20261004T192353700548Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv).
Validated rows: 1000; sum of mean probabilities: 100.000000%.
Original probability sums ranged from 0.990000 to 1.000000; 72 rounded distributions required normalization. Original sums are retained in the CSV, and original values in the raw JSONL checkpoint.

Candidate answers: **77.72%**; abstention: **20.04%**; blank/null: **2.23%**.

Mean absolute option error: **4.85 pp**. Largest discrepancy: **François HOLLANDE**, +24.46 pp.

Reference: [Ministry of the Interior, official results](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php).

| Answer | JEV, all personas | Official, registered voters | Difference | JEV, candidate-only |
| --- | ---: | ---: | ---: | ---: |
| François HOLLANDE | 46.78% | 22.32% | +24.46 pp | 60.19% |
| Vous n'iriez pas voter | 20.04% | 20.52% | -0.47 pp | — |
| François BAYROU | 7.98% | 7.12% | +0.86 pp | 10.27% |
| Jean-Luc MELENCHON | 7.83% | 8.66% | -0.83 pp | 10.08% |
| Nicolas SARKOZY | 6.75% | 21.19% | -14.44 pp | 8.69% |
| Eva JOLY | 4.60% | 1.80% | +2.80 pp | 5.91% |
| Vous voteriez blanc ou nul | 2.23% | 1.52% | +0.71 pp | — |
| Marine LE PEN | 2.10% | 13.95% | -11.85 pp | 2.70% |
| Nicolas DUPONT-AIGNAN | 0.62% | 1.40% | -0.78 pp | 0.80% |
| Jacques CHEMINADE | 0.45% | 0.19% | +0.26 pp | 0.58% |
| Philippe POUTOU | 0.34% | 0.89% | -0.56 pp | 0.43% |
| Nathalie ARTHAUD | 0.28% | 0.44% | -0.16 pp | 0.36% |

## French presidential election 2017, first round

Question: `presidential_2017_first_round.txt`.
Exported distributions (normalized): [20261004T192353727930Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv](../results/20261004_presidential_v2/20261004T192353727930Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv).
Validated rows: 1000; sum of mean probabilities: 100.000000%.
Original probability sums ranged from 0.990000 to 1.000000; 73 rounded distributions required normalization. Original sums are retained in the CSV, and original values in the raw JSONL checkpoint.

Candidate answers: **73.76%**; abstention: **21.94%**; blank/null: **4.31%**.

Mean absolute option error: **3.69 pp**. Largest discrepancy: **Emmanuel MACRON**, +18.13 pp.

Reference: [Ministry of the Interior, official results](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php).

| Answer | JEV, all personas | Official, registered voters | Difference | JEV, candidate-only |
| --- | ---: | ---: | ---: | ---: |
| Emmanuel MACRON | 36.32% | 18.19% | +18.13 pp | 49.25% |
| Vous n'iriez pas voter | 21.94% | 22.23% | -0.29 pp | — |
| Jean-Luc MELENCHON | 9.67% | 14.84% | -5.17 pp | 13.11% |
| François FILLON | 7.05% | 15.16% | -8.11 pp | 9.56% |
| Marine LE PEN | 6.34% | 16.14% | -9.80 pp | 8.60% |
| Benoît HAMON | 6.22% | 4.82% | +1.40 pp | 8.43% |
| Jean LASSALLE | 4.38% | 0.91% | +3.47 pp | 5.94% |
| Vous voteriez blanc | 3.41% | 1.39% | +2.02 pp | — |
| Nicolas DUPONT-AIGNAN | 2.30% | 3.56% | -1.26 pp | 3.12% |
| Vous voteriez nul | 0.90% | 0.61% | +0.29 pp | — |
| Jacques CHEMINADE | 0.63% | 0.14% | +0.49 pp | 0.85% |
| Philippe POUTOU | 0.37% | 0.83% | -0.46 pp | 0.50% |
| François ASSELINEAU | 0.28% | 0.70% | -0.42 pp | 0.38% |
| Nathalie ARTHAUD | 0.20% | 0.49% | -0.29 pp | 0.26% |

## French presidential election 2022, first round

Question: `q3_presidential_2022.txt`.
Exported distributions (normalized): [20261004T192353744391Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv](../results/20261004_presidential_v2/20261004T192353744391Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv).
Validated rows: 1000; sum of mean probabilities: 100.000000%.
Original probability sums ranged from 0.990000 to 1.000000; 74 rounded distributions required normalization. Original sums are retained in the CSV, and original values in the raw JSONL checkpoint.

Candidate answers: **46.12%**; abstention: **45.90%**; blank/null: **7.98%**.

Mean absolute option error: **5.25 pp**. Largest discrepancy: **Vous n'iriez pas voter**, +19.59 pp.

Reference: [Ministry of the Interior, official results](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php).

| Answer | JEV, all personas | Official, registered voters | Difference | JEV, candidate-only |
| --- | ---: | ---: | ---: | ---: |
| Vous n'iriez pas voter | 45.90% | 26.31% | +19.59 pp | — |
| Emmanuel MACRON | 11.18% | 20.07% | -8.89 pp | 24.23% |
| Yannick JADOT | 9.18% | 3.34% | +5.84 pp | 19.91% |
| Jean-Luc MELENCHON | 7.06% | 15.82% | -8.76 pp | 15.30% |
| Valérie PECRESSE | 7.00% | 3.44% | +3.56 pp | 15.17% |
| Vous voteriez blanc | 6.30% | 1.12% | +5.18 pp | — |
| Jean LASSALLE | 4.36% | 2.26% | +2.10 pp | 9.45% |
| Fabien ROUSSEL | 2.53% | 1.65% | +0.88 pp | 5.48% |
| Anne HIDALGO | 2.30% | 1.26% | +1.04 pp | 4.99% |
| Vous voteriez nul | 1.68% | 0.51% | +1.17 pp | — |
| Marine LE PEN | 1.23% | 16.69% | -15.46 pp | 2.68% |
| Nicolas DUPONT-AIGNAN | 0.99% | 1.49% | -0.50 pp | 2.16% |
| Éric ZEMMOUR | 0.12% | 5.10% | -4.98 pp | 0.26% |
| Philippe POUTOU | 0.10% | 0.55% | -0.45 pp | 0.21% |
| Nathalie ARTHAUD | 0.07% | 0.40% | -0.33 pp | 0.16% |

## Prospective presidential candidate scenario

Question: `presidential_next_first_round_2026.txt`.
Exported distributions (normalized): [20261004T192353760768Z_si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-y-aurait-il-le-plus-de-chances-que-vous-votiez-1-marine-le-pen-jordan-bardella-r.csv](../results/20261004_presidential_v2/20261004T192353760768Z_si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-y-aurait-il-le-plus-de-chances-que-vous-votiez-1-marine-le-pen-jordan-bardella-r.csv).
Validated rows: 1000; sum of mean probabilities: 100.000000%.
Original probability sums ranged from 0.990000 to 1.000000; 121 rounded distributions required normalization. Original sums are retained in the CSV, and original values in the raw JSONL checkpoint.

Candidate answers: **63.13%**; abstention: **34.84%**; blank/null: **2.03%**.

| Answer | JEV, all personas | JEV, candidate-only |
| --- | ---: | ---: |
| Vous vous abstiendriez | 34.84% | — |
| Un autre candidat | 15.76% | 24.96% |
| Gabriel Attal – Renaissance | 10.26% | 16.25% |
| Le candidat issu de la primaire sociale-démocrate : Raphaël Glucksmann / Olivier Faure / Jérôme Guedj / Ségolène Royal / Emmanuel Maurel | 9.52% | 15.08% |
| Marine Tondelier – Les Écologistes | 5.66% | 8.97% |
| Édouard Philippe – Horizons | 3.84% | 6.08% |
| Bruno Retailleau – Les Républicains | 3.83% | 6.06% |
| Fabien Roussel – Parti communiste français | 3.51% | 5.56% |
| Bernard Cazeneuve | 3.23% | 5.12% |
| Jean-Luc Mélenchon – La France insoumise | 3.03% | 4.81% |
| Marine Le Pen / Jordan Bardella – Rassemblement national | 2.17% | 3.43% |
| François Ruffin – Debout ! | 2.11% | 3.34% |
| Vous voteriez blanc ou nul | 2.03% | — |
| Karim Bouamrane | 0.08% | 0.13% |
| Éric Zemmour – Reconquête | 0.06% | 0.09% |
| Nicolas Dupont-Aignan – Debout la France | 0.04% | 0.06% |
| Nathalie Arthaud – Lutte ouvrière | 0.02% | 0.03% |
| Selma Labib – NPA-Révolutionnaires | 0.01% | 0.01% |
| Anasse Kazib – Révolution Permanente | 0.00% | 0.00% |
| François Asselineau – Union populaire républicaine | 0.00% | 0.00% |
| Florian Philippot – Les Patriotes | 0.00% | 0.00% |

## Evidence and limits

All four exported CSVs passed the runner’s cache validator: current question/instruction fingerprints, current ordered population fingerprint, 1,000 matching persona IDs, finite probabilities between zero and one, distributions summing to one, valid selected answers and valid confidence values. The demographic and life-scenario CSV also passed population validation before inference.

These are model judgments conditional on invented scenarios. There are no human survey responses, electoral-eligibility filters, historical age adjustments, weighting, sampling-error intervals or held-out calibration in this run.

Original service responses: [raw checkpoint](../results/20261004_presidential_v2/checkpoint_f5065b4281179b49.jsonl).

Machine-readable aggregates: [summary.csv](../results/20261004_presidential_v2/summary.csv).
