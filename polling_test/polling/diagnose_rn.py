#!/usr/bin/env python3
"""Reconcile the cached 2022 poll with official geography and Ipsos marginals.

No inference requests or API keys are needed. Raw public downloads stay in .cache.
"""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import urllib.request
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pandas as pd

from compare_benchmarks import find_result
from poll_population import load_personas, parse_numbered_options, read_question

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "communes.txt": "https://static.data.gouv.fr/resources/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour/20220414-152459/resultats-par-niveau-subcom-t1-france-entiere.txt",
    "regions.txt": "https://static.data.gouv.fr/resources/election-presidentielle-des-10-et-24-avril-2022-resultats-definitifs-du-1er-tour/20220414-152331/resultats-par-niveau-reg-t1-france-entiere.txt",
    "urban.zip": "https://www.insee.fr/fr/statistiques/fichier/4802589/UU2020_au_01-01-2022.zip",
}
REGIONS = {
    "01": "Guadeloupe", "02": "Martinique", "03": "Guyane", "04": "La Réunion",
    "11": "Île-de-France", "24": "Centre-Val de Loire", "27": "Bourgogne-Franche-Comté",
    "28": "Normandie", "32": "Hauts-de-France", "44": "Grand Est", "52": "Pays de la Loire",
    "53": "Bretagne", "75": "Nouvelle-Aquitaine", "76": "Occitanie",
    "84": "Auvergne-Rhône-Alpes", "93": "Provence-Alpes-Côte d'Azur", "94": "Corse",
}
AGE_SURVEY = {"18-24": 26, "25-34": 25, "35-49": 28, "50-59": 30, "60-69": 22, "70+": 13}
CSP_SURVEY = {
    "manager_intellectual_profession": 12, "intermediate_profession": 24,
    "employee": 36, "worker": 36, "retired": 17,
}


def fetch(cache, name):
    path = cache / name
    if not path.exists():
        path.write_bytes(urllib.request.urlopen(SOURCES[name], timeout=60).read())
    return path


def official_results(path, regional=False):
    """The official wide export repeats candidate blocks beyond its short header."""
    records = []
    start, width, name_offset, votes_offset = (17, 6, 1, 3) if regional else (19, 7, 2, 4)
    with path.open(encoding="cp1252", newline="") as f:
        rows = csv.reader(f, delimiter=";")
        next(rows)
        for row in rows:
            assert len(row) == start + 12 * width, "Unexpected official export schema"
            votes = {row[i + name_offset]: int(row[i + votes_offset]) for i in range(start, len(row), width)}
            registered, abstentions, expressed = (3, 4, 14) if regional else (5, 6, 16)
            assert len(votes) == 12 and sum(votes.values()) == int(row[expressed])
            record = dict(region_code=row[0]) if regional else dict(department_code=row[0], commune_code=row[2])
            record.update(name=row[1] if regional else row[3], registered=int(row[registered]),
                          abstentions=int(row[abstentions]), valid_votes=int(row[expressed]),
                          rn_votes=votes["LE PEN"], zemmour_votes=votes["ZEMMOUR"])
            records.append(record)
    return pd.DataFrame(records)


