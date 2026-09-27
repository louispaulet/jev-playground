# JEV benchmark results versus IRL targets

This report compares the cached JEV probability distributions with known
French election results, INSEE-controlled margins, and independent INSEE
Camme opinion balances. All benchmark questions were batched into one JEV
request per persona, and each question's response was saved as its own CSV.

JEV values are mean probabilities across the personas. Differences are
JEV minus IRL, in percentage points. Election targets use registered voters
as the denominator, so abstention, blank and null options remain comparable.

## French presidential election 2012, first round

- Question file: `presidential_2012_first_round.txt`
- JEV CSV: [`20260927T201142858512Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv`](../results/20260927T201142858512Z_si-le-premier-tour-de-lelection-presidentielle-de-2012-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-eva-joly-2-marine-le-pen-3.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/PR2012/FE.php)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| Eva JOLY | 3.06% | 1.80% | +1.26 pp |
| Marine LE PEN | 7.87% | 13.95% | -6.08 pp |
| Nicolas SARKOZY | 19.74% | 21.19% | -1.45 pp |
| Jean-Luc MELENCHON | 4.01% | 8.66% | -4.65 pp |
| Philippe POUTOU | 0.17% | 0.89% | -0.73 pp |
| Nathalie ARTHAUD | 0.14% | 0.44% | -0.30 pp |
| Jacques CHEMINADE | 0.42% | 0.19% | +0.22 pp |
| François BAYROU | 4.45% | 7.12% | -2.66 pp |
| Nicolas DUPONT-AIGNAN | 0.68% | 1.40% | -0.72 pp |
| François HOLLANDE | 41.86% | 22.32% | +19.54 pp |
| Vous voteriez blanc ou nul | 0.50% | 1.52% | -1.03 pp |
| Vous n'iriez pas voter | 17.02% | 20.52% | -3.50 pp |

## French presidential election 2017, first round

- Question file: `presidential_2017_first_round.txt`
- JEV CSV: [`20260927T201142866574Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv`](../results/20260927T201142866574Z_si-le-premier-tour-de-lelection-presidentielle-de-2017-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-cette-personne-aurait-elle-probablement-vote-1-emmanuel-macron-2-marine-le.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2017/FE.php)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| Emmanuel MACRON | 35.93% | 18.19% | +17.74 pp |
| Marine LE PEN | 17.52% | 16.14% | +1.38 pp |
| François FILLON | 12.34% | 15.16% | -2.82 pp |
| Jean-Luc MELENCHON | 6.74% | 14.84% | -8.10 pp |
| Benoît HAMON | 2.05% | 4.82% | -2.77 pp |
| Nicolas DUPONT-AIGNAN | 2.62% | 3.56% | -0.94 pp |
| Jean LASSALLE | 3.15% | 0.91% | +2.24 pp |
| Philippe POUTOU | 0.12% | 0.83% | -0.71 pp |
| François ASSELINEAU | 0.32% | 0.70% | -0.38 pp |
| Nathalie ARTHAUD | 0.14% | 0.49% | -0.35 pp |
| Jacques CHEMINADE | 0.39% | 0.14% | +0.25 pp |
| Vous voteriez blanc | 1.54% | 1.39% | +0.15 pp |
| Vous voteriez nul | 0.45% | 0.61% | -0.16 pp |
| Vous n'iriez pas voter | 16.62% | 22.23% | -5.61 pp |

## French presidential election 2022, first round

