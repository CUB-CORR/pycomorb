# 1. download the AHRQ Elixhauser Comorbidity Software, Version 3.7 (ICD-9-CM)
#    from https://hcup-us.ahrq.gov/toolssoftware/comorbidity/comorbidity.jsp#download
# 2. place comformat2012-2015.txt and comindex2012-2015.txt into this folder
# 3. run this script from this folder: python clinicalmodification_ahrq_icd9.py
# 4. writes ../ELIXHAUSER_AHRQ_ICD9.csv and merges weights into ../ELIXHAUSER_WEIGHTS.csv
#    (as a new ahrq_icd9_weights column)

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "utils"))
from utils import (
    contract_codes,
    expand_sas_range,
    merge_weights,
    parse_sas_value_block,
    write_rows,
)

FORMAT_FILE = "comformat2012-2015.txt"
INDEX_FILE = "comindex2012-2015.txt"
DEFINITIONS_OUT = Path("../ELIXHAUSER_AHRQ_ICD9.csv")
WEIGHTS_FILE = Path("../ELIXHAUSER_WEIGHTS.csv")


format_text = Path(FORMAT_FILE).read_text(encoding="latin-1")
block_match = re.search(r"Value\s+\$RCOMFMT(.*?)\n\s*VALUE\s", format_text, re.IGNORECASE | re.DOTALL)
raw = parse_sas_value_block(block_match.group(1), expand_range=expand_sas_range)
raw = {label: sorted(set(codes)) for label, codes in raw.items()}

# comoanaly2012-2015.txt (lines ~212-238): redistributes these 10 temporary
# hypertension/CHF/renal-failure formats into the real categories below
TEMP_FORMAT_TARGETS = {
    "HTNPREG": ["HTNCX"],
    "HTNWOCHF": ["HTNCX"],
    "HTNWCHF": ["HTNCX", "CHF"],
    "HRENWORF": ["HTNCX"],
    "HRENWRF": ["HTNCX", "RENLFAIL"],
    "HHRWOHRF": ["HTNCX"],
    "HHRWCHF": ["HTNCX", "CHF"],
    "HHRWRF": ["HTNCX", "RENLFAIL"],
    "HHRWHRF": ["HTNCX", "CHF", "RENLFAIL"],
    "OHTNPREG": ["HTNCX"],
}

categories: dict[str, set[str]] = {
    label: set(codes) for label, codes in raw.items() if label not in TEMP_FORMAT_TARGETS
}
for temp_label, targets in TEMP_FORMAT_TARGETS.items():
    for target in targets:
        categories[target].update(raw[temp_label])

# comindex2012-2015.txt scores Hypertension as one combined variable (HTN_C);
# HTN and HTNCX stay separate rows below (both named "Hypertension", OR'd
# together by CustomComorbidityIndex) but share HTN_C's single weight
WEIGHT_LABEL = {"HTN": "HTN_C", "HTNCX": "HTN_C"}

# human-readable names, per comoanaly2012-2015.txt's LABEL block (typos fixed)
CATEGORY_NAMES = {
    "AIDS": "AIDS/HIV",
    "ALCOHOL": "Alcohol abuse",
    "ANEMDEF": "Deficiency anemia",
    "ARTH": "Rheumatoid arthritis/collagen vascular diseases",
    "BLDLOSS": "Blood loss anemia",
    "CHF": "Congestive heart failure",
    "CHRNLUNG": "Chronic pulmonary disease",
    "COAG": "Coagulopathy",
    "DEPRESS": "Depression",
    "DM": "Diabetes without chronic complications",
    "DMCX": "Diabetes with chronic complications",
    "DRUG": "Drug abuse",
    "HTN": "Hypertension",
    "HTNCX": "Hypertension",
    "HYPOTHY": "Hypothyroidism",
    "LIVER": "Liver disease",
    "LYMPH": "Lymphoma",
    "LYTES": "Fluid and electrolyte disorders",
    "METS": "Metastatic cancer",
    "NEURO": "Other neurological disorders",
    "OBESE": "Obesity",
    "PARA": "Paralysis",
    "PERIVASC": "Peripheral vascular disorders",
    "PSYCH": "Psychoses",
    "PULMCIRC": "Pulmonary circulation disorders",
    "RENLFAIL": "Renal failure",
    "TUMOR": "Solid tumor without metastasis",
    "ULCER": "Peptic ulcer disease excluding bleeding",
    "VALVE": "Valvular disease",
    "WGHTLOSS": "Weight loss",
}

assert set(categories) == set(CATEGORY_NAMES), set(categories) ^ set(CATEGORY_NAMES)

# --- mortality index weights (comindex2012-2015.txt mw* macros) ---
index_text = Path(INDEX_FILE).read_text(encoding="latin-1")
mortality = dict(re.findall(r"mw(\w+)\s*=\s*(-?\d+)\s*;", index_text))

weight_labels = {WEIGHT_LABEL.get(label, label) for label in categories}
assert set(mortality) == weight_labels, set(mortality) ^ weight_labels

# renamed categories merge into their existing ELIXHAUSER_WEIGHTS.csv row;
# only "Hypertension" (merged HTN+HTNCX) is genuinely new
WEIGHT_ALIASES, order_index = merge_weights(
    WEIGHTS_FILE,
    Path("../ELIXHAUSER_CATEGORY_ALIASES.yaml"),
    "ahrq_icd9",
    "ahrq_icd9_weights",
    categories,
    CATEGORY_NAMES,
    mortality,
    mortality_label=lambda label: WEIGHT_LABEL.get(label, label),
)

# order the definitions the same way ELIXHAUSER_WEIGHTS.csv orders categories;
# sort HTN before HTNCX so "Hypertension"'s two rows land in a stable order
rows = sorted(
    (
        (CATEGORY_NAMES[label], "|".join(sorted(contract_codes(codes))), label)
        for label, codes in categories.items()
    ),
    key=lambda r: (order_index[WEIGHT_ALIASES.get(r[0], r[0])], r[2]),
)
rows = [(category, codes) for category, codes, _label in rows]
write_rows(DEFINITIONS_OUT, ["category", "icd9_codes"], rows)

n_categories = len(set(CATEGORY_NAMES.values()))
print(f"Wrote {len(rows)} rows ({n_categories} categories) to {DEFINITIONS_OUT}")
for label, codes in sorted(categories.items(), key=lambda kv: CATEGORY_NAMES[kv[0]]):
    print(f"  {CATEGORY_NAMES[label]:55s} {len(codes):4d} codes")
print(f"Merged {n_categories} categories' weights into {WEIGHTS_FILE}")
