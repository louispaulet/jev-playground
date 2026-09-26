# Joint-distribution audit of `population_sample.csv`

Date: 2026-09-26  
File checked: `polling_test/population/population_sample.csv`  
Sample size: 1,000 adults

## Verdict

The sample matches its controlled `sex × age_group` quota, but it does not yet
look like a French population at the joint level. The generator assigns `csp`,
`region`, and `urban_area_size` independently after creating the `sex × age`
cells. That creates both implausible combinations and regional distributions
that contradict INSEE.

The strongest defects are:

- `age_group × csp`: retired people are assigned to young age groups. The
  sample has `retired` for 35.2% of 25–34-year-olds and 32.3% of 35–49-year-olds;
  the comparable INSEE 2022 table is approximately 0.0% and 0.1%.
- `region × urban_area_size`: 142 of the 162 `paris_urban_unit` personas are
  outside Île-de-France. INSEE defines the Paris urban unit as the
  agglomeration containing Paris, so those are impossible cells.

## Comparisons

The distance metric below is weighted total variation: for each row group, take
half the sum of absolute differences between the sample and INSEE conditional
percentages, then weight by the sample row size. `0` is an exact match and `1`
means disjoint distributions. It is used as a compact diagnostic, not as a
sampling-error test.

| Joint distribution | INSEE reference | Result |
| --- | --- | --- |
| `sex × age_group` | INSEE population estimates at 1 January 2025, as documented for the sample | **Exact controlled quota**: all 10 cells match the checked-in targets; rounding is at most 0.1 percentage point. |
| `age_group × csp` | RP2022 POP6 V2, France entière, population aged 15+, current or previous socioprofessional group | **Poor match**, weighted TV ≈ **0.372**. |
| `region × csp` | RP2022 regional table, population aged 15+, current or previous socioprofessional group | **Poor match**, weighted TV ≈ **0.142**. |
| `region × urban_area_size` | RP2022 commune population, joined to the INSEE 2022 commune geography and 2020 urban-unit size classes | **Poor match**, weighted TV ≈ **0.339**. |

### Selected gaps

Percentages below are within the indicated row group.

| Cell | Synthetic | INSEE | Difference |
| --- | ---: | ---: | ---: |
| `25–34 × retired` | 35.2% | ≈0.0% | +35.2 pp |
| `35–49 × retired` | 32.3% | ≈0.1% | +32.2 pp |
| `65+ × retired` | 29.3% | 93.2% | −63.9 pp |
| Île-de-France × manager/intellectual profession | 10.6% | 20.0% | −9.4 pp |
| Île-de-France × retired | 27.9% | 19.7% | +8.2 pp |
| Île-de-France × `paris_urban_unit` | 11.2% | 88.6% | −77.4 pp |
| Île-de-France × rural/outside urban unit | 21.2% | 3.5% | +17.7 pp |
| Provence-Alpes-Côte d’Azur × 100k–1,999,999 urban unit | 23.1% | 70.6% | −47.5 pp |

The INSEE urban-unit aggregation also shows that the overall urban margin can
look close while the regional allocation is wrong: the national categories are
similar, but the sample spreads every category across every region.

## Requested comparisons that are not identifiable from this CSV

The current file has no `employment_status`, `education_level`, `income_band`,
or `household_type` columns. Therefore these checks cannot be run yet:

- age × employment status;
- CSP × education;
- income × household type.

INSEE does publish relevant source tables: RP2022 POP5 contains age × type of
activity, the harmonized 25–54 active-population tables contain CSP × diploma,
and the 2022 income results include income by household type and age. Those
comparisons require adding the fields to the synthetic schema and choosing a
common scope first.

## Recommended next population version

1. Keep the exact `sex × age_group` quota.
2. Add hard structural constraints: `paris_urban_unit ⇒ Île-de-France`, and
   use INSEE `region × urban_area_size` targets instead of independent margins.
3. Add an age-conditioned CSP assignment from RP2022 POP6 V2; at minimum,
   forbid or sharply limit `retired` below age 55 and make retirement dominant
   at 65+.
4. Add employment, education, income, and household variables only when their
   joint INSEE tables and scope are documented. Use IPF/raking or constrained
   allocation for the multi-way targets; do not assign each new variable
   independently.

## Sources and scope

- [INSEE RP2022 POP6 V2: population aged 15+ by age, sex, and socioprofessional group](https://www.insee.fr/fr/statistiques/8581725?geo=FE-1&sommaire=8581745).
- [INSEE RP2022 regional socioprofessional structure](https://www.insee.fr/fr/statistiques/2012701).
- [INSEE RP2022 detailed population tables, including POP1A and POP5](https://www.insee.fr/fr/statistiques/8581810).
- [INSEE commune geography table, including region and urban-unit membership](https://www.insee.fr/fr/information/7671844).
- [INSEE 2020 urban-unit base and size classes](https://www.insee.fr/fr/information/4802589?lang=en).
- [INSEE population estimates at 1 January 2025](https://www.insee.fr/fr/statistiques/8331297), the reference used by the existing `sex × age` and region quotas.

The age × CSP and regional CSP comparisons use a 15+ INSEE reference against an
18+ synthetic sample because the published socioprofessional table is for 15+.
The `18–24` source row uses the same explicit `2/5` approximation for ages
18–19 that the existing sampling documentation uses for quinquennial tables.
The urban comparison uses RP2022 adult age bands with the 2020 urban-unit
classification; its size bands are based on the INSEE classification tied to
the 2017 census, so it is a structural audit rather than a same-date estimate.
