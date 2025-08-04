# Reference for HFRS:
# 1. Gilbert T, Neuburger J, Kraindler J, Keeble E, Smith P, Ariti C, Arora S,
#    Street A, Parker S, Roberts HC, Bardsley M, Conroy S. Development and
#    validation of a Hospital Frailty Risk Score focusing on older people in
#    acute care settings using electronic hospital records: an observational
#    study. Lancet. 2018 May 5;391(10132):1775-1782.
#    doi: 10.1016/S0140-6736(18)30668-8. Epub 2018 Apr 26. PMID: 29706364;
#    PMCID: PMC5946808.

from pathlib import Path

import pandas as pd
import polars as pl


def HospitalFrailtyRiskScore(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    return_categories=False,
):
    """
    Calculate the Hospital Frailty Risk Score (HFRS) using ICD-10 codes.

    Args:
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col].
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        icd_version (str): ICD version ('icd10'). HFRS requires ICD-10. Default: "icd10".
        return_categories (bool): If True, also return presence indicators for each HFRS category.

    Returns:
        - DataFrame with [id_col, "HFRS Score"].
        - DataFrame with category indicators if return_categories is True, else None.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    # Input validation
    assert icd_version == "icd10", "icd_version must be 'icd10' for HFRS."
    assert (
        code_col in df.columns
    ), f"Column '{code_col}' (ICD code) must be present in input DataFrame."
    assert (
        id_col in df.columns
    ), f"Column '{id_col}' (ID) must be present in input DataFrame."

    # Drop rows from df with missing codes
    df = df.filter(pl.col(code_col).is_not_null())

    # Load definitions
    definition_file = "HFRS.csv"
    definition_file_path = Path(__file__).parent / f"common/{definition_file}"
    definitions = pl.read_csv(definition_file_path, separator=",")

    assert (
        "category" in definitions.columns
    ), "'category' column not found in definition file."
    assert (
        "weight" in definitions.columns
    ), "'weight' column not found in definition file."

    def process_single_icd(df, icd_col_name):
        # Prepare mapping DataFrame: code_col, category
        code_map_rows = []
        for row in definitions.iter_rows(named=True):
            if row["category"] is None or row.get(icd_col_name) is None:
                continue
            for code in row[icd_col_name].split("|"):
                code_map_rows.append(
                    {"prefix": code.strip(), "category": row["category"]}
                )
        code_map = pl.DataFrame(code_map_rows)

        # Create dataframe with presence indicators
        categories = code_map.select("category").unique()
        categories_list = categories.to_series().to_list()
        categories_df = categories.with_columns(
            pl.when(pl.col("category") == category)
            .then(pl.lit(1))
            .otherwise(pl.lit(0))
            .alias(category)
            for category in categories_list
        )

        # Get all unique ICD codes in the data
        code_prefixes = code_map.select("prefix").to_series()
        unique_codes = df.select(code_col).unique()
        code_list = [
            str(c) for c in unique_codes[code_col].to_list() if c is not None
        ]
        if code_list:
            longest_code_len = max((len(c) for c in code_list), default=1)
        else:
            longest_code_len = 1

        # Create a DataFrame with all possible prefixes, then find the best match
        best_prefix = (
            unique_codes.with_columns(
                pl.col(code_col).str.slice(0, n).alias(f"prefix_{n}")
                for n in range(1, longest_code_len + 1)
            )
            .with_columns(
                pl.when(pl.col(f"prefix_{n}").is_in(code_prefixes))
                .then(pl.col(f"prefix_{n}"))
                .otherwise(None)
                .alias(f"prefix_{n}")
                for n in range(1, longest_code_len + 1)
            )
            .with_columns(
                pl.coalesce(
                    *[
                        pl.col(f"prefix_{n}")
                        for n in range(longest_code_len, 0, -1)
                    ]
                ).alias("best_prefix")
            )
            .select(code_col, "best_prefix")
            .drop_nulls("best_prefix")
        )

        code_to_category = (
            best_prefix.join(
                code_map, left_on="best_prefix", right_on="prefix", how="left"
            )
            .select(code_col, "category")
            .join(categories_df, on="category", how="left")
            .select(code_col, *categories_list)
        )

        # Join diagnoses with code_to_category to get the best matching category for each diagnosis
        df_presence_absence = (
            df.join(code_to_category, on=code_col, how="left")
            .group_by(id_col)
            .agg(pl.max(cat).fill_null(0).alias(cat) for cat in categories_list)
        )

        # Add missing columns
        for cat in categories_list:
            if cat not in df_presence_absence.columns:
                df_presence_absence = df_presence_absence.with_columns(
                    pl.lit(0).alias(cat)
                )
        df_presence_absence = df_presence_absence.select(
            [id_col] + categories_list
        )
        return df_presence_absence, categories_list

    # Only ICD-10 supported for HFRS
    df_presence_absence, all_categories = process_single_icd(df, "icd10_codes")

    # STEP 2: calculate HFRS score
    category_weights = dict(zip(definitions["category"], definitions["weight"]))
    category_weights = {
        k: v
        for k, v in category_weights.items()
        if k is not None and v is not None
    }

    score_expr = (
        pl.sum_horizontal(
            pl.col(cat) * category_weights.get(cat, 0)
            for cat in all_categories
            if cat in df_presence_absence.columns and cat in category_weights
        )
        .round(1)
        .alias("HFRS Score")
    )

    cols = [id_col] + all_categories if return_categories else [id_col]
    hfrs_df = df_presence_absence.select(*cols, score_expr).cast(
        {"HFRS Score": float}
    )

    if is_pandas:
        return hfrs_df.to_pandas()

    return hfrs_df
