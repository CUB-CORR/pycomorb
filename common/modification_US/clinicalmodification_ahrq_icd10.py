# 1. download the "Elixhauser Comorbidity Software Refined for ICD-10-CM"
#    (most recent version) from
#    https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp#down
# 2. unzip it into a CMR-vYYYY-N folder next to this script (update VERSION
#    below for a different version) so that CMR_Format_Program_vYYYY-N.sas,
#    CMR_Mapping_Program_vYYYY-N.sas and CMR_Index_Program_vYYYY-N.sas sit inside it
# 3. run this script from this folder: python clinicalmodification_ahrq_icd10.py
# 4. writes ../ELIXHAUSER_AHRQ_ICD10.csv and merges weights into ../ELIXHAUSER_WEIGHTS.csv
#    (as a new ahrq_icd10_weights column)
#
# Year handling: $COMFMT (the categories) is static across all covered years --
# the only year-dependence is the 11 yearly $POAXMPT_VxxFMT "present on
# admission" exemption lists for the 19 POA-dependent categories. year below
# is a cumulative changelog of when each code entered its category's
# POA-exempt list (same shape as ELIXHAUSER_QUAN.csv); all codes are always
# included, never-exempt ones just get the baseline year.

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
from utils import (
    contract_codes,
    merge_weights,
    parse_sas_value_block,
    write_rows,
)

VERSION = "v2026-1"
VERSION_DIR = f"CMR-{VERSION}"
FORMAT_FILE = f"{VERSION_DIR}/CMR_Format_Program_{VERSION}.sas"
INDEX_FILE = f"{VERSION_DIR}/CMR_Index_Program_{VERSION}.sas"
DEFINITIONS_OUT = Path("../ELIXHAUSER_AHRQ_ICD10.csv")
WEIGHTS_FILE = Path("../ELIXHAUSER_WEIGHTS.csv")

# CMR_Mapping_Program_vYYYY-N.sas (lines ~110-132): YEAR/DQTR -> ICD-10-CM
# code-set version (ICDVER), one $POAXMPT_VxxFMT POA-exemption format per
# version (FY2016 through FY2026).
ICDVER_YEAR = {
    33: 2016, 34: 2017, 35: 2018, 36: 2019, 37: 2020, 38: 2021, 39: 2022,
    40: 2023, 41: 2024, 42: 2025, 43: 2026,
}  # fmt: skip


def extract_value_block(text: str, name: str) -> str:
    match = re.search(
        rf"Value\s+\${name}\b(.*?)(?=\n\s*Value\s+\$|\Z)", text, re.IGNORECASE | re.DOTALL
    )
    if not match:
        raise ValueError(f"could not find Value ${name} block in {FORMAT_FILE}")
    return match.group(1)


format_text = Path(FORMAT_FILE).read_text(encoding="latin-1")

comfmt = {
    label: sorted(set(codes))
    for label, codes in parse_sas_value_block(extract_value_block(format_text, "COMFMT")).items()
}

poa_exempt: dict[int, set[str]] = {
    version: set(
        parse_sas_value_block(extract_value_block(format_text, f"POAXMPT_V{version}FMT")).get("1", [])
    )
    for version in ICDVER_YEAR
}

# CMR_Mapping_Program_vYYYY-N.sas (lines ~235-291): 10 of the 49 $COMFMT
# labels concatenate two categories a code belongs to at once (SAS format
# values can't overlap) -- each contributes its codes to every target below.
COMBO_TARGETS = {
    "DRUG_ABUSEPSYCHOSES": ["DRUG_ABUSE", "PSYCHOSES"],
    "HFHTN_CX": ["HTN_CX", "HF"],
    "HTN_CXRENLFL_SEV": ["HTN_CX", "RENLFL_SEV"],
    "HFHTN_CXRENLFL_SEV": ["HTN_CX", "HF", "RENLFL_SEV"],
    "ALCOHOLLIVER_MLD": ["ALCOHOL", "LIVER_MLD"],
    "VALVE_AUTOIMMUNE": ["AUTOIMMUNE", "VALVE"],
    "CBVD_SQLAPARALYSIS": ["PARALYSIS", "CBVD_SQLA"],
    "LIVER_MLD_NEURO": ["LIVER_MLD", "NEURO_OTH"],
    "NEURO_OTH_SEIZ": ["NEURO_OTH", "NEURO_SEIZ"],
    "LIVER_MLD_PULMCIRC": ["LIVER_MLD", "PULMCIRC"],
}

