# 1. clone https://github.com/bjoroeKI/Charlson-comorbidity-index-revisited into this
#    folder so that Charlson-comorbidity-index-revisited/Charlson_SAS sits next to this
#    script (not included in the repository)
# 2. run this script from this folder: python sweden.py
# 3. writes ../CHARLSON_SWEDEN.csv

import re
from pathlib import Path

import polars as pl

SOURCE_FILE = "Charlson-comorbidity-index-revisited/Charlson_SAS"
OUT_PATH = Path("../CHARLSON_SWEDEN.csv")

# SAS variable name -> (index, label), index matches CHARLSON_SWEDEN.csv's existing rows
CATEGORIES = {
    "myocardial_infarction":  (1, "Myocardial infarction"),
    "chf":                    (2, "Congestive heart failure"),
    "peripheral_vascular":    (3, "Peripheral vascular disease"),
    "cerebrovascular":        (4, "Cerebrovascular disease"),
    "dementia":               (5, "Dementia"),
    "copd":                   (6, "Chronic obstructive pulmonary disease (COPD)"),
    "other_cpd":              (7, "Other chronic pulmonary disease"),
    "rheumatic":              (8, "Rheumatic disease"),
    "ulcer":                  (9, "(Peptic) Ulcer disease"),
    "mild_liver_disease":    (10, "Mild liver disease"),
    "diabetes":              (11, "Diabetes"),
    "diabetes_eod":          (12, "Diabetes with end organ damage"),
    "hemiplegia":            (13, "Hemiplegia, tetraplegia"),
    "severe_kidney_disease": (14, "Moderate or severe kidney disease"),
    "malignancy":            (15, "Any malignancy, including lymphoma and leukemia"),
    "severe_liver_disease":  (16, "Moderate or severe liver disease"),
    "metastatic_cancer":     (17, "Metastatic cancer"),
    "aids":                  (18, "AIDS/HIV"),
} # fmt: skip


# drop any code whose shorter ancestor prefix is already present
def contract_codes(codes) -> set[str]:
    ordered = sorted(set(codes), key=len)
    kept: list[str] = []
    for code in ordered:
        if not any(code != k and code.startswith(k) for k in kept):
            kept.append(code)
    return set(kept)


# slice text between marker and next_marker, or the block's closing END; if next_marker is omitted
def extract_section(text: str, marker: str, next_marker: str | None = None) -> str:
    start = text.index(marker) + len(marker)
    end = text.index(next_marker, start) if next_marker else text.index("\n\tEND;", start)
    return text[start:end]


# parse a block's 'IN: (...) then _name = 1' statements into {name: codes}
def parse_categories(block: str) -> dict[str, set[str]]:
    categories: dict[str, set[str]] = {}
    for codes_blob, name in re.findall(r"IN:\s*\((.*?)\)\s*then\s*_(\w+)\s*=\s*1", block, re.DOTALL):
        categories.setdefault(name, set()).update(re.findall(r"'([^']*)'", codes_blob))
    # liver_special (R18/789F, ascites) upgrades mild to severe liver disease when both
    # are present on one patient; fold it into severe since categories here are patient-independent
    categories["severe_liver_disease"] |= categories.pop("liver_special")
    assert set(categories) == set(CATEGORIES), set(categories) ^ set(CATEGORIES)
    return categories


text = Path(SOURCE_FILE).read_text()
# only ICD-9 (1987-1997)/ICD-10 (1997-) blocks are parsed; icd9_codes is kept only as a
# historical record, since the 'sweden' implementation itself is ICD-10-only at runtime
categories_by_version = {
    "icd9_codes": parse_categories(extract_section(text, "*--- ICD9 ---*;", "*--- ICD10 ---*;")),
    "icd10_codes": parse_categories(extract_section(text, "*--- ICD10 ---*;")),
}

rows = [(0, "Age", "XXXX|XXXX", "YYYY|YYYY")]
for name, (index, label) in sorted(CATEGORIES.items(), key=lambda kv: kv[1][0]):
    rows.append((
        index,
        label,
        "|".join(sorted(contract_codes(categories_by_version["icd9_codes"][name]))),
        "|".join(sorted(contract_codes(categories_by_version["icd10_codes"][name]))),
    ))

pl.DataFrame(
    rows, schema=["index", "category", "icd9_codes", "icd10_codes"], orient="row"
).write_csv(OUT_PATH)

print(f"Wrote {len(rows)} rows ({len(CATEGORIES)} categories) to {OUT_PATH}")
for name, (index, label) in sorted(CATEGORIES.items(), key=lambda kv: kv[1][0]):
    n9 = len(categories_by_version["icd9_codes"][name])
    n10 = len(categories_by_version["icd10_codes"][name])
    print(f"  {label:55s} {n9:3d} ICD-9 codes, {n10:3d} ICD-10 codes")
