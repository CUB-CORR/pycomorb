# 1. download the most current ICD-10-CM conversion table from https://www.cms.gov/medicare/coding-billing/icd-10-codes
# 2. unzip them into the folder where this script is located
# 3. run this script in that folder

import re

import polars as pl

INPUT_FILE = "508-compliant-version-ICD_10_CM_CONVERSION_TABLE_FY2026.txt"
OUTPUT_FILE = "icd10cm.csv"
START_YEAR = 15  # 2015 as 16
END_YEAR = 26  # 2026 as 26


def split_codes(codes):
    # Split a string of codes into a list, handling multi-code delimiters and ranges
    if not codes:
        return []

    codes = codes.replace('"', "").replace("'", "")
    codes = re.sub(r"\s*(,|;|&| and | AND | And |\band\b)\s*", ",", codes)
    parts = []

    for part in codes.split(","):
        part = part.strip()
        m = re.match(r"([A-Z0-9.]+)-([A-Z0-9.]+)", part)

        if m and len(m.group(1)) == len(m.group(2)):
            prefix = re.match(r"([A-Z.]+)([0-9]+)", m.group(1))
            suffix = re.match(r"([A-Z.]+)([0-9]+)", m.group(2))

            if prefix and suffix and prefix.group(1) == suffix.group(1):
                start = int(prefix.group(2))
                end = int(suffix.group(2))

                for i in range(start, end + 1):
                    parts.append(f"{prefix.group(1)}{i}")

            else:
                parts.append(part)

        else:
            parts.append(part)

    return [
        c.strip()
        for c in parts
        if c.strip()
        and not c.lower().startswith("a code from")
        and not c.lower().startswith("code from")
        and not c.lower().startswith("codes in categories")
    ]


def clean_column(col: pl.Expr, year: int = None):
    return (
        col.str.replace_all(r"\.", "")
        .str.to_uppercase()
        .replace("NONE", f"UNDEF{year}")
    )


# Read as TSV, skip first two lines, use third as header
df = pl.read_csv(
    INPUT_FILE,
    separator="\t",
    skip_rows=2,
    has_header=True,
    new_columns=["current_code", "effective", "previous_codes"],
    schema_overrides={
        "current_code": pl.Utf8,
        "effective": pl.Utf8,
        "previous_codes": pl.Utf8,
    },
)


# --- Build wide table by year, left-joining each year's mapping ---
years = list(range(START_YEAR, END_YEAR + 1))
year_cols = [str(2000 + y) for y in years]

# Start with all unique codes from the first year as the base DataFrame
codes_first = (
    df.filter(pl.col("effective").str.ends_with(str(2000 + START_YEAR)))
    .select("current_code", "previous_codes")
    .with_columns(
        pl.col("current_code")
        .pipe(clean_column, year=2000 + START_YEAR)
        .alias(str(2000 + START_YEAR)),
        pl.col("previous_codes")
        .map_elements(lambda x: split_codes(x)[0] if split_codes(x) else None)
        .pipe(clean_column, year=2000 + START_YEAR)
        .alias("prev"),
    )
    .select(str(2000 + START_YEAR))
    .unique()
)
df_wide = codes_first

for i, y in enumerate(years[:-1]):
    next_year = y + 1
    # Filter for mappings for this transition
    year_df = (
        df.filter(pl.col("effective").str.ends_with(str(2000 + next_year)))
        .select("current_code", "previous_codes")
        .with_columns(
            pl.col("current_code")
            .pipe(clean_column, year=2000 + START_YEAR)
            .alias(str(2000 + next_year)),
            pl.col("previous_codes")
            .map_elements(
                lambda x: split_codes(x)[0] if split_codes(x) else None
            )
            .pipe(clean_column, year=2000 + START_YEAR)
            .alias(str(2000 + y)),
        )
        .select(str(2000 + y), str(2000 + next_year))
        .unique()
    )
    # Left join on previous year
    df_wide = df_wide.join(year_df, on=str(2000 + y), how="full", coalesce=True)

# Propagate codes forward to fill in unmapped codes
for y in year_cols[1:]:
    df_wide = df_wide.with_columns(
        pl.when(pl.col(y).is_null())
        .then(pl.col(year_cols[year_cols.index(y) - 1]))
        .otherwise(pl.col(y))
        .alias(y)
    )
# Propagate codes backward to fill in unmapped codes
for y in reversed(year_cols[:-1]):
    df_wide = df_wide.with_columns(
        pl.when(pl.col(y).is_null())
        .then(pl.col(year_cols[year_cols.index(y) + 1]))
        .otherwise(pl.col(y))
        .alias(y)
    )


(
    # Drop rows where all codes stay the same across all years (polars-native)
    df_wide.with_columns(
        pl.concat_list([pl.col(y) for y in year_cols])
        .list.n_unique()
        .alias("n_unique")
    )
    .filter(pl.col("n_unique") > 1)
    .drop("n_unique")
    # Write to CSV (years as columns, no code column, just years)
    .write_csv(OUTPUT_FILE)
)