categories: dict[str, set[str]] = {
    label: set(codes) for label, codes in comfmt.items() if label not in COMBO_TARGETS
}
for combo_label, targets in COMBO_TARGETS.items():
    for target in targets:
        categories[target].update(comfmt[combo_label])

# CMR_Mapping_Program_vYYYY-N.sas (lines 153-159, VALANYPOA/VALPOA arrays):
# the 20 POA-neutral and 19 POA-dependent raw categories. CBVD_POA and
# CBVD_SQLA (two of the 19) are merged below into one CBVD category, matching
# how the mapping program derives a single CMR_CBVD flag from their union.
NEUTRAL_LABELS = [
    "AIDS", "ALCOHOL", "AUTOIMMUNE", "LUNG_CHRONIC", "DEMENTIA", "DEPRESS", "DIAB_UNCX", "DIAB_CX",
    "DRUG_ABUSE", "HTN_UNCX", "HTN_CX", "THYROID_HYPO", "THYROID_OTH", "CANCER_LYMPH", "CANCER_LEUK",
    "CANCER_METS", "OBESE", "PERIVASC", "CANCER_SOLID", "CANCER_NSITU",
]  # fmt: skip
DEPENDENT_LABELS = [
    "ANEMDEF", "BLDLOSS", "HF", "COAG", "LIVER_MLD", "LIVER_SEV", "NEURO_MOVT", "NEURO_SEIZ",
    "NEURO_OTH", "PARALYSIS", "PSYCHOSES", "PULMCIRC", "RENLFL_MOD", "RENLFL_SEV", "ULCER_PEPTIC",
    "WGHTLOSS", "VALVE",
]  # fmt: skip  (+ CBVD, appended below once CBVD_POA/CBVD_SQLA are merged)

all_labels = set(NEUTRAL_LABELS) | set(DEPENDENT_LABELS) | {"CBVD_POA", "CBVD_SQLA"}
assert all_labels == set(categories), all_labels ^ set(categories)

categories["CBVD"] = categories.pop("CBVD_POA") | categories.pop("CBVD_SQLA")
DEPENDENT_LABELS = DEPENDENT_LABELS + ["CBVD"]

# human-readable names, per CMR_Mapping_Program_vYYYY-N.sas's LABEL block
# (lines 326-368); ULCER_PEPTIC covers both bleeding and non-bleeding
# subtypes (K25-K28), so it's named plainly rather than "x excluding bleeding"
CATEGORY_NAMES = {
    "AIDS": "Acquired immune deficiency syndrome",
    "ALCOHOL": "Alcohol abuse",
    "ANEMDEF": "Anemias due to other nutritional deficiencies",
    "AUTOIMMUNE": "Autoimmune conditions",
    "BLDLOSS": "Chronic blood loss anemia (iron deficiency)",
    "CANCER_LEUK": "Leukemia",
    "CANCER_LYMPH": "Lymphoma",
    "CANCER_METS": "Metastatic cancer",
    "CANCER_NSITU": "Solid tumor without metastasis, in situ",
    "CANCER_SOLID": "Solid tumor without metastasis, malignant",
    "CBVD": "Cerebrovascular disease",
    "HF": "Heart failure",
    "COAG": "Coagulopathy",
    "DEMENTIA": "Dementia",
    "DEPRESS": "Depression",
    "DIAB_CX": "Diabetes with chronic complications",
    "DIAB_UNCX": "Diabetes without chronic complications",
    "DRUG_ABUSE": "Drug abuse",
    "HTN_CX": "Hypertension, complicated",
    "HTN_UNCX": "Hypertension, uncomplicated",
    "LIVER_MLD": "Liver disease, mild",
    "LIVER_SEV": "Liver disease, moderate to severe",
    "LUNG_CHRONIC": "Chronic pulmonary disease",
    "NEURO_MOVT": "Neurological disorders affecting movement",
    "NEURO_OTH": "Other neurological disorders",
    "NEURO_SEIZ": "Seizures and epilepsy",
    "OBESE": "Obesity",
    "PARALYSIS": "Paralysis",
    "PERIVASC": "Peripheral vascular disease",
    "PSYCHOSES": "Psychoses",
    "PULMCIRC": "Pulmonary circulation disease",
    "RENLFL_MOD": "Renal failure, moderate",
    "RENLFL_SEV": "Renal failure, severe",
    "THYROID_HYPO": "Hypothyroidism",
    "THYROID_OTH": "Other thyroid disorders",
    "ULCER_PEPTIC": "Peptic ulcer disease",
    "VALVE": "Valvular disease",
    "WGHTLOSS": "Weight loss",
}
assert set(categories) == set(CATEGORY_NAMES), set(categories) ^ set(CATEGORY_NAMES)

