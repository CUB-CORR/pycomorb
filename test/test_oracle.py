"""Independent oracle for the scoring.

The scoring is re-implemented in plain Python from the mapping and weight files and
compared with the engine on random patients, for every implementation and weighting
scheme. Targeted patients guarantee that every category (also rare ones that exist for
a single score or implementation) and every AND-group is exercised, so a wrong
assignment or a missing weight cannot hide.
"""

import random
from itertools import product

import polars as pl
import pytest
from helpers import (
    CHARLSON_FILES,
    CHARLSON_WEIGHTS,
    ELIXHAUSER_FILES,
    ELIXHAUSER_WEIGHTS,
    aliases,
    quiet,
    read,
    versions_of,
)

YEARS = [2010, 2016, 2017, 2021, 2024, 2025, 2026]
NOISE = ["Z00.0", "Z23", "R51", "V70", "999", "S06.0"]
YEAR_AWARE = {"sokolowski", "ahrq_icd10"}
# These Charlson implementations always use their own weights
OWN_WEIGHTS = ("rcs", "uk_shmi")
# Weighting schemes that must cover every category of an implementation
CHARLSON_CHECKED = ["charlson", "schneeweiss", "quan"]
ELIXHAUSER_CHECKED = ["van_walraven", "thompson_30", "thompson_29", "swiss"]
# Output columns of Charlson that are not categories
CHARLSON_OUTPUTS = {
    "Charlson Comorbidity Index",
    "Age Score",
    "Charlson Age-Comorbidity Score",
}

# Clinical hierarchy as (more severe, milder); only the severe one counts when both occur
CHARLSON_RULES = [
    ("Diabetes with chronic complication", "Diabetes without chronic complication"),
    ("Moderate or severe liver disease", "Mild liver disease"),
    ("Metastatic solid tumor", "Any malignancy"),
]
ELIXHAUSER_RULES = [
    ("Diabetes complicated", "Diabetes uncomplicated"),
    ("Hypertension complicated", "Hypertension uncomplicated"),
    ("Metastatic cancer", "Solid tumor without metastasis"),
    ("Liver disease, moderate to severe", "Liver disease"),
    ("Renal failure, severe", "Renal failure"),
    ("Metastatic cancer", "Solid tumor without metastasis, in situ"),
    ("Solid tumor without metastasis", "Solid tumor without metastasis, in situ"),
]


# --- the oracle -------------------------------------------------------------------------


def weights_table(stem):
    return {row["category"]: row for row in read(stem)}


def weight_of(table, category, column):
    value = table.get(category, {}).get(column, "")
    # categories without a weight count as 0
    return float(value) if value not in ("", None) else 0.0


def category_names(stem):
    names = (row["category"] for row in read(stem))
    return list(dict.fromkeys(name for name in names if name))


def present_categories(defs, ver, records, year_aware):
    """Category -> 0/1 for one patient. records: [(code, year)]."""
    cleaned = [(code.replace(".", "").strip().upper(), y) for code, y in records]
    groups = {}  # category -> {group key -> hit of each of its definition rows}
    for i, row in enumerate(defs):
        codes = row.get(f"{ver}_codes")
        if not row["category"] or not codes:
            continue
        since = int(row["year"]) if year_aware else 0
        prefixes = tuple(p.strip() for p in codes.split("|"))
        hit = any(y >= since and c.startswith(prefixes) for c, y in cleaned)
        group = groups.setdefault(row["category"], {})
        group.setdefault(row.get("and_group") or i, []).append(hit)
    present = dict.fromkeys((row["category"] for row in defs if row["category"]), 0)
    for category, group in groups.items():
        present[category] = int(any(all(hits) for hits in group.values()))
    return present


def apply_exclusions(present, renames, rules):
    """Drop the milder category when the more severe one is present."""
    canonical = {c: renames.get(c, c) for c in present}
    for severe, mild in product(present, repeat=2):
        if (canonical[severe], canonical[mild]) in rules and present[severe] == 1:
            present[mild] = 0
    return present


def weighted_sum(present, renames, table, column):
    weights = (weight_of(table, renames.get(c, c), column) for c in present)
    return sum(flag * weight for flag, weight in zip(present.values(), weights))


def age_points(age):
    bins = [(50, 0), (60, 1), (70, 2), (80, 3)]
    return next((points for limit, points in bins if age < limit), 4)


def any_category_hit(expected, outputs):
    """True if some patient has a category set, i.e. the comparison was not vacuous."""
    return any(v for row in expected for k, v in row.items() if k not in outputs)


# --- patients and engine ----------------------------------------------------------------