- Question file: `q3_presidential_2022.txt`
- JEV CSV: [`20260927T201142875145Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv`](../results/20260927T201142875145Z_q3-si-le-premier-tour-de-lelection-presidentielle-avait-lieu-dimanche-prochain-pour-lequel-des-candidats-suivants-voteriez-vous-1-philippe-poutou-2-nathalie-arthaud-3-fabien-roussel-4-jean-lu.csv)
- Rows: `1000`
- Denominator: % of registered voters
- Source: [https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php](https://www.archives-resultats-elections.interieur.gouv.fr/resultats/presidentielle-2022/FE.php)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| Philippe POUTOU | 0.23% | 0.55% | -0.32 pp |
| Nathalie ARTHAUD | 0.04% | 0.40% | -0.36 pp |
| Fabien ROUSSEL | 1.70% | 1.65% | +0.05 pp |
| Jean-Luc MELENCHON | 6.24% | 15.82% | -9.58 pp |
| Anne HIDALGO | 1.66% | 1.26% | +0.40 pp |
| Yannick JADOT | 3.52% | 3.34% | +0.18 pp |
| Emmanuel MACRON | 23.61% | 20.07% | +3.54 pp |
| Valérie PECRESSE | 8.53% | 3.44% | +5.09 pp |
| Jean LASSALLE | 6.68% | 2.26% | +4.42 pp |
| Nicolas DUPONT-AIGNAN | 2.36% | 1.49% | +0.87 pp |
| Marine LE PEN | 7.09% | 16.69% | -9.60 pp |
| Éric ZEMMOUR | 0.79% | 5.10% | -4.31 pp |
| Vous voteriez blanc | 2.26% | 1.12% | +1.14 pp |
| Vous voteriez nul | 1.10% | 0.51% | +0.59 pp |
| Vous n'iriez pas voter | 34.14% | 26.31% | +7.83 pp |

## INSEE-controlled sex margin in the synthetic sample

- Question file: `insee_sex.txt`
- JEV CSV: [`20260927T201142849514Z_quelle-est-la-modalite-de-sexe-indiquee-pour-cette-personne-dans-son-profil-1-male-2-female.csv`](../results/20260927T201142849514Z_quelle-est-la-modalite-de-sexe-indiquee-pour-cette-personne-dans-son-profil-1-male-2-female.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| male | 47.80% | 47.80% | +0.00 pp |
| female | 52.20% | 52.20% | +0.00 pp |

Persona-level selected-answer accuracy against the supplied `sex` field: `100.00%`.

## INSEE-controlled age-group margin in the synthetic sample

- Question file: `insee_age_group.txt`
- JEV CSV: [`20260927T201142804796Z_dans-quelle-classe-dage-se-trouve-cette-personne-selon-son-profil-1-18-24-2-25-34-3-35-49-4-50-64-5-65.csv`](../results/20260927T201142804796Z_dans-quelle-classe-dage-se-trouve-cette-personne-selon-son-profil-1-18-24-2-25-34-3-35-49-4-50-64-5-65.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| 18-24 | 10.40% | 10.40% | +0.00 pp |
| 25-34 | 14.50% | 14.50% | -0.00 pp |
| 35-49 | 23.50% | 23.50% | +0.00 pp |
| 50-64 | 24.30% | 24.30% | +0.00 pp |
| 65+ | 27.30% | 27.30% | +0.00 pp |

Persona-level selected-answer accuracy against the supplied `age_group` field: `100.00%`.

## INSEE-controlled socioprofessional margin in the synthetic sample

- Question file: `insee_csp.txt`
- JEV CSV: [`20260927T201142836068Z_quel-est-le-groupe-socioprofessionnel-actuel-ou-anterieur-de-cette-personne-selon-son-profil-1-farmer-2-craft-trader-business-owner-3-manager-intellectual-profession-4-intermediate-profession-5.csv`](../results/20260927T201142836068Z_quel-est-le-groupe-socioprofessionnel-actuel-ou-anterieur-de-cette-personne-selon-son-profil-1-farmer-2-craft-trader-business-owner-3-manager-intellectual-profession-4-intermediate-profession-5.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| farmer | 0.70% | 0.70% | +0.00 pp |
| craft_trader_business_owner | 3.60% | 3.60% | -0.00 pp |
| manager_intellectual_profession | 10.69% | 10.70% | -0.01 pp |
| intermediate_profession | 14.40% | 14.40% | -0.00 pp |
| employee | 15.30% | 15.30% | -0.00 pp |
| worker | 11.60% | 11.60% | -0.00 pp |
| retired | 27.81% | 27.80% | +0.01 pp |
| other_inactive | 15.90% | 15.90% | +0.00 pp |

Persona-level selected-answer accuracy against the supplied `csp` field: `100.00%`.

## INSEE-controlled regional margin in the synthetic sample

- Question file: `insee_region.txt`
- JEV CSV: [`20260927T201142841684Z_dans-quelle-region-ou-collectivite-cette-personne-reside-t-elle-selon-son-profil-1-auvergne-rhone-alpes-2-bourgogne-franche-comte-3-bretagne-4-centre-val-de-loire-5-corse-6-grand-est-7-hauts.csv`](../results/20260927T201142841684Z_dans-quelle-region-ou-collectivite-cette-personne-reside-t-elle-selon-son-profil-1-auvergne-rhone-alpes-2-bourgogne-franche-comte-3-bretagne-4-centre-val-de-loire-5-corse-6-grand-est-7-hauts.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| Auvergne-Rhône-Alpes | 12.00% | 12.00% | +0.00 pp |
| Bourgogne-Franche-Comté | 4.10% | 4.10% | +0.00 pp |
| Bretagne | 5.20% | 5.20% | +0.00 pp |
| Centre-Val de Loire | 3.80% | 3.80% | +0.00 pp |
| Corse | 0.60% | 0.60% | +0.00 pp |
| Grand Est | 8.20% | 8.20% | +0.00 pp |
| Hauts-de-France | 8.60% | 8.60% | +0.00 pp |
| Île-de-France | 17.90% | 17.90% | +0.00 pp |
| Normandie | 4.90% | 4.90% | +0.00 pp |
| Nouvelle-Aquitaine | 9.30% | 9.30% | +0.00 pp |
| Occitanie | 9.20% | 9.20% | +0.00 pp |
| Pays de la Loire | 5.70% | 5.70% | +0.00 pp |
| Provence-Alpes-Côte d'Azur | 7.80% | 7.80% | +0.00 pp |
| Guadeloupe | 0.60% | 0.60% | +0.00 pp |
| Martinique | 0.50% | 0.50% | +0.00 pp |
| Guyane | 0.40% | 0.40% | +0.00 pp |
| La Réunion | 1.20% | 1.20% | +0.00 pp |

Persona-level selected-answer accuracy against the supplied `region` field: `100.00%`.

## INSEE-controlled urban-area margin in the synthetic sample

- Question file: `insee_urban_area.txt`
- JEV CSV: [`20260927T201142853301Z_dans-quelle-classe-de-taille-dunite-urbaine-cette-personne-reside-t-elle-selon-son-profil-1-rural-outside-urban-unit-2-urban-unit-under-20k-3-urban-unit-20k-to-99k-4-urban-unit-100k-to-1-999-99.csv`](../results/20260927T201142853301Z_dans-quelle-classe-de-taille-dunite-urbaine-cette-personne-reside-t-elle-selon-son-profil-1-rural-outside-urban-unit-2-urban-unit-under-20k-3-urban-unit-20k-to-99k-4-urban-unit-100k-to-1-999-99.csv)
- Rows: `1000`
- Denominator: % of personas / INSEE quota
- Source: [../population/population_sampling.md](../population/population_sampling.md)

| Option | JEV mean | IRL / target | Difference |
|---|---:|---:|---:|
| rural_outside_urban_unit | 20.80% | 20.80% | +0.00 pp |
| urban_unit_under_20k | 18.00% | 18.00% | +0.00 pp |
| urban_unit_20k_to_99k | 14.10% | 14.10% | -0.00 pp |
| urban_unit_100k_to_1_999_999 | 30.90% | 30.90% | +0.00 pp |
| paris_urban_unit | 16.20% | 16.20% | +0.00 pp |

Persona-level selected-answer accuracy against the supplied `urban_area_size` field: `100.00%`.

## INSEE Camme: expected personal financial situation

- Question file: `insee_camme_financial_future.txt`
- JEV CSV: [`20260927T201142819424Z_au-cours-des-douze-prochains-mois-votre-situation-financiere-personnelle-va-t-elle-1-s-ameliorer-2-rester-stable-3-se-degrader.csv`](../results/20260927T201142819424Z_au-cours-des-douze-prochains-mois-votre-situation-financiere-personnelle-va-t-elle-1-s-ameliorer-2-rester-stable-3-se-degrader.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share expecting improvement minus share expecting deterioration

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | +1.12 pp | n/a | -14.00 pp | +15.12 pp | n/a |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| S'améliorer | 6.35% | n/a |
| Rester stable | 88.43% | n/a |
| Se dégrader | 5.23% | n/a |

## INSEE Camme: opportunity to make major purchases

- Question file: `insee_camme_major_purchases.txt`
- JEV CSV: [`20260927T201142824519Z_dans-la-situation-economique-actuelle-pensez-vous-que-les-gens-aient-interet-a-faire-des-achats-importants-1-oui-le-moment-est-plutot-favorable-2-le-moment-n-est-ni-particulierement-favorable-ni.csv`](../results/20260927T201142824519Z_dans-la-situation-economique-actuelle-pensez-vous-que-les-gens-aient-interet-a-faire-des-achats-importants-1-oui-le-moment-est-plutot-favorable-2-le-moment-n-est-ni-particulierement-favorable-ni.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share finding the moment favorable minus share finding it unfavorable

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | -76.43 pp | n/a | -36.00 pp | -40.43 pp | n/a |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| Oui, le moment est plutôt favorable | 1.45% | n/a |
| Le moment n'est ni particulièrement favorable ni particulièrement défavorable | 20.66% | n/a |
| Non, le moment est plutôt défavorable, il faudrait reporter l'achat | 77.88% | n/a |

## INSEE Camme: expected change in unemployment

- Question file: `insee_camme_unemployment_future.txt`
- JEV CSV: [`20260927T201142830803Z_pensez-vous-que-dans-les-douze-prochains-mois-le-nombre-de-chomeurs-va-1-fortement-ou-un-peu-augmenter-2-rester-stationnaire-3-fortement-ou-un-peu-diminuer.csv`](../results/20260927T201142830803Z_pensez-vous-que-dans-les-douze-prochains-mois-le-nombre-de-chomeurs-va-1-fortement-ou-un-peu-augmenter-2-rester-stationnaire-3-fortement-ou-un-peu-diminuer.csv)
- Rows: `1000`
- Denominator: INSEE Camme balance of responses, percentage points
- Source: [https://www.insee.fr/fr/statistiques/9031846](https://www.insee.fr/fr/statistiques/9031846)
- Reference period: `July 2026`

- Balance definition: share expecting unemployment to increase minus share expecting it to decrease

| Metric | JEV mean | JEV weighted | IRL / target | Unweighted diff | Weighted diff |
|---|---:|---:|---:|---:|---:|
| Opinion balance | +17.17 pp | n/a | +55.00 pp | -37.83 pp | n/a |

JEV response probabilities:

| Option | JEV mean | JEV weighted |
|---|---:|---:|
| Fortement ou un peu augmenter | 24.46% | n/a |
| Rester stationnaire | 68.23% | n/a |
| Fortement ou un peu diminuer | 7.29% | n/a |

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