# --- mortality index weights (mw* macros) ---
index_text = Path(INDEX_FILE).read_text(encoding="latin-1")
mortality = dict(re.findall(r"mw(\w+)\s*=\s*(-?\d+)\s*;", index_text))

assert set(mortality) == set(categories), set(mortality) ^ set(categories)

# renamed categories merge into their existing ELIXHAUSER_WEIGHTS.csv row;
# only genuinely new categories (Liver/Renal/Neuro splits, Dementia, ...) get a new row
WEIGHT_ALIASES, order_index = merge_weights(
    WEIGHTS_FILE,
    Path("../ELIXHAUSER_CATEGORY_ALIASES.yaml"),
    "ahrq_icd10",
    "ahrq_icd10_weights",
    categories,
    CATEGORY_NAMES,
    mortality,
)

BASELINE_YEAR = ICDVER_YEAR[33]
rows: list[tuple[str, int, list[str]]] = []
for label in NEUTRAL_LABELS:
    rows.append((CATEGORY_NAMES[label], BASELINE_YEAR, sorted(contract_codes(categories[label]))))

gated_to_later_year: dict[str, int] = {}
for label in DEPENDENT_LABELS:
    codes = categories[label]
    first_exempt_year: dict[str, int] = {}
    for version, year in ICDVER_YEAR.items():
        for code in codes & poa_exempt[version]:
            first_exempt_year.setdefault(code, year)
    never_exempt = codes - set(first_exempt_year)
    gated_to_later_year[label] = sum(1 for y in first_exempt_year.values() if y > BASELINE_YEAR)
    by_year: dict[int, list[str]] = {}
    for code, year in first_exempt_year.items():
        by_year.setdefault(year, []).append(code)
    by_year.setdefault(BASELINE_YEAR, []).extend(never_exempt)
    for year in sorted(by_year):
        rows.append((CATEGORY_NAMES[label], year, sorted(contract_codes(by_year[year]))))

# order the definitions the same way ELIXHAUSER_WEIGHTS.csv orders categories
rows.sort(key=lambda r: (order_index[WEIGHT_ALIASES.get(r[0], r[0])], r[1]))
rows = [(category, year, None, "|".join(codes)) for category, year, codes in rows]
write_rows(DEFINITIONS_OUT, ["category", "year", "and_group", "icd10_codes"], rows)

print(f"Wrote {len(rows)} rows ({len(categories)} categories) to {DEFINITIONS_OUT}")
for label in NEUTRAL_LABELS:
    print(f"  {CATEGORY_NAMES[label]:55s} {len(categories[label]):5d} codes (POA-neutral)")
for label in DEPENDENT_LABELS:
    total = len(categories[label])
    later = gated_to_later_year[label]
    print(
        f"  {CATEGORY_NAMES[label]:55s} {total:5d} codes "
        f"(POA-dependent, {later} gated to a year after {BASELINE_YEAR})"
    )
print(f"Merged {len(categories)} categories' weights into {WEIGHTS_FILE}")
