# 1. download the AHRQ Elixhauser Comorbidity Software, Version 3.7 (ICD-9-CM)
#    from https://hcup-us.ahrq.gov/toolssoftware/comorbidity/comorbidity.jsp#download
# 2. place comformat2012-2015.txt and comindex2012-2015.txt into this folder
# 3. run this script from this folder: python clinicalmodification_ahrq_icd9.py
# 4. writes ../ELIXHAUSER_AHRQ_ICD9.csv and merges weights into ../ELIXHAUSER_WEIGHTS.csv
#    (as a new ahrq_icd9_weights column)

import re
from pathlib import Path

import polars as pl
import yaml

FORMAT_FILE = "comformat2012-2015.txt"
INDEX_FILE = "comindex2012-2015.txt"
DEFINITIONS_OUT = Path("../ELIXHAUSER_AHRQ_ICD9.csv")
WEIGHTS_FILE = Path("../ELIXHAUSER_WEIGHTS.csv")


# parse a SAS 'Value $NAME ... ;' PROC FORMAT body into {label: [codes]};
# handles both quote styles and, if expand_range is given, dash-ranges
# like "4280 "-"4289 " = "CHF"
def parse_sas_value_block(text: str, expand_range=None) -> dict[str, list[str]]:
    text = re.sub(r"other\s*=\s*[\"'][^\"']*[\"']\s*;?", "", text, flags=re.IGNORECASE)
    tokens = list(re.finditer(r"[\"']([^\"']*)[\"']", text))
    groups: dict[str, list[str]] = {}
    pending: list[str] = []
    i = 0
    while i < len(tokens):
        value = tokens[i].group(1).strip()
        preceding = text[tokens[i - 1].end() if i > 0 else 0 : tokens[i].start()]
        if "=" in preceding:
            groups.setdefault(value, []).extend(pending)
            pending = []
            i += 1
            continue
        if expand_range is not None and i + 1 < len(tokens):
            between = text[tokens[i].end() : tokens[i + 1].start()]
            if between.strip() == "-":
                pending.extend(expand_range(value, tokens[i + 1].group(1).strip()))
                i += 2
                continue
        pending.append(value)
        i += 1
    return groups


# expand a SAS $CHAR dash-range (e.g. '4280'-'4289', 'V560'-'V5632') by padding
# the shorter bound with trailing zeros and enumerating integers
def expand_sas_range(lo: str, hi: str) -> list[str]:
    prefix = ""
    while lo and hi and lo[0] == hi[0] and lo[0].isalpha():
        prefix += lo[0]
        lo, hi = lo[1:], hi[1:]
    width = max(len(lo), len(hi))
    lo_n, hi_n = int(lo.ljust(width, "0")), int(hi.ljust(width, "0"))
    return [f"{prefix}{n:0{width}d}" for n in range(lo_n, hi_n + 1)]


# drop codes whose shorter ancestor prefix is already present, and collapse
# complete digit-families (all 10 next-digit children of a prefix) into the
# prefix (e.g. 5000|5001|...|5009 -> 500); repeats until stable
def contract_codes(codes: set[str]) -> set[str]:
    codes = set(codes)
    changed = True
    while changed:
        changed = False

        ordered = sorted(codes, key=len)
        kept: list[str] = []
        for code in ordered:
            if not any(code != k and code.startswith(k) for k in kept):
                kept.append(code)
        if len(kept) != len(codes):
            codes, changed = set(kept), True

        by_prefix: dict[str, set[str]] = {}
        for code in codes:
            if len(code) > 1:
                by_prefix.setdefault(code[:-1], set()).add(code)
        for prefix, group in by_prefix.items():
            if {c[-1] for c in group} == set("0123456789"):
                codes -= group
                codes.add(prefix)
                changed = True

    return codes


def write_rows(path: Path, columns: list[str], rows: list[tuple]) -> None:
    pl.DataFrame(rows, schema=columns, orient="row").with_row_index("index").write_csv(path)


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
with open("../ELIXHAUSER_CATEGORY_ALIASES.yaml") as f:
    WEIGHT_ALIASES = yaml.safe_load(f)["ahrq_icd9"]

existing = pl.read_csv(WEIGHTS_FILE).drop("index").to_dicts()
by_category = {row["category"]: row for row in existing}
order = [row["category"] for row in existing]
for label in categories:
    weight_category = WEIGHT_ALIASES.get(CATEGORY_NAMES[label], CATEGORY_NAMES[label])
    row = by_category.setdefault(weight_category, {"category": weight_category})
    row["ahrq_icd9_weights"] = int(mortality[WEIGHT_LABEL.get(label, label)])
    if weight_category not in order:
        order.append(weight_category)
pl.DataFrame([by_category[c] for c in order]).with_row_index("index").write_csv(WEIGHTS_FILE)

# order the definitions the same way ELIXHAUSER_WEIGHTS.csv orders categories;
# sort HTN before HTNCX so "Hypertension"'s two rows land in a stable order
order_index = {category: i for i, category in enumerate(order)}
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
