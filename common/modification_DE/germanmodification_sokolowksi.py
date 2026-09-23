# 1. clone https://github.com/fabiansiegel/comorbidity_score/ into this folder
#    (ships year-specific ICD-10-GM mapping JSONs in comorbidity_score_calc/mappings/)
# 2. run this script from this folder: python germanmodification_sokolowksi.py
# 3. writes ../CHARLSON_SOKOLOWSKI.csv

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
from utils import contract_codes, write_rows

# ICD-10-GM catalogue years covered by comorbidity_score's mapping JSONs
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
# and_group key: liver_severe only counts when both its cause and organ-damage codes are present
liver_severe_and_group = "liver_severe_and"


# codes come dotted (e.g. 'I25.20'); the rest of pycomorb matches undotted prefixes
def strip_dots(codes):
    return {code.replace(".", "") for code in codes}


# union of every 'any'-condition code group's flat code list
def flatten_any_codes(category_def):
    codes = set()
    for group in category_def["codes"]:
        if group["condition"] == "any":
            codes.update(group["codes"])
    return strip_dots(codes)


# the two subgroup lists of the (single) 'both'-condition group, if any
def flatten_both_subgroups(category_def):
    for group in category_def["codes"]:
        if group["condition"] == "both":
            cause, organ = group["codes"]
            return strip_dots(cause), strip_dots(organ)
    return set(), set()


# load one year's ICD-10-GM code -> Charlson category mapping
def load_year(year):
    with open(source_dir / f"charlson_icd10gm_{year}.json") as f:
        return json.load(f)["mapping"]


# emit a row only where the contracted code set gains prefixes versus the previous year
def changelog_rows(index, label, raw_by_year, and_group=None):
    rows = []
    cumulative_raw = set()
    previous_contracted = set()
    for year in years:
        cumulative_raw |= raw_by_year[year]
        contracted = contract_codes(cumulative_raw)
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

# group each category's changelog rows together, in year order
rows.sort(key=lambda r: (r[0], r[2], r[3] or ""))

write_rows(
    out_path,
    ["category", "year", "and_group", "icd9_codes", "icd10_codes"],
    [(label, year, and_group, None, codes) for _, label, year, and_group, codes in rows],
)

print(f"Wrote {len(rows)} rows to {out_path}")
