# shared by the modification_US/modification_DE/version_SE generation scripts

import re
from pathlib import Path

import polars as pl
import yaml


# drop codes whose shorter ancestor prefix is already present, and collapse
# complete digit-families (all 10 next-digit children of a prefix) into the
# prefix (e.g. 5000|5001|...|5009 -> 500); repeats until stable
def contract_codes(codes) -> set[str]:
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


def write_rows(path: Path, columns: list[str], rows: list[tuple]) -> None:
    pl.DataFrame(rows, schema=columns, orient="row").with_row_index("index").write_csv(path)


# merge per-category mortality weights into a shared *_WEIGHTS.csv, aliasing
# renamed categories onto their existing row (only genuinely new categories
# get a new row); returns (alias map, {category: row order}) for reuse
def merge_weights(
    weights_file: Path,
    aliases_file: Path,
    aliases_key: str,
    weight_column: str,
    categories: dict,
    category_names: dict,
    mortality: dict[str, str],
    mortality_label=lambda label: label,
) -> tuple[dict[str, str], dict[str, int]]:
    with open(aliases_file) as f:
        weight_aliases = yaml.safe_load(f)[aliases_key]

    existing = pl.read_csv(weights_file).drop("index").to_dicts()
    by_category = {row["category"]: row for row in existing}
    order = [row["category"] for row in existing]
    for label in categories:
        weight_category = weight_aliases.get(category_names[label], category_names[label])
        row = by_category.setdefault(weight_category, {"category": weight_category})
        row[weight_column] = int(mortality[mortality_label(label)])
        if weight_category not in order:
            order.append(weight_category)
    pl.DataFrame([by_category[c] for c in order]).with_row_index("index").write_csv(weights_file)
    return weight_aliases, {category: i for i, category in enumerate(order)}