def targeted_patients(defs, col):
    """One patient per definition row and per AND-group (complete and incomplete)."""
    patients, groups = [], {}
    for row in defs:
        code = (row.get(col) or "").split("|")[0].strip()
        if not code:
            continue
        patients.append((60, [(code, 2026)]))
        if row.get("and_group"):
            groups.setdefault((row["category"], row["and_group"]), []).append(code)
    for codes in groups.values():
        patients.append((60, [(c, 2026) for c in codes]))
        patients.append((60, [(c, 2026) for c in codes[:-1]]))
    return patients


def make_patients(defs, ver, seed):
    """Random patients plus the targeted ones; a patient is (age, [(code, year)])."""
    rnd = random.Random(seed)
    col = f"{ver}_codes"
    pool = list(NOISE)
    for row in defs:
        for prefix in (row.get(col) or "").split("|"):
            if prefix.strip():
                pool += [prefix.strip(), prefix.strip() + str(rnd.randint(0, 9))]
    patients = []
    for _ in range(150):
        size = rnd.randint(1, 6)
        records = [(rnd.choice(pool), rnd.choice(YEARS)) for _ in range(size)]
        patients.append((rnd.randint(18, 95), records))
    return patients + targeted_patients(defs, col)


def run_engine(score, patients, ver, **kw):
    rows = [(i, c, age, y) for i, (age, recs) in enumerate(patients) for c, y in recs]
    df = pl.DataFrame(rows, schema=["id", "code", "age", "year"], orient="row")
    return quiet(score, df, icd_version=ver, return_categories=True, **kw).sort("id")


def compare(res, expected):
    """expected: per patient {column: value}; every column of the engine result must match."""
    got = res.to_dicts()
    assert len(got) == len(expected)
    for engine, oracle in zip(got, expected):
        for column, value in oracle.items():
            message = f"patient {engine['id']}, {column}: {engine[column]} != {value}"
            assert engine[column] == pytest.approx(value), message


# --- Charlson ---------------------------------------------------------------------------


def charlson_cases():
    for impl in CHARLSON_FILES:
        weights = [impl] if impl in OWN_WEIGHTS else CHARLSON_WEIGHTS
        for w, ver in product(weights, versions_of(impl)):
            yield pytest.param(impl, w, ver, id=f"{impl}-{w}-{ver}")


@pytest.mark.parametrize("impl,weights,ver", list(charlson_cases()))
def test_charlson_matches_oracle(impl, weights, ver):
    defs = read(CHARLSON_FILES[impl])
    table = weights_table("CHARLSON_WEIGHTS")
    renames = aliases("CHARLSON_CATEGORY_ALIASES.yaml", impl)
    column = f"{weights}_weights"
    patients = make_patients(defs, ver, seed=sum(map(ord, impl + ver)))
    expected = []
    for age, records in patients:
        present = present_categories(defs, ver, records, impl in YEAR_AWARE)
        present = apply_exclusions(present, renames, CHARLSON_RULES)
        index = weighted_sum(present, renames, table, column)
        if weights == "uk_shmi":
            index = max(index, 0)
        age_score = age_points(age) if weights == "charlson" else 0
        expected.append(
            {
                **present,
                "Charlson Comorbidity Index": index,
                "Age Score": age_score,
                "Charlson Age-Comorbidity Score": index + age_score,
            }
        )
    res = run_engine("charlson", patients, ver, implementation=impl, weights=weights)
    compare(res, expected)
    assert any_category_hit(expected, CHARLSON_OUTPUTS)


# --- Elixhauser -------------------------------------------------------------------------


def elixhauser_cases():
    for impl in ELIXHAUSER_FILES:
        weights = ["ahrq"] if impl.startswith("ahrq") else ELIXHAUSER_WEIGHTS
        for w, ver in product(weights, versions_of(impl)):
            yield pytest.param(impl, w, ver, id=f"{impl}-{w}-{ver}")


@pytest.mark.parametrize("impl,weights,ver", list(elixhauser_cases()))
def test_elixhauser_matches_oracle(impl, weights, ver):
    defs = read(ELIXHAUSER_FILES[impl])
    table = weights_table("ELIXHAUSER_WEIGHTS")
    renames = aliases("ELIXHAUSER_CATEGORY_ALIASES.yaml", impl)
    column = f"ahrq_{ver}_weights" if weights == "ahrq" else f"{weights}_weights"
    patients = make_patients(defs, ver, seed=sum(map(ord, impl + ver)))
    expected = []
    for _, records in patients:
        present = present_categories(defs, ver, records, impl in YEAR_AWARE)
        present = apply_exclusions(present, renames, ELIXHAUSER_RULES)
        index = weighted_sum(present, renames, table, column)
        expected.append({**present, "Elixhauser Comorbidity Index": index})
    res = run_engine("elixhauser", patients, ver, implementation=impl, weights=weights)
    compare(res, expected)
    assert any_category_hit(expected, {"Elixhauser Comorbidity Index"})


