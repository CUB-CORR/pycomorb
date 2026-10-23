import warnings
from collections import defaultdict
from itertools import product
from pathlib import Path

import polars as pl
import yaml

from .ICDModifications import check_code_dtype, clean_code_expr


def coerce_icd_version(icd_version, implementation, icd9_only, icd10_only):
    """Replace an ICD version the implementation cannot use, with a warning."""
    if implementation in icd9_only:
        version, label = "icd9", "ICD-9"
    elif implementation in icd10_only:
        version, label = "icd10", "ICD-10"
    else:
        return icd_version
    if icd_version in ("icd9", "icd10", "icd9_10") and icd_version != version:
        warnings.warn(
            f"Implementation '{implementation}' only uses {label}. Setting ICD version to '{version}'.",
            UserWarning,
            stacklevel=3,
        )
        return version
    return icd_version


def weighted_definitions(prefix, definition_file, implementation, canonical_rules):
    """Definitions of a Charlson/Elixhauser implementation joined with its weights, plus its exclusion rules.

    ``prefix`` ("CHARLSON" or "ELIXHAUSER") names the weight and alias files; ``canonical_rules`` are
    (more severe, milder) pairs in canonical category names, translated to the implementation's own names.
    """
    base_path = Path(__file__).parent / "common"
    definitions = pl.read_csv(base_path / definition_file)
    weights = pl.read_csv(base_path / f"{prefix}_WEIGHTS.csv").drop("index")
    with open(base_path / f"{prefix}_CATEGORY_ALIASES.yaml") as f:
        aliases = yaml.safe_load(f).get(implementation, {})
    combined = (
        definitions.with_columns(pl.col("category").replace(aliases).alias("__weight_category__"))
        .join(weights.rename({"category": "__weight_category__"}), on="__weight_category__", how="left")
        .drop("__weight_category__")
    )
    canonical = {c: aliases.get(c, c) for c in combined["category"]}
    rules = [
        (severe, mild)
        for severe, mild in product(canonical, repeat=2)
        if (canonical[severe], canonical[mild]) in canonical_rules
    ]
    return combined, rules


def CustomComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    icd_version_col: str | None = None,
    definition_data: Path | pl.DataFrame | None = None,
    weight_col_name: str | None = None,
    score_col_name: str | None = None,
    mutual_exclusion_rules: list[tuple[str, str]] | None = None,
    year_col: str | None = None,
    return_categories=False,
) -> pl.DataFrame:
    """Compute a custom comorbidity score from ICD-coded input data.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col`` and ``code_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        definition_data (Path | pl.DataFrame, optional): Path to a CSV file or DataFrame containing category definitions and weights. May optionally include an ``and_group`` column: rows sharing a ``category`` and a non-empty ``and_group`` value must all be present (AND) for that group to count, OR'd into the category's normal presence; blank ``and_group`` behaves as before. Defaults to ``None``.
        weight_col_name (str, optional): Column name with weights inside ``definition_data``. Defaults to ``None``.
        score_col_name (str, optional): Column name assigned to the calculated score in the result. Defaults to ``None``.
        mutual_exclusion_rules (list[tuple[str, str]], optional): Pairs of mutually exclusive categories where the second entry is suppressed when the first is present. Defaults to ``None``.
        year_col (str, optional): Column name with each record's definition-catalogue year (e.g. ICD-10-GM catalogue year). When provided, ``definition_data`` must include a ``year`` column, and a code only matches a category as of the definition row's year onward (``df[year_col] >= definitions["year"]``). Defaults to ``None`` (year-independent matching, the historical behavior).
        return_categories (bool, optional): If ``True``, includes indicator columns for each matched category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the calculated score column, and, when ``return_categories`` is ``True``, category indicators.

    Patients without a usable code are kept with all categories 0.

    Raises:
        AssertionError: If required columns or definitions are missing, or if ``icd_version`` and ``icd_version_col`` are inconsistent.
        ValueError: If ``code_col`` holds numbers instead of strings, or if ``mutual_exclusion_rules`` name a category that is not in the definitions.
    """

    # Input validation
    assert icd_version in [
        "icd9",
        "icd10",
        "icd9_10",
    ], f"icd_version must be one of: 'icd9', 'icd10', or 'icd9_10'. Got '{icd_version}'."
    assert id_col in df.columns, f"Column '{id_col}' (ID) must be present in input DataFrame." # fmt: skip
    assert code_col in df.columns, f"Column '{code_col}' (ICD code) must be present in input DataFrame." # fmt: skip
    if icd_version == "icd9_10":
        assert icd_version_col is not None and icd_version_col in df.columns, f"For icd9_10, '{icd_version_col}' (ICD version) column must be present in input DataFrame." # fmt: skip

    # Load definitions
    if isinstance(definition_data, Path):
        definitions = pl.read_csv(definition_data, separator=",")
    else:
        definitions = definition_data

    assert (
        "category" in definitions.columns
    ), "'category' column not found in definition file."
    assert (
        weight_col_name in definitions.columns
    ), f"'{weight_col_name}' column not found in definition file."

    df = check_code_dtype(df, code_col)

    # Year gating only applies when both year_col and a year column are given
    year_aware = year_col is not None and "year" in definitions.columns

    def process_single_icd(df, icd_col_name):
        # Patients without a usable code stay in the result with all categories 0
        ids = df.select(id_col).unique()
        df = df.filter(pl.col(code_col).is_not_null())

        # Validation and cleaning only touch the unique codes, the diagnosis rows keep their
        # raw codes and are joined on them below. Blank codes match nothing.
        unique_codes = (
            df.select(code_col)
            .unique()
            .with_columns(clean_code_expr(code_col).alias("clean"))
            .filter(pl.col("clean") != "")
        )

        categories_list = definitions["category"].drop_nulls().unique(maintain_order=True).to_list()
        if unique_codes.is_empty():  # no codes of this ICD version: nothing present
            return ids.with_columns(pl.lit(0).cast(int).alias(c) for c in categories_list), categories_list

        # Prepare mapping DataFrame: prefix, bit, since. Every definition row is one bit in a
        # per-patient mask; a category is present if all bits of one of its groups are set,
        # where a group is a single row or the rows sharing an and_group.
        required, code_map_rows = defaultdict(lambda: defaultdict(int)), []
        for i, row in enumerate(definitions.iter_rows(named=True)):
            if row["category"] is None or row.get(icd_col_name) is None:
                continue
            bit = 1 << i
            required[row["category"]][row.get("and_group") or i] |= bit
            for code in row[icd_col_name].split("|"):
                code_map_rows.append(
                    {"prefix": code.strip(), "bit": bit, "since": row["year"] if year_aware else 0}
                )
        code_map = pl.DataFrame(code_map_rows)

        code_prefixes = code_map.select("prefix").to_series().to_list()
        longest_code = max(unique_codes["clean"].to_list(), key=len)

        # Create a DataFrame with all possible prefixes, then find the best match
        best_prefix = (
            unique_codes.with_columns(
                pl.col("clean").str.slice(0, n).alias(f"prefix_{n}")
                for n in range(1, len(longest_code) + 1)
            )
            .with_columns(
                pl.when(pl.col(f"prefix_{n}").is_in(code_prefixes))
                .then(pl.col(f"prefix_{n}"))
                .otherwise(None)
                .alias(f"prefix_{n}")
                for n in range(1, len(longest_code) + 1)
            )
            # Count ICD code as present for each comorbidity it matches
            .unpivot(
                on=[f"prefix_{n}" for n in range(1, len(longest_code) + 1)],
                index=code_col,
                value_name="best_prefix",
            )
            .drop_nulls("best_prefix")
            .select(code_col, "best_prefix")
            .unique()
        )

        # Join diagnoses with the bits of their code; only matching diagnoses are aggregated
        matches = df.join(
            best_prefix.join(
                code_map, left_on="best_prefix", right_on="prefix"
            ).select(code_col, "bit", "since"),
            on=code_col,
        )
        if year_aware:
            matches = matches.filter(pl.col(year_col) >= pl.col("since"))

        masks_by_id = matches.group_by(id_col).agg(pl.col("bit").bitwise_or().alias("mask"))
        df_presence_absence = (
            ids.join(masks_by_id, on=id_col, how="left")
            .with_columns(pl.col("mask").fill_null(0))
            .select(
                id_col,
                *(
                    pl.any_horizontal((pl.col("mask") & m) == m for m in masks.values())
                    .cast(int)
                    .alias(cat)
                    for cat, masks in required.items()
                ),
            )
        )

        # Add missing columns
        for cat in categories_list:
            if cat not in df_presence_absence.columns:
                df_presence_absence = df_presence_absence.with_columns(
                    pl.lit(0).cast(int).alias(cat)
                )
        df_presence_absence = df_presence_absence.select(
            [id_col] + categories_list
        )
        return df_presence_absence, categories_list

    if icd_version == "icd9_10":
        # Split by icd_version_col
        df_icd9 = df.filter(pl.col(icd_version_col).cast(str) == "ICD-9")
        df_icd10 = df.filter(pl.col(icd_version_col).cast(str) != "ICD-9")

        # Process each ICD version separately
        df9, cats9 = process_single_icd(df_icd9, "icd9_codes")
        df10, cats10 = process_single_icd(df_icd10, "icd10_codes")

        # Combine: outer join on id_col, take max for each category
        # Preserve definition file order instead of alphabetical sorting
        all_categories_set = set(cats9) | set(cats10)
        all_categories = [
            cat
            for cat in dict.fromkeys(definitions["category"].to_list())
            if cat in all_categories_set and cat is not None
        ]
        df_combined = df9.join(
            df10, on=id_col, how="full", suffix="_right", coalesce=True
        )
        # both halves report every category, so each has a "_right" counterpart
        df_presence_absence = df_combined.select(
            id_col,
            *(pl.max_horizontal(cat, f"{cat}_right").alias(cat) for cat in all_categories),
        )
    else:
        icd_col_name = f"{icd_version}_codes"
        df_presence_absence, all_categories = process_single_icd(
            df, icd_col_name
        )

    # STEP 2: calculate score
    category_weights = dict(
        zip(definitions["category"], definitions[weight_col_name])
    )
    category_weights = {
        k: v
        for k, v in category_weights.items()
        if k is not None and v is not None
    }

    # Apply mutual exclusion rules
    for complicated, uncomplicated in mutual_exclusion_rules or []:
        unknown = {complicated, uncomplicated} - set(df_presence_absence.columns)
        if unknown:
            raise ValueError(f"mutual_exclusion_rules refer to unknown categories: {sorted(unknown)}.") # fmt: skip
        df_presence_absence = df_presence_absence.with_columns(
            pl.when(pl.col(complicated) == 1)
            .then(0)
            .otherwise(pl.col(uncomplicated))
            .alias(uncomplicated)
        )

    # calculate scores
    # Ensure weights are applied only to existing category columns that have weights
    score_expr = pl.sum_horizontal(
        pl.col(cat) * category_weights.get(cat, 0)
        for cat in all_categories
        if cat in df_presence_absence.columns and cat in category_weights
    ).alias(score_col_name)

    cols = [id_col] + all_categories if return_categories else [id_col]
    return df_presence_absence.select(*cols, score_expr)
