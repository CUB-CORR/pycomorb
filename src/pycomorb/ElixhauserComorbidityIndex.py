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
# 4. Original Elixhauser definitions (used when implementation='elixhauser')
# 5. AHRQ definitions (used when implementation='ahrq_icd9' or 'ahrq_icd10')

from pathlib import Path

import pandas as pd
import polars as pl

# Import the generalized function
from .CustomComorbidityIndex import CustomComorbidityIndex


def ElixhauserComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd10",
    icd_version_col: str = None,
    implementation: str = "quan",
    weights: str = "van_walraven",
    return_categories=False,
):
    """
    Calculate the Elixhauser Comorbidity Index (ECI) using ICD codes.

    Args:
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col].
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        icd_version (str): ICD version ('icd9', 'icd10', or 'icd9_10'). Default: "icd10".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        implementation (str): Coding algorithm ('quan' or 'elixhauser'). Default: "quan".
        weights (str): Weighting scheme ('van_walraven', 'thompson_30', 'thompson_29', 'ahrq'). Default: "van_walraven".
        return_categories (bool): If True, also return presence indicators for each ECI category.

    Returns:
        - DataFrame with [id_col, score_col_name].
        - DataFrame with category indicators if return_categories is True, else None.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    # Change ICD to ICD-9 for original Elixhauser and AHRQ ICD-9
    if icd_version == "icd10" and implementation in [
        "elixhauser",
        "ahrq_icd9",
    ]:
        print(f"Warning: Implementation '{implementation}' only uses ICD-9. Setting ICD version to 'icd9'.")  # fmt: skip
        icd_version = "icd9"
    # Change ICD to ICD-10 for AHRQ ICD-10
    if icd_version == "icd9" and implementation in ["ahrq_icd10"]:
        print(f"Warning: Implementation '{implementation}' only uses ICD-10. Setting ICD version to 'icd10'.") # fmt: skip
        icd_version = "icd10"

    # Input validation specific to Elixhauser
    assert implementation in [
        "quan",
        "elixhauser",
    ], "implementation must be one of: 'quan', 'elixhauser'."
    assert weights in [
        "van_walraven",
        "thompson_30",
        "thompson_29",
        "ahrq",
    ], "weights must be one of: 'van_walraven', 'thompson_30', 'thompson_29', or 'ahrq'."

    # Determine definition file based on implementation
    if implementation == "quan":
        definition_file = "ELIXHAUSER_QUAN.csv"
    elif implementation == "elixhauser":
        definition_file = "ELIXHAUSER.csv"
    else:
        # Should be caught by assert earlier, but as a safeguard
        raise ValueError(f"Unsupported implementation: {implementation}")

    # Determine weight column and score column names based on weights argument
    if weights == "van_walraven":
        weight_col_name = "van_walraven_weights"
        score_col_name = "Elixhauser van Walraven Score"
    elif weights == "thompson_30":
        weight_col_name = "Thompson_30_weights"
        score_col_name = "Elixhauser Thompson(30) Score"
    elif weights == "thompson_29":
        weight_col_name = "Thompson_29_weights"
        score_col_name = "Elixhauser Thompson(29) Score"
    elif weights == "ahrq":
        weight_col_name = "AHRQ_weights"
        score_col_name = "Elixhauser AHRQ Score"
    else:
        # Should be caught by assert earlier, but as a safeguard
        raise ValueError(f"Unsupported weights scheme: {weights}")

    # Load definition and weight files
    base_path = Path(__file__).parent / "common/"
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
        definition_data=df_combined,
        weight_col_name=weight_col_name,
        score_col_name=score_col_name,
        mutual_exclusion_rules=mutual_exclusion_rules,
        return_categories=return_categories,
    )

    if is_pandas:
        return df_elixhauser.to_pandas()

    return df_elixhauser
