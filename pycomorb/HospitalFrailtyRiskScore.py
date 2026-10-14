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


DEFINITION_FILE = Path(__file__).parent / "common" / "HFRS.csv"
SCORE_COL_NAME = "HFRS Score"


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

    is_pandas = isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    assert icd_version == "icd10", "icd_version must be 'icd10' for HFRS."
    assert id_col in df.columns, f"Column '{id_col}' (ID) must be present in input DataFrame." # fmt: skip
    assert code_col in df.columns, f"Column '{code_col}' (ICD code) must be present in input DataFrame." # fmt: skip

    hfrs_df = CustomComorbidityIndex(
        df=df,
        id_col=id_col,
        code_col=code_col,
        icd_version=icd_version,
        definition_data=DEFINITION_FILE,
        weight_col_name="weight",
        score_col_name=SCORE_COL_NAME,
        return_categories=return_categories,
    ).with_columns(pl.col(SCORE_COL_NAME).round(1))

    return hfrs_df.to_pandas() if is_pandas else hfrs_df
