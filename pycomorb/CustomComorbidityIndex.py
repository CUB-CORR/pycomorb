from pathlib import Path
from typing import List, Optional, Tuple, Union

import polars as pl


def CustomComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    icd_version_col: str = None,
    definition_data: Union[Path, pl.DataFrame] = None,
    weight_col_name: str = None,
    score_col_name: str = None,
    mutual_exclusion_rules: Optional[List[Tuple[str, str]]] = None,
    return_categories=False,
):
    """Compute a custom comorbidity score from ICD-coded input data.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col`` and ``code_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        definition_data (Path | pl.DataFrame, optional): Path to a CSV file or DataFrame containing category definitions and weights. Defaults to ``None``.
        weight_col_name (str, optional): Column name with weights inside ``definition_data``. Defaults to ``None``.
        score_col_name (str, optional): Column name assigned to the calculated score in the result. Defaults to ``None``.
        mutual_exclusion_rules (list[tuple[str, str]], optional): Pairs of mutually exclusive categories where the second entry is suppressed when the first is present. Defaults to ``None``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each matched category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the calculated score column, and, when ``return_categories`` is ``True``, category indicators.

    Raises:
        AssertionError: If required columns or definitions are missing, or if ``icd_version`` and ``icd_version_col`` are inconsistent.
    """

    # Input validation
    assert icd_version in [
        "icd9",
        "icd10",
        "icd9_10",
    ], f"icd_version must be one of: 'icd9', 'icd10', or 'icd9_10'. Got '{icd_version}'."
    assert (
        code_col in df.columns
    ), f"Column '{code_col}' (ICD code) must be present in input DataFrame."
    assert (
        id_col in df.columns
    ), f"Column '{id_col}' (ID) must be present in input DataFrame."
    if icd_version == "icd9_10":
        assert (
            icd_version_col is not None and icd_version_col in df.columns
        ), f"For icd9_10, '{icd_version_col}' (ICD version) column must be present in input DataFrame."

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

    # Drop rows from df with missing codes
    df = df.filter(pl.col(code_col).is_not_null())

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
        longest_code = max(unique_codes.to_series().to_list(), key=len)

        # Create a DataFrame with all possible prefixes, then find the best match
        best_prefix = (
            unique_codes.with_columns(
                pl.col(code_col).str.slice(0, n).alias(f"prefix_{n}")
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
            .with_columns(
                pl.concat_list(
                    pl.col(f"prefix_{n}")
                    for n in range(1, len(longest_code) + 1)
                )
                .list.drop_nulls()
                .list.unique()
                .alias("best_prefixes")
            )
            .explode("best_prefixes")
            .rename({"best_prefixes": "best_prefix"})
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

    if icd_version == "icd9_10":
        # Split by icd_version_col
        df_icd9 = df.filter(pl.col(icd_version_col).cast(str) == "ICD-9")
        df_icd10 = df.filter(pl.col(icd_version_col).cast(str) != "ICD-9")

        # Process each ICD version separately
        df9, cats9 = process_single_icd(df_icd9, "icd9_codes")
        df10, cats10 = process_single_icd(df_icd10, "icd10_codes")

        # Combine: outer join on id_col, take max for each category
        all_categories = sorted(set(cats9) | set(cats10))
        df_combined = df9.join(
            df10, on=id_col, how="outer", suffix="_right", coalesce=True
        )
        for cat in all_categories:
            left = cat
            right = f"{cat}_right"
            if left in df_combined.columns and right in df_combined.columns:
                df_combined = df_combined.with_columns(
                    pl.max_horizontal(pl.col(left), pl.col(right)).alias(cat)
                )
            elif right in df_combined.columns:
                df_combined = df_combined.rename({right: cat})
        df_presence_absence = df_combined.select([id_col] + all_categories)
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
    if mutual_exclusion_rules:
        for complicated, uncomplicated in mutual_exclusion_rules:
            if (
                complicated in df_presence_absence.columns
                and uncomplicated in df_presence_absence.columns
            ):
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
    comorbidity_df = df_presence_absence.select(*cols, score_expr).cast(
        {score_col_name: int}
    )

    return comorbidity_df
