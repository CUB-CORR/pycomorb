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

from .CustomComorbidityIndex import CustomComorbidityIndex


def HospitalFrailtyRiskScore(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    return_categories=False,
):
    """Calculate the Hospital Frailty Risk Score (HFRS) using ICD-10 codes.

    Args:
        df (pl.DataFrame | pd.DataFrame): Input data containing at least ``id_col`` and ``code_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        icd_version (str, optional): ICD version; must be ``"icd10"``. Defaults to ``"icd10"``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each HFRS category. Defaults to ``False``.

    Returns:
        pl.DataFrame | pd.DataFrame: DataFrame containing ``id_col``, the ``"HFRS Score"`` column, and, when ``return_categories`` is ``True``, category indicators.

    Raises:
        AssertionError: If ``icd_version`` is not ``"icd10"`` or required columns are missing.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    # Input validation
    assert icd_version == "icd10", "icd_version must be 'icd10' for HFRS."
    assert id_col in df.columns, f"Column '{id_col}' (ID) must be present in input DataFrame." # fmt: skip
    assert code_col in df.columns, f"Column '{code_col}' (ICD code) must be present in input DataFrame." # fmt: skip

    # Drop rows from df with missing codes
    df = df.filter(pl.col(code_col).is_not_null())

    # Load definitions
    definition_file = "HFRS.csv"
    definition_file_path = Path(__file__).parent / "common" / definition_file
    definitions = pl.read_csv(definition_file_path, separator=",")

    assert (
        "category" in definitions.columns
    ), "'category' column not found in definition file."
    assert (
        "weight" in definitions.columns
    ), "'weight' column not found in definition file."

    # Only ICD-10 supported for HFRS
    def detect_categories(chunk):
        return CustomComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            definition_data=chunk,
            weight_col_name="weight",
            score_col_name="HFRS Score",
            return_categories=True,
        ).drop("HFRS Score")

    # CustomComorbidityIndex handles at most 63 definition rows, HFRS.csv has 109
    all_categories = definitions["category"].to_list()
    df_presence_absence = detect_categories(definitions[:63]).join(
        detect_categories(definitions[63:]), on=id_col
    )

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
