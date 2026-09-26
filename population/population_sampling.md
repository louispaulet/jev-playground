# Synthetic French adult population sample

This directory contains a reproducible first sample of 1,000 synthetic personas for JEV experiments.

The sample is a quota-controlled synthetic population, not a probability sample of real people and not a guarantee that every joint relationship in the French population is reproduced. It is intended to provide a stable, inspectable baseline for simulation. The next step can add richer joint distributions or survey-specific variables when their source tables are selected.

## Scope and reference dates

- **Population:** adults aged 18 and over residing in metropolitan France and the four overseas departments/regions covered by the INSEE table: Guadeloupe, Martinique, Guyane and La Réunion.
- **Excluded territory:** Mayotte. The 2025 INSEE age/sex workbook includes Mayotte, but the 2022 INSEE socioprofessional reference is published for *France hors Mayotte*. Excluding Mayotte keeps the core margins on a common scope.
- **Age/sex and region reference:** INSEE population estimates at 1 January 2025, based on ages reached at 1 January.
- **Socioprofessional reference:** INSEE 2022 census, population aged 15 or over, current or previous socioprofessional group, France hors Mayotte. This is used as a proxy for adults because the published summary table is for 15+ rather than 18+.
- **Urban-area reference:** INSEE 2017 census population distribution by size of 2020 urban unit. It is older than the other margins and should be replaced when a comparable current table is selected.

## Selected attributes

| CSV column | Meaning | How it is used |
| --- | --- | --- |
| `persona_id` | Stable synthetic identifier | Unique row key; not a population characteristic |
| `sex` | `male` or `female` | Exact margin and part of the primary sex×age quota |
| `age` | Synthetic integer age | Generated within the checked age group; not separately quota-controlled |
| `age_group` | `18-24`, `25-34`, `35-49`, `50-64`, `65+` | Exact margin jointly crossed with `sex` |
| `csp` | Eight INSEE-style current/previous socioprofessional groups | Exact national margin |
| `region` | 13 metropolitan regions plus four overseas departments/regions | Exact adult regional margin |
| `urban_area_size` | Five grouped urban-unit size classes | Exact margin based on the INSEE 2017 distribution |

Education, income, employment status, nationality, religion, previous vote and turnout intention are intentionally not included in this first file. They require an explicit scope and source choice, and adding them independently would create misleading combinations. They can be added in a later version with a documented joint or post-stratification method.

## Sources and transformations

### Age, sex and region

Source: [INSEE, population estimates at 1 January 2025](https://www.insee.fr/fr/statistiques/8331297), especially the regional workbook [estim-pop-nreg-sexe-aq-1975-2025.xlsx](https://www.insee.fr/fr/statistiques/fichier/8331297/estim-pop-nreg-sexe-aq-1975-2025.xlsx).

The workbook contains five-year age bands by region and sex. For the adult sample, the `18-24` band is calculated as `2/5` of the `15-19` band plus all of `20-24`; the other bands are sums of complete five-year bands:

- `25-34` = 25-29 + 30-34
- `35-49` = 35-39 + 40-44 + 45-49
- `50-64` = 50-54 + 55-59 + 60-64
- `65+` = 65-69 through 95+

The `2/5` step is an explicit uniform-within-15-to-19 approximation because this source workbook is quinquennial. Applying those rules to the `France métropolitaine et DOM` row gives approximately 54.59 million adults, with the following 1,000-person integer allocation:

| Sex × age group | Personas |
| --- | ---: |
| male, 18-24 | 53 |
| male, 25-34 | 72 |
| male, 35-49 | 115 |
| male, 50-64 | 119 |
| male, 65+ | 119 |
| female, 18-24 | 51 |
| female, 25-34 | 73 |
| female, 35-49 | 120 |
| female, 50-64 | 124 |
| female, 65+ | 154 |

The region margin is calculated from the same adult transformation and allocated with the largest-remainder method:

| Region | Personas | Region | Personas |
| --- | ---: | --- | ---: |
| Auvergne-Rhône-Alpes | 120 | Bourgogne-Franche-Comté | 41 |
| Bretagne | 52 | Centre-Val de Loire | 38 |
| Corse | 6 | Grand Est | 82 |
| Hauts-de-France | 86 | Île-de-France | 179 |
| Normandie | 49 | Nouvelle-Aquitaine | 93 |
| Occitanie | 92 | Pays de la Loire | 57 |
| Provence-Alpes-Côte d'Azur | 78 | Guadeloupe | 6 |
| Martinique | 5 | Guyane | 4 |
| La Réunion | 12 | | |

### Socioprofessional group

Source: [INSEE, structure by current or previous socioprofessional group in 2022](https://www.insee.fr/fr/statistiques/2012701), using the published `France hors Mayotte` row and the linked regional workbook [TCRD_005.xlsx](https://www.insee.fr/fr/statistiques/fichier/2012701/TCRD_005.xlsx).

The eight source categories are retained, with short stable CSV labels. Percentages are 0.7%, 3.6%, 10.7%, 14.4%, 15.3%, 11.6%, 27.8% and 15.9%; the sample uses the corresponding exact integer quota `7, 36, 107, 144, 153, 116, 278, 159`.

This is a current-or-previous group, not an employment-status variable. For example, `retired` is a population category and not a prediction of whether a person currently works.

### Urban area size

Source: [INSEE, urban units](https://www.insee.fr/fr/statistiques/5039853), Figure 1, which reports the 2017 population distribution using the 2020 urban-unit composition.

The source’s detailed classes are grouped so that cells are not too small for a 1,000-person sample:

| CSV class | Source classes combined | Reference population | Personas |
| --- | --- | ---: | ---: |
| `rural_outside_urban_unit` | Outside an urban unit | 13,919,171 | 208 |
| `urban_unit_under_20k` | 2,000-4,999; 5,000-9,999; 10,000-19,999 | 12,022,735 | 180 |
| `urban_unit_20k_to_99k` | 20,000-49,999; 50,000-99,999 | 9,410,688 | 141 |
| `urban_unit_100k_to_1_999_999` | 100,000-199,999; 200,000-1,999,999 | 20,643,171 | 309 |
| `paris_urban_unit` | Paris urban unit | 10,785,092 | 162 |

The urban source table’s total is 66,780,857, and its scope is France. Since it is not the same 2025 adult frame as the other sources, urban-area size is treated as a controlled contextual margin rather than a claim of a fully current adult cross-tab.

## Allocation and validation

`create_population_sample.py` uses a fixed seed and assigns each marginal distribution to shuffled row positions, so repeated generation is reproducible while avoiding visible blocks of identical categories. The primary sex×age cells are created first; region, CSP and urban-area class are then balanced independently. This preserves every documented margin but does not manufacture unsupported correlations between them.

Run:

```bash
python population/create_population_sample.py
python population/validate_population_sample.py
```

The validator loads the CSV into a pandas `DataFrame` and checks the schema, row count, missing values, unique IDs, age-band consistency, exact sex×age cells, and exact one-way margins for CSP, region and urban area.

## Why these five controls first

The attached discussion correctly highlights sex×age, socioprofessional group, region and urbanity as useful first-order controls for an opinion simulation. At 1,000 rows, crossing every attribute would create many tiny or empty cells. The sample therefore uses one key joint control (sex×age) and four manageable one-way controls. Future versions should use published microdata or a synthetic-population/IPF method before treating additional joint relationships as realistic.