# --- Combined Comorbidity Score and HFRS ------------------------------------------------


@pytest.mark.parametrize("ver", ["icd9", "icd10"])
def test_combined_matches_oracle(ver):
    defs = read("GAGNE")
    weights = {row["category"]: float(row["weights"]) for row in defs}
    expected = []
    patients = make_patients(defs, ver, seed=1)
    for _, records in patients:
        present = present_categories(defs, ver, records, False)
        score = sum(flag * weights[c] for c, flag in present.items())
        expected.append({**present, "Combined Comorbidity Score": score})
    compare(run_engine("gagne", patients, ver), expected)
    assert any_category_hit(expected, {"Combined Comorbidity Score"})


def test_hfrs_matches_oracle():
    defs = read("HFRS")
    weights = {row["category"]: float(row["weight"]) for row in defs}
    expected = []
    patients = make_patients(defs, "icd10", seed=2)
    for _, records in patients:
        present = present_categories(defs, "icd10", records, False)
        score = round(sum(flag * weights[c] for c, flag in present.items()), 1)
        expected.append({**present, "HFRS Score": score})
    compare(run_engine("hfrs", patients, "icd10"), expected)
    assert any_category_hit(expected, {"HFRS Score"})


# --- mixed ICD-9 / ICD-10 input ---------------------------------------------------------


@pytest.mark.parametrize("impl", ["quan", "sweden"])
def test_mixed_versions_take_union_of_both_catalogues(impl):
    defs = read(CHARLSON_FILES[impl])
    table = weights_table("CHARLSON_WEIGHTS")
    renames = aliases("CHARLSON_CATEGORY_ALIASES.yaml", impl)
    rnd = random.Random(3)
    icd9 = make_patients(defs, "icd9", seed=1)
    icd10 = make_patients(defs, "icd10", seed=2)
    rows, expected = [], []
    for i in range(120):
        records9, records10 = rnd.choice(icd9)[1], rnd.choice(icd10)[1]
        rows += [(i, c, 55, y, "ICD-9") for c, y in records9]
        rows += [(i, c, 55, y, "ICD-10") for c, y in records10]
        present9 = present_categories(defs, "icd9", records9, False)
        present10 = present_categories(defs, "icd10", records10, False)
        present = {c: max(present9[c], present10[c]) for c in present9}
        present = apply_exclusions(present, renames, CHARLSON_RULES)
        index = weighted_sum(present, renames, table, "charlson_weights")
        expected.append(
            {
                "Charlson Comorbidity Index": index,
                "Age Score": 1,  # age 55
                "Charlson Age-Comorbidity Score": index + 1,
            }
        )
    df = pl.DataFrame(rows, schema=["id", "code", "age", "year", "ver"], orient="row")
    res = quiet(
        "charlson",
        df,
        icd_version="icd9_10",
        icd_version_col="ver",
        implementation=impl,
        return_categories=True,
    ).sort("id")
    compare(res, expected)


# --- no category silently scores 0 ------------------------------------------------------


def missing_weights(stem, table, renames, scheme):
    """Categories of a definition file that have no weight in the given scheme."""
    column = f"{scheme}_weights"
    names = category_names(stem)
    return [c for c in names if table.get(renames.get(c, c), {}).get(column, "") == ""]


@pytest.mark.parametrize("impl", CHARLSON_FILES)
def test_every_charlson_category_has_a_weight(impl):
    """A category missing from the weight table (e.g. a forgotten alias) would count as 0."""
    table = weights_table("CHARLSON_WEIGHTS")
    renames = aliases("CHARLSON_CATEGORY_ALIASES.yaml", impl)
    schemes = [impl] if impl in OWN_WEIGHTS else CHARLSON_CHECKED
    for scheme in schemes:
        missing = missing_weights(CHARLSON_FILES[impl], table, renames, scheme)
        assert not missing, f"{impl}/{scheme}: no weight for {missing}"


@pytest.mark.parametrize("impl", ELIXHAUSER_FILES)
def test_every_elixhauser_category_has_a_weight(impl):
    table = weights_table("ELIXHAUSER_WEIGHTS")
    renames = aliases("ELIXHAUSER_CATEGORY_ALIASES.yaml", impl)
    # the AHRQ weight tables deliberately omit arrhythmias and fluid/electrolyte disorders
    ahrq = impl.startswith("ahrq")
    schemes = [impl] if ahrq else ELIXHAUSER_CHECKED
    for scheme in schemes:
        missing = missing_weights(ELIXHAUSER_FILES[impl], table, renames, scheme)
        assert not missing, f"{impl}/{scheme}: no weight for {missing}"