def xlsx_rows(archive, sheet):
    """Read only cell values: this INSEE workbook has malformed color styles.

    Its known worksheets use shared strings and numeric values, without formulas.
    Reading the original XML avoids changing the source or adding an Excel engine.
    """
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = ["".join(x.itertext()) for x in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", ns)]
    for row in ET.fromstring(archive.read(f"xl/worksheets/sheet{sheet}.xml")).findall(".//m:row", ns):
        cells = {}
        for cell in row:
            value = cell.findtext("m:v", default="", namespaces=ns)
            cells[cell.attrib["r"].rstrip("0123456789")] = strings[int(value)] if cell.attrib.get("t") == "s" else value
        yield cells


def urban_crosswalk(path):
    with ZipFile(path) as outer:
        with ZipFile(io.BytesIO(outer.read("UU2020_au_01-01-2022.xlsx"))) as book:
            units = {r["A"]: int(r["C"]) for r in list(xlsx_rows(book, 2))[6:] if r.get("A")}
            rows = list(xlsx_rows(book, 3))
            assert rows[5]["A"] == "CODGEO" and rows[5]["C"] == "UU2020"
            records = []
            for r in rows[6:]:
                if not r.get("A"):
                    continue
                unit = r["C"]
                size = 0 if r["E"] == "Hors unité urbaine" else units[unit]
                category = ("rural_outside_urban_unit" if size == 0 else
                            "paris_urban_unit" if unit == "00851" else
                            "urban_unit_under_20k" if size <= 3 else
                            "urban_unit_20k_to_99k" if size <= 5 else "urban_unit_100k_to_1_999_999")
                records.append(dict(insee_code=r["A"], region_code=r["H"].zfill(2), urban_area_size=category))
    return pd.DataFrame(records)


def sim_cuts(frame, field):
    g = frame.groupby(field, observed=True).agg(personas=("persona_id", "size"), rn_mass=("rn", "sum"),
                                               valid_mass=("valid", "sum"), abstention_mass=("abst", "sum"))
    g["sim_rn_expressed_pct"] = 100 * g.rn_mass / g.valid_mass
    g["sim_rn_all_personas_pct"] = 100 * g.rn_mass / g.personas
    g["sim_abstention_pct"] = 100 * g.abstention_mass / g.personas
    return g.reset_index()


def official_cuts(frame, field):
    g = frame.groupby(field).agg(communes=("name", "size"), registered=("registered", "sum"),
                                  valid_votes=("valid_votes", "sum"), rn_votes=("rn_votes", "sum"))
    g["official_rn_expressed_pct"] = 100 * g.rn_votes / g.valid_votes
    return g.reset_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", type=Path, default=ROOT / "polling_test/results/20261004_presidential_v2")
    parser.add_argument("--population", type=Path, default=ROOT / "polling_test/population/population_sample.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "polling_test/diagnostics/rn_2022")
    args = parser.parse_args()
    cache = ROOT / ".cache/rn_diagnostics"
    cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    personas = load_personas(args.population, 0)
    question = read_question(ROOT / "polling_test/questions/q3_presidential_2022.txt")
    result_path = find_result(args.result_dir, question, parse_numbered_options(question), personas)
    results = pd.read_csv(result_path)
    frame = pd.DataFrame(personas).merge(results, on="persona_id", validate="one_to_one")
    assert len(frame) == len(personas) == len(results)
    candidates = [c for c in results if c.startswith("probability_") and not c.startswith("probability_vous")]
    assert len(candidates) == 12
    frame["rn"] = frame["probability_marine-le-pen"]
    frame["rn_zemmour"] = frame["rn"] + frame["probability_eric-zemmour"]
    frame["valid"] = frame[candidates].sum(axis=1)
    frame["abst"] = frame["probability_vous-n-iriez-pas-voter"]
    frame["age_survey"] = pd.cut(frame.age.astype(int), [17, 24, 34, 49, 59, 69, 120], labels=list(AGE_SURVEY))
    assert frame.age_survey.notna().all()

    paths = {name: fetch(cache, name) for name in SOURCES}
    communes = official_results(paths["communes.txt"])
    regions = official_results(paths["regions.txt"], regional=True)
    totals = communes[["registered", "valid_votes", "rn_votes", "abstentions"]].sum()
    assert totals.to_dict() == dict(registered=48747876, valid_votes=35132947, rn_votes=8133828, abstentions=12824169)
    # Regional export excludes overseas collectivities and citizens abroad.
    regional_scope = communes[communes.department_code.isin(["ZA", "ZB", "ZC", "ZD", "ZM"]) | ~communes.department_code.str.startswith("Z")]
    assert regions[["registered", "valid_votes", "rn_votes", "abstentions"]].sum().equals(regional_scope[["registered", "valid_votes", "rn_votes", "abstentions"]].sum())
    dom = {"ZA": "971", "ZB": "972", "ZC": "973", "ZD": "974", "ZM": "976"}
    communes["insee_code"] = [dom[d] + c[-2:] if d in dom else d + c for d, c in zip(communes.department_code, communes.commune_code)]
    assert communes.insee_code.is_unique
    crosswalk = urban_crosswalk(paths["urban.zip"])
    assert crosswalk.insee_code.is_unique
    scoped = communes[communes.department_code.isin(dom.keys() - {"ZM"}) | ~communes.department_code.str.startswith("Z")]
    joined = scoped.merge(crosswalk, on="insee_code", how="left", validate="one_to_one", indicator=True)
    assert joined._merge.eq("both").all(), joined.loc[joined._merge != "both", ["insee_code", "name"]].to_dict("records")
    assert set(joined.region_code) == set(REGIONS)
    # Reconcile every region: catches department/overseas code and join mistakes.
    a = joined.groupby("region_code")[["registered", "valid_votes", "rn_votes"]].sum()
    b = regions.set_index("region_code").loc[a.index, a.columns]
    assert a.equals(b)
    joined["region"] = joined.region_code.map(REGIONS)
    joined["rn_expressed_pct"] = 100 * joined.rn_votes / joined.valid_votes
    joined["zemmour_expressed_pct"] = 100 * joined.zemmour_votes / joined.valid_votes
    joined["rn_zemmour_expressed_pct"] = joined.rn_expressed_pct + joined.zemmour_expressed_pct
    joined.drop(columns="_merge").to_csv(args.output / "communes.csv", index=False, float_format="%.6f")
    cities = ["Paris", "Lyon", "Rennes", "Nantes", "Lille", "Marseille", "Nice", "Roubaix", "Calais", "Hénin-Beaumont", "Perpignan", "Béziers"]
    selected = joined[joined.name.isin(cities)].copy()
    assert len(selected) == len(cities)
    selected.to_csv(args.output / "selected_cities.csv", index=False, float_format="%.6f")
    urban_mix = None
    for field in ["urban_area_size", "region"]:
        cuts = sim_cuts(frame, field).merge(official_cuts(joined, field), on=field, validate="one_to_one")
        assert len(cuts) == frame[field].nunique()
        cuts["gap_pp"] = cuts.sim_rn_expressed_pct - cuts.official_rn_expressed_pct
        cuts.to_csv(args.output / f"{field}.csv", index=False, float_format="%.6f")
        if field == "urban_area_size":
            urban_mix = float((cuts.sim_rn_expressed_pct * cuts.valid_votes / cuts.valid_votes.sum()).sum())
    for field, survey in [("age_survey", AGE_SURVEY), ("csp", CSP_SURVEY), ("sex", {"male": 23, "female": 24})]:
        cuts = sim_cuts(frame, field)
        cuts["ipsos_2022_rn_pct"] = cuts[field].map(survey).astype(float)
        cuts["gap_pp"] = cuts.sim_rn_expressed_pct - cuts.ipsos_2022_rn_pct
        cuts.to_csv(args.output / f"{field}.csv", index=False, float_format="%.6f")
    national = dict(personas=len(frame), sim_rn_expressed_pct=100 * frame.rn.sum() / frame.valid.sum(),
                    sim_rn_all_personas_pct=100 * frame.rn.mean(), sim_abstention_pct=100 * frame.abst.mean(),
                    sim_rn_zemmour_expressed_pct=100 * frame.rn_zemmour.sum() / frame.valid.sum(),
                    official_rn_expressed_pct=100 * totals.rn_votes / totals.valid_votes,
                    official_rn_zemmour_expressed_pct=100 * (communes.rn_votes.sum() + communes.zemmour_votes.sum()) / totals.valid_votes,
                    official_rn_registered_pct=100 * totals.rn_votes / totals.registered,
                    official_abstention_pct=100 * totals.abstentions / totals.registered,
                    profile_scope_rn_expressed_pct=100 * joined.rn_votes.sum() / joined.valid_votes.sum(),
                    sim_rn_with_official_valid_turnout_pct=100 * (totals.valid_votes / totals.registered) * frame.rn.sum() / frame.valid.sum(),
                    sim_rn_with_official_urban_valid_mix_pct=urban_mix,
                    profile_scope_communes=len(joined), excluded_communes=len(communes) - len(joined),
                    source_communes=len(communes), matched_communes=len(joined))
    manifest = dict(national=national, population_file_sha256=hashlib.sha256(args.population.read_bytes()).hexdigest(),
                    result_file=result_path.name, result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                    sources={name: dict(url=SOURCES[name], sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for name, path in paths.items()},
                    survey_source="https://www.ipsos.com/fr-fr/presidentielle-2022/1er-tour-abstentionnistes-sociologie-electorat",
                    survey_pages=dict(age_survey=4, csp=5, sex=4),
                    caveats=["Simulation uses 2025 adult-resident demographics, not the registered electorate in 2022.",
                             "Ipsos survey: 4,000 registered adults, online fieldwork 6–9 April 2022; estimates, not official demographic vote counts.",
                             "CSP mapping is approximate: synthetic CSP can be current or previous group, not survey current profession.",
                             "Rural means outside an INSEE urban unit, not the separate density-grid rural definition.",
                             "INSEE download is 2022 geography, released 21 March 2025, with corrected historical classifications.",
                             "Municipal rates are electoral aggregates; they do not identify individual political preferences.",
                             "No persona has a commune: municipality-level simulation comparisons are unavailable.",
                             "Conditional simulation rates divide summed RN mass by summed candidate mass; no argmax votes or average individual ratios."])
    (args.output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(national, indent=2))


if __name__ == "__main__":
    main()
