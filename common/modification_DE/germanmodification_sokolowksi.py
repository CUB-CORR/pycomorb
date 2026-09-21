# 1. place a copy of https://github.com/fabiansiegel/comorbidity_score/ in this folder
#    -> ships year-specific ICD-10-GM mapping JSONs in comorbidity_score_calc/mappings/
# 2. run this script from this folder: python germanmodification_sokolowksi.py
# 3. writes ../CHARLSON_SOKOLOWSKI.csv

import json
from pathlib import Path

years = range(2010, 2027)

source_dir = Path("comorbidity_score/comorbidity_score_calc/mappings")
out_path = Path("../CHARLSON_SOKOLOWSKI.csv")

# category key -> (index, label), index matches CHARLSON_WEIGHTS.csv's existing rows
categories = {
    "mi":                  (1, "Myocardial infarction"),
    "hf":                  (2, "Congestive heart failure"),
    "peripheral_vascular": (3, "Peripheral vascular disease"),
    "cerebrovascular":     (4, "Cerebrovascular disease"),
    "dementia":            (5, "Dementia"),
    "pulmo":               (6, "Chronic pulmonary disease"),
    "rheumatic":           (7, "Rheumatic disease"),
    "peptic_ulcer":        (8, "Peptic ulcer disease"),
    "liver_mild":          (9, "Mild liver disease"),
    "dm_simple":          (10, "Diabetes without chronic complication"),
    "dm_complicated":     (11, "Diabetes with chronic complication"),
    "plegia":             (12, "Hemiplegia or paraplegia"),
    "kidney":             (13, "Renal disease"),
    "malignancy_nonmeta": (14, "Any malignancy"),
    "liver_severe":       (15, "Moderate or severe liver disease"),
    "malignancy_meta":    (16, "Metastatic solid tumor"),
    "aids":               (17, "AIDS/HIV"),
} # fmt: skip
liver_severe_and_group = "liver_severe_and"


def strip_dots(codes):
    # codes come dotted (e.g. 'I25.20'); the rest of pycomorb matches undotted prefixes
    return {code.replace(".", "") for code in codes}


def flatten_any_codes(category_def):
    # union of every 'any'-condition code group's flat code list
    codes = set()
    for group in category_def["codes"]:
        if group["condition"] == "any":
            codes.update(group["codes"])
    return strip_dots(codes)


def flatten_both_subgroups(category_def):
    # the two subgroup lists of the (single) 'both'-condition group, if any
    for group in category_def["codes"]:
        if group["condition"] == "both":
            cause, organ = group["codes"]
            return strip_dots(cause), strip_dots(organ)
    return set(), set()


def contract(codes):
    # drop any code that has a proper ancestor prefix already in the set
    ordered = sorted(codes, key=len)
    kept = []
    for code in ordered:
        if not any(code != k and code.startswith(k) for k in kept):
            kept.append(code)
    return set(kept)


def load_year(year):
    with open(source_dir / f"charlson_icd10gm_{year}.json") as f:
        return json.load(f)["mapping"]


def changelog_rows(index, label, raw_by_year, and_group=None):
    # emit a row only where the contracted code set gains prefixes versus the previous year
    rows = []
    cumulative_raw = set()
    previous_contracted = set()
    for year in years:
        cumulative_raw |= raw_by_year[year]
        contracted = contract(cumulative_raw)
        new_prefixes = contracted - previous_contracted
        if new_prefixes:
            rows.append((index, label, year, and_group, "|".join(sorted(new_prefixes))))
        previous_contracted = contracted
    return rows


by_year = {year: load_year(year) for year in years}

rows = []
for key, (index, label) in categories.items():
    raw_by_year = {year: flatten_any_codes(by_year[year][key]) for year in years}
    rows.extend(changelog_rows(index, label, raw_by_year))

    if key == "liver_severe":
        cause_by_year, organ_by_year = {}, {}
        for year in years:
            cause_by_year[year], organ_by_year[year] = flatten_both_subgroups(by_year[year][key])
        rows.extend(changelog_rows(index, label, cause_by_year, liver_severe_and_group))
        rows.extend(changelog_rows(index, label, organ_by_year, liver_severe_and_group))

rows.sort(key=lambda r: (r[0], r[2], r[3] or ""))

with open(out_path, "w") as f:
    f.write("index,category,year,and_group,icd9_codes,icd10_codes\n")
    for index, label, year, and_group, codes in rows:
        f.write(f"{index},{label},{year},{and_group or ''},,{codes}\n")

print(f"Wrote {len(rows)} rows to {out_path}")
