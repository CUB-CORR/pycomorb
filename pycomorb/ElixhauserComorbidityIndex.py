# Reference for ECI:
# 1. van Walraven C, Austin PC, Jennings A, Quan H, Forster AJ.
#    A modification of the Elixhauser comorbidity measures into a point system for hospital death using administrative data.
#    Med Care. 2009 Jun;47(6):626-33.
#    doi: 10.1097/MLR.0b013e31819432e5. PMID: 19433995.
# 2. Elixhauser A, Steiner C, Harris DR, Coffey RM.
#    Comorbidity measures for use with administrative data.
#    Med Care. 1998 Jan;36(1):8-27.
#    doi: 10.1097/00005650-199801000-00004. PMID: 9431328.
#
# Reference for ICD-9-CM and ICD-10 Coding Algorithms for Elixhauser Comorbidities:
# 3. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA.
#    Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data.
#    Med Care. 2005 Nov;43(11):1130-9.
#    doi: 10.1097/01.mlr.0000182534.19832.83. PMID: 16224307.
# 4. Agency for Healthcare Research and Quality. Elixhauser Comorbidity Software, Version 3.7 (ICD-9-CM).
#    https://hcup-us.ahrq.gov/toolssoftware/comorbidity/comorbidity.jsp#download (implementation='ahrq_icd9')
# 5. Agency for Healthcare Research and Quality. Elixhauser Comorbidity Software Refined for ICD-10-CM, v2026.1.
#    https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp#down (implementation='ahrq_icd10')

import warnings
from pathlib import Path

import polars as pl

from .CustomComorbidityIndex import CustomComorbidityIndex

SCORE_COL_NAME = "Elixhauser Comorbidity Index"


def ElixhauserComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    icd_version_col: str | None = None,
    year_col: str | None = None,
    implementation: str = "quan",
    weights: str = "van_walraven",
    return_categories=False,
):
    """Calculate the Elixhauser Comorbidity Index (ECI) using ICD codes.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col`` and ``code_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        year_col (str, optional): Column name with each record's diagnosis year. Required when ``implementation`` is ``"ahrq_icd10"`` (ignored otherwise), since its POA-exemption changelog is year-specific. Defaults to ``None``.
        implementation (str, optional): Definition set to use; ``"quan"``, ``"elixhauser"``, ``"ahrq_icd9"``, or ``"ahrq_icd10"``. Defaults to ``"quan"``.
        weights (str, optional): Weighting scheme; one of ``"van_walraven"``, ``"thompson_30"``, ``"thompson_29"``, ``"ahrq"``, or ``"swiss"``. ``"ahrq"`` uses ``icd_version`` to pick ``ahrq_icd9_weights``/``ahrq_icd10_weights``; ``implementation="ahrq_icd9"``/``"ahrq_icd10"`` enforce it regardless of this argument. Defaults to ``"van_walraven"``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each Elixhauser category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the calculated score column, and, when ``return_categories`` is ``True``, category indicators.

    Raises:
        AssertionError: If ``implementation`` or ``weights`` is outside the supported values, or if ``implementation="ahrq_icd10"`` and ``year_col`` is missing.
        ValueError: If an unsupported ``implementation`` or ``weights`` argument passes validation safeguards.
    """

    # Change ICD to ICD-9 for original Elixhauser and AHRQ ICD-9
    if icd_version in ("icd10", "icd9_10") and implementation in [
        "elixhauser",
        "ahrq_icd9",
    ]:
        warnings.warn(
            f"Implementation '{implementation}' only uses ICD-9. Setting ICD version to 'icd9'.",
            UserWarning,
            stacklevel=2
        )
        icd_version = "icd9"
    # Change ICD to ICD-10 for AHRQ ICD-10
    if icd_version in ("icd9", "icd9_10") and implementation in ["ahrq_icd10"]:
        warnings.warn(
            f"Implementation '{implementation}' only uses ICD-10. Setting ICD version to 'icd10'.",
            UserWarning,
            stacklevel=2
        )
        icd_version = "icd10"

    # Input validation specific to Elixhauser
    assert implementation in [
        "quan",
        "elixhauser",
        "ahrq_icd9",
        "ahrq_icd10",
    ], "implementation must be one of: 'quan', 'elixhauser', 'ahrq_icd9', or 'ahrq_icd10'."
    assert weights in [
        "van_walraven",
        "thompson_30",
        "thompson_29",
        "ahrq",
        "swiss",
    ], "weights must be one of: 'van_walraven', 'thompson_30', 'thompson_29', 'ahrq', or 'swiss'."
    if implementation == "ahrq_icd10":
        assert year_col is not None and year_col in df.columns, "Implementation 'ahrq_icd10' requires a 'year_col' column (diagnosis year) in the input DataFrame." # fmt: skip

    # Determine definition file based on implementation
    if implementation == "quan":
        definition_file = "ELIXHAUSER_QUAN.csv"
    elif implementation == "elixhauser":
        definition_file = "ELIXHAUSER.csv"
    elif implementation == "ahrq_icd9":
        definition_file = "ELIXHAUSER_AHRQ_ICD9.csv"
    elif implementation == "ahrq_icd10":
        definition_file = "ELIXHAUSER_AHRQ_ICD10.csv"
    else:
        # Should be caught by assert earlier, but as a safeguard
        raise ValueError(f"Unsupported implementation: {implementation}")

    # Determine weight column and score column names based on weights argument
    # AHRQ implementations always use their own AHRQ weights; icd_version
    # (forced above) picks between the ICD-9/ICD-10 column
    if implementation in ("ahrq_icd9", "ahrq_icd10") and weights and weights.lower() != "ahrq":
        warnings.warn(
            f"Implementation '{implementation}' requires 'ahrq' weights. Overriding weights='{weights}' with 'ahrq_weights'.",
            UserWarning,
            stacklevel=2
        )

    if implementation in ("ahrq_icd9", "ahrq_icd10") or weights == "ahrq":
        if icd_version not in ("icd9", "icd10"):
            raise ValueError("weights='ahrq' requires icd_version 'icd9' or 'icd10'.")
        weight_col_name = "ahrq_icd9_weights" if icd_version == "icd9" else "ahrq_icd10_weights"
    elif weights == "van_walraven":
        weight_col_name = "van_walraven_weights"
    elif weights == "thompson_30":
        weight_col_name = "thompson_30_weights"
    elif weights == "thompson_29":
        weight_col_name = "thompson_29_weights"
    elif weights == "swiss":
        weight_col_name = "swiss_weights"

    # Load definition and weight files
    base_path = Path(__file__).parent / "common"
    definition_file_path = base_path / definition_file
    weights_file_path = base_path / "ELIXHAUSER_WEIGHTS.csv"

    df_definitions = pl.read_csv(definition_file_path)
    df_weights = pl.read_csv(weights_file_path).drop("index")

    # Join definitions and weights
    # Ensure 'category' column exists in both for joining
    if (
        "category" not in df_definitions.columns
        or "category" not in df_weights.columns
    ):
        raise ValueError("Both definition and weight files must contain a 'category' column.") # fmt: skip

    # Perform the join
    df_combined = df_definitions.join(df_weights, on="category", how="left")

    # Define mutual exclusion rules for Elixhauser
    # Category names must match this implementation's own definition file
    if implementation == "ahrq_icd9":
        mutual_exclusion_rules = [
            ("Diabetes with chronic complications", "Diabetes without chronic complications"),
        ]
    elif implementation == "ahrq_icd10":
        # Liver/Renal severe-suppresses-mild matches AHRQ's own CMR_Mapping_Program
        mutual_exclusion_rules = [
            ("Diabetes with chronic complications", "Diabetes without chronic complications"),
            ("Hypertension, complicated", "Hypertension, uncomplicated"),
            ("Liver disease, moderate to severe", "Liver disease, mild"),
            ("Renal failure, severe", "Renal failure, moderate"),
        ]
    else:
        mutual_exclusion_rules = [
            ("Diabetes complicated", "Diabetes uncomplicated"),
            ("Hypertension complicated", "Hypertension uncomplicated"),
        ]

    # Call the generalized function with the combined DataFrame
    df_elixhauser = CustomComorbidityIndex(
        df=df,
        id_col=id_col,
        code_col=code_col,
        icd_version=icd_version,
        icd_version_col=icd_version_col,
        year_col=year_col if implementation == "ahrq_icd10" else None,
        definition_data=df_combined,
        weight_col_name=weight_col_name,
        score_col_name=SCORE_COL_NAME,
        mutual_exclusion_rules=mutual_exclusion_rules,
        return_categories=return_categories,
    )

    return df_elixhauser
