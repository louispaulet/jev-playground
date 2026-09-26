# JEV benchmark results versus IRL targets

This report compares the cached JEV probability distributions with known
French election results, INSEE-controlled margins, and independent INSEE
Camme opinion balances. All benchmark questions were batched into one JEV
request per persona, and each question's response was saved as its own CSV.

JEV values are mean probabilities across the personas. Differences are
JEV minus IRL, in percentage points. Election targets use registered voters
as the denominator, so abstention, blank and null options remain comparable.

A weighted diagnostic is also shown using [`calibrated_weights_all.csv`](calibrated_weights_all.csv).
Weight range: `0.500`–`2.000`; effective sample size: `650.7`.

## French presidential election 2012, first round

- Question file: `presidential_2012_first_round.txt`
- JEV CSV: [`20260926T203549940156Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv`](../results/20260926T203549940156Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Eva JOLY | 4.59% | 3.52% | 1.80% | +2.79 pp | +1.72 pp |
| Marine LE PEN | 4.31% | 5.71% | 13.95% | -9.64 pp | -8.25 pp |
| Nicolas SARKOZY | 14.97% | 17.00% | 21.19% | -6.22 pp | -4.19 pp |
| Jean-Luc MELENCHON | 4.06% | 4.19% | 8.66% | -4.60 pp | -4.47 pp |
| Philippe POUTOU | 0.15% | 0.20% | 0.89% | -0.74 pp | -0.70 pp |
| Nathalie ARTHAUD | 0.12% | 0.15% | 0.44% | -0.32 pp | -0.29 pp |
| Jacques CHEMINADE | 0.60% | 0.82% | 0.19% | +0.41 pp | +0.63 pp |
| François BAYROU | 7.16% | 6.07% | 7.12% | +0.04 pp | -1.05 pp |
| Nicolas DUPONT-AIGNAN | 1.02% | 1.29% | 1.40% | -0.38 pp | -0.11 pp |
| François HOLLANDE | 47.55% | 40.28% | 22.32% | +25.23 pp | +17.96 pp |
| Vous voteriez blanc ou nul | 1.13% | 1.52% | 1.52% | -0.39 pp | -0.00 pp |
| Vous n'iriez pas voter | 14.27% | 19.22% | 20.52% | -6.25 pp | -1.30 pp |

## French presidential election 2017, first round

- Question file: `presidential_2017_first_round.txt`
- JEV CSV: [`20260926T203549962306Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv`](../results/20260926T203549962306Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Emmanuel MACRON | 45.74% | 35.73% | 18.19% | +27.55 pp | +17.54 pp |
| Marine LE PEN | 9.75% | 12.75% | 16.14% | -6.39 pp | -3.39 pp |
| François FILLON | 10.48% | 11.71% | 15.16% | -4.68 pp | -3.45 pp |
| Jean-Luc MELENCHON | 6.66% | 6.87% | 14.84% | -8.18 pp | -7.97 pp |
| Benoît HAMON | 2.45% | 2.28% | 4.82% | -2.37 pp | -2.54 pp |
| Nicolas DUPONT-AIGNAN | 3.04% | 3.77% | 3.56% | -0.52 pp | +0.21 pp |
| Jean LASSALLE | 4.72% | 5.07% | 0.91% | +3.81 pp | +4.16 pp |
| Philippe POUTOU | 0.10% | 0.15% | 0.83% | -0.73 pp | -0.68 pp |
| François ASSELINEAU | 0.46% | 0.53% | 0.70% | -0.24 pp | -0.17 pp |
| Nathalie ARTHAUD | 0.10% | 0.14% | 0.49% | -0.39 pp | -0.35 pp |
| Jacques CHEMINADE | 0.50% | 0.61% | 0.14% | +0.36 pp | +0.47 pp |
| Vous voteriez blanc | 1.93% | 2.35% | 1.39% | +0.54 pp | +0.96 pp |
| Vous voteriez nul | 0.46% | 0.63% | 0.61% | -0.15 pp | +0.02 pp |
| Vous n'iriez pas voter | 13.53% | 17.38% | 22.23% | -8.70 pp | -4.85 pp |

## French presidential election 2022, first round

- Question file: `q3_presidential_2022.txt`
- JEV CSV: [`20260926T203549979775Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv`](../results/20260926T203549979775Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Philippe POUTOU | 0.09% | 0.14% | 0.55% | -0.46 pp | -0.41 pp |
| Nathalie ARTHAUD | 0.02% | 0.03% | 0.40% | -0.38 pp | -0.37 pp |
| Fabien ROUSSEL | 1.45% | 2.09% | 1.65% | -0.20 pp | +0.44 pp |
| Jean-Luc MELENCHON | 4.19% | 4.86% | 15.82% | -11.63 pp | -10.96 pp |
| Anne HIDALGO | 4.02% | 3.45% | 1.26% | +2.76 pp | +2.19 pp |
| Yannick JADOT | 7.93% | 6.75% | 3.34% | +4.59 pp | +3.41 pp |
| Emmanuel MACRON | 21.42% | 17.25% | 20.07% | +1.35 pp | -2.82 pp |
| Valérie PECRESSE | 10.66% | 7.56% | 3.44% | +7.22 pp | +4.12 pp |
| Jean LASSALLE | 8.78% | 9.57% | 2.26% | +6.52 pp | +7.31 pp |
| Nicolas DUPONT-AIGNAN | 2.19% | 2.83% | 1.49% | +0.70 pp | +1.34 pp |
| Marine LE PEN | 2.83% | 3.91% | 16.69% | -13.87 pp | -12.78 pp |
| Éric ZEMMOUR | 0.35% | 0.48% | 5.10% | -4.75 pp | -4.62 pp |
| Vous voteriez blanc | 3.38% | 3.61% | 1.12% | +2.26 pp | +2.49 pp |
| Vous voteriez nul | 1.18% | 1.36% | 0.51% | +0.67 pp | +0.85 pp |
| Vous n'iriez pas voter | 31.46% | 36.05% | 26.31% | +5.15 pp | +9.74 pp |

## INSEE-controlled sex margin in the synthetic sample

- Question file: `insee_sex.txt`
- JEV CSV: [`20260926T203549999437Z_quelle-est-la-modalite-de-sexe-indiquee-pour-cette-personne-dans-son-profil-1-male-2-female.csv`](../results/20260926T203549999437Z_quelle-est-la-modalite-de-sexe-indiquee-pour-cette-personne-dans-son-profil-1-male-2-female.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| male | 47.80% | 56.01% | 47.80% | +0.00 pp | +8.21 pp |
| female | 52.20% | 43.99% | 52.20% | +0.00 pp | -8.21 pp |

Persona-level selected-answer accuracy against the supplied `sex` field: `100.00%`.

## INSEE-controlled age-group margin in the synthetic sample

- Question file: `insee_age_group.txt`
- JEV CSV: [`20260926T203550008577Z_dans-quelle-classe-dage-se-trouve-cette-personne-selon-son-profil-1-18-24-2-25-34-3-35-49-4-50-64-5-65.csv`](../results/20260926T203550008577Z_dans-quelle-classe-dage-se-trouve-cette-personne-selon-son-profil-1-18-24-2-25-34-3-35-49-4-50-64-5-65.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| 18-24 | 10.40% | 10.91% | 10.40% | +0.00 pp | +0.51 pp |
| 25-34 | 14.50% | 16.14% | 14.50% | -0.00 pp | +1.64 pp |
| 35-49 | 23.50% | 23.79% | 23.50% | +0.00 pp | +0.29 pp |
| 50-64 | 24.30% | 24.32% | 24.30% | +0.00 pp | +0.02 pp |
| 65+ | 27.30% | 24.84% | 27.30% | +0.00 pp | -2.46 pp |

Persona-level selected-answer accuracy against the supplied `age_group` field: `100.00%`.

## INSEE-controlled socioprofessional margin in the synthetic sample

- Question file: `insee_csp.txt`
- JEV CSV: [`20260926T203550018364Z_quel-est-le-groupe-socioprofessionnel-actuel-ou-anterieur-de-cette-personne-selon-son-profil-1-farmer-2-craft-trader-business-owner-3-manager-intellectual-profession-4-intermediate-profession-5.csv`](../results/20260926T203550018364Z_quel-est-le-groupe-socioprofessionnel-actuel-ou-anterieur-de-cette-personne-selon-son-profil-1-farmer-2-craft-trader-business-owner-3-manager-intellectual-profession-4-intermediate-profession-5.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| farmer | 0.78% | 1.36% | 0.70% | +0.08 pp | +0.66 pp |
| craft_trader_business_owner | 3.63% | 3.57% | 3.60% | +0.03 pp | -0.03 pp |
| manager_intellectual_profession | 10.67% | 6.16% | 10.70% | -0.03 pp | -4.54 pp |
| intermediate_profession | 14.05% | 11.72% | 14.40% | -0.35 pp | -2.68 pp |
| employee | 15.26% | 13.42% | 15.30% | -0.04 pp | -1.88 pp |
| worker | 11.31% | 15.19% | 11.60% | -0.29 pp | +3.59 pp |
| retired | 28.46% | 27.02% | 27.80% | +0.66 pp | -0.78 pp |
| other_inactive | 15.85% | 21.57% | 15.90% | -0.05 pp | +5.67 pp |

Persona-level selected-answer accuracy against the supplied `csp` field: `100.00%`.

## INSEE-controlled regional margin in the synthetic sample

- Question file: `insee_region.txt`
- JEV CSV: [`20260926T203550040385Z_dans-quelle-region-ou-collectivite-cette-personne-reside-t-elle-selon-son-profil-1-auvergne-rhone-alpes-2-bourgogne-franche-comte-3-bretagne-4-centre-val-de-loire-5-corse-6-grand-est-7-hauts.csv`](../results/20260926T203550040385Z_dans-quelle-region-ou-collectivite-cette-personne-reside-t-elle-selon-son-profil-1-auvergne-rhone-alpes-2-bourgogne-franche-comte-3-bretagne-4-centre-val-de-loire-5-corse-6-grand-est-7-hauts.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Auvergne-Rhône-Alpes | 11.92% | 11.31% | 12.00% | -0.08 pp | -0.69 pp |
| Bourgogne-Franche-Comté | 4.06% | 4.11% | 4.10% | -0.04 pp | +0.01 pp |
| Bretagne | 5.13% | 5.21% | 5.20% | -0.07 pp | +0.01 pp |
| Centre-Val de Loire | 3.80% | 3.64% | 3.80% | -0.00 pp | -0.16 pp |
| Corse | 0.60% | 0.50% | 0.60% | +0.00 pp | -0.10 pp |
| Grand Est | 8.17% | 8.77% | 8.20% | -0.03 pp | +0.57 pp |
| Hauts-de-France | 8.60% | 9.74% | 8.60% | -0.00 pp | +1.14 pp |
| Île-de-France | 18.36% | 19.08% | 17.90% | +0.46 pp | +1.18 pp |
| Normandie | 4.88% | 4.45% | 4.90% | -0.02 pp | -0.45 pp |
| Nouvelle-Aquitaine | 9.21% | 7.99% | 9.30% | -0.09 pp | -1.31 pp |
| Occitanie | 9.16% | 7.92% | 9.20% | -0.04 pp | -1.28 pp |
| Pays de la Loire | 5.68% | 6.26% | 5.70% | -0.02 pp | +0.56 pp |
| Provence-Alpes-Côte d'Azur | 7.79% | 8.32% | 7.80% | -0.01 pp | +0.52 pp |
| Guadeloupe | 0.60% | 1.01% | 0.60% | +0.00 pp | +0.41 pp |
| Martinique | 0.50% | 0.28% | 0.50% | +0.00 pp | -0.22 pp |
| Guyane | 0.39% | 0.62% | 0.40% | -0.01 pp | +0.22 pp |
| La Réunion | 1.15% | 0.81% | 1.20% | -0.05 pp | -0.39 pp |

Persona-level selected-answer accuracy against the supplied `region` field: `99.70%`.

## INSEE-controlled urban-area margin in the synthetic sample

- Question file: `insee_urban_area.txt`
- JEV CSV: [`20260926T203550059269Z_dans-quelle-classe-de-taille-dunite-urbaine-cette-personne-reside-t-elle-selon-son-profil-1-rural-outside-urban-unit-2-urban-unit-under-20k-3-urban-unit-20k-to-99k-4-urban-unit-100k-to-1-999-99.csv`](../results/20260926T203550059269Z_dans-quelle-classe-de-taille-dunite-urbaine-cette-personne-reside-t-elle-selon-son-profil-1-rural-outside-urban-unit-2-urban-unit-under-20k-3-urban-unit-20k-to-99k-4-urban-unit-100k-to-1-999-99.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| rural_outside_urban_unit | 20.81% | 23.09% | 20.80% | +0.01 pp | +2.29 pp |
| urban_unit_under_20k | 18.00% | 18.51% | 18.00% | +0.00 pp | +0.51 pp |
| urban_unit_20k_to_99k | 14.10% | 13.86% | 14.10% | +0.00 pp | -0.24 pp |
| urban_unit_100k_to_1_999_999 | 30.90% | 31.16% | 30.90% | +0.00 pp | +0.26 pp |
| paris_urban_unit | 16.19% | 13.39% | 16.20% | -0.01 pp | -2.81 pp |

Persona-level selected-answer accuracy against the supplied `urban_area_size` field: `100.00%`.

## INSEE Camme: expected personal financial situation

- Question file: `insee_camme_financial_future.txt`
- JEV CSV: [`20260926T204905961896Z_au-cours-des-douze-prochains-mois-votre-situation-financiere-personnelle-va-t-elle-1-s-ameliorer-2-rester-stable-3-se-degrader.csv`](../results/20260926T204905961896Z_au-cours-des-douze-prochains-mois-votre-situation-financiere-personnelle-va-t-elle-1-s-ameliorer-2-rester-stable-3-se-degrader.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share expecting improvement minus share expecting deterioration

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | +7.01 pp | +2.88 pp | -14.00 pp | +21.01 pp | +16.88 pp |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| S'améliorer | 9.74% | 6.68% |
| Rester stable | 87.53% | 89.52% |
| Se dégrader | 2.73% | 3.80% |

## INSEE Camme: opportunity to make major purchases

- Question file: `insee_camme_major_purchases.txt`
- JEV CSV: [`20260926T204905980372Z_dans-la-situation-economique-actuelle-pensez-vous-que-les-gens-aient-interet-a-faire-des-achats-importants-1-oui-le-moment-est-plutot-favorable-2-le-moment-n-est-ni-particulierement-favorable-ni.csv`](../results/20260926T204905980372Z_dans-la-situation-economique-actuelle-pensez-vous-que-les-gens-aient-interet-a-faire-des-achats-importants-1-oui-le-moment-est-plutot-favorable-2-le-moment-n-est-ni-particulierement-favorable-ni.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share finding the moment favorable minus share finding it unfavorable

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | -63.50 pp | -64.48 pp | -36.00 pp | -27.50 pp | -28.48 pp |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| Oui, le moment est plutôt favorable | 1.62% | 1.66% |
| Le moment n'est ni particulièrement favorable ni particulièrement défavorable | 33.26% | 32.20% |
| Non, le moment est plutôt défavorable, il faudrait reporter l'achat | 65.12% | 66.14% |

## INSEE Camme: expected change in unemployment

- Question file: `insee_camme_unemployment_future.txt`
- JEV CSV: [`20260926T204905996112Z_pensez-vous-que-dans-les-douze-prochains-mois-le-nombre-de-chomeurs-va-1-fortement-ou-un-peu-augmenter-2-rester-stationnaire-3-fortement-ou-un-peu-diminuer.csv`](../results/20260926T204905996112Z_pensez-vous-que-dans-les-douze-prochains-mois-le-nombre-de-chomeurs-va-1-fortement-ou-un-peu-augmenter-2-rester-stationnaire-3-fortement-ou-un-peu-diminuer.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share expecting unemployment to increase minus share expecting it to decrease

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | +7.30 pp | +9.69 pp | +55.00 pp | -47.70 pp | -45.31 pp |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| Fortement ou un peu augmenter | 15.52% | 17.11% |
| Rester stationnaire | 76.25% | 75.47% |
| Fortement ou un peu diminuer | 8.22% | 7.42% |

## Interpretation

The INSEE-controlled demographic sections are profile-reading checks:
the correct answer is already present in each persona row, while the
aggregate target comes from the documented INSEE quota. They test
whether JEV consumes the provided profile coherently; they are not
independent opinion polls.

The INSEE Camme sections are independent opinion benchmarks. INSEE's
July 2026 release publishes opinion balances rather than every raw
response share, so the report compares the same positive-minus-negative
balance computed from JEV probabilities with the published balance.

The election sections are aggregate historical benchmarks. They are useful
for measuring model/population mismatch, but fitting weights directly to
one election can overfit. Use the SciPy calibration script only after
checking weight bounds, effective sample size, and held-out questions or
elections.
