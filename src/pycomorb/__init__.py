"""Top-level package for comorbidipy."""

__author__ = """Finn Fassbender"""
__email__ = "finn.fassbender@charite.de"
__version__ = "0.6"

import pandas as pd
import polars as pl

from .CharlsonComorbidityIndex import CharlsonComorbidityIndex
from .CustomComorbidityIndex import CustomComorbidityIndex
from .ElixhauserComorbidityIndex import ElixhauserComorbidityIndex
from .GagneComorbidityIndex import GagneComorbidityIndex
from .HospitalFrailtyRiskScore import HospitalFrailtyRiskScore
from .ICDModifications import get_icd10cm, get_icd10gm


def comorbidity(
    score: str,
    df,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    year_col: str = "year",
    icd_version: str = "icd10",
    icd_version_col: str = None,
    icd_modification: str = None,
    icd_modification_target_year: int = 2004,
    implementation: str = None,
    weights: str = None,
    definition_data=None,
    definition_file_path: str = None,
    weight_col_name: str = "weights",
    score_col_name: str = "Custom Comorbidity Score",
    mutual_exclusion_rules: list[tuple[str, str]] = None,
    return_categories: bool = False,
    fix_dot_in_icd_code: bool = False,
):
    """
    Unified wrapper to calculate a comorbidity or frailty score.

    Args:
        score (str): Which score to calculate.
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col] (and age_col for Charlson).
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        age_col (str): Name of the column containing patient ages (Charlson only). Default: "age".
        year_col (str): Name of the column containing the year of the ICD code (for ICD history modifications). Default: "year".
        icd_version (str): ICD version. Must be one of: 'icd9', 'icd10', or 'icd9_10'. Default: "icd10".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        icd_modification (str, optional): ICD modification to apply ('icd10gm'). Default: None.
        icd_modification_target_year (int): Target year for ICD modification (if applicable). Default: 2004.
        implementation (str, optional): Implementation variant (see individual index docs).
        weights (str, optional): Weighting scheme (Elixhauser only).
        definition_data (DataFrame, optional): DataFrame with ICD definitions and weights (Custom only).
        definition_file_path (str, optional): Path to CSV with ICD definitions and weights (Custom only).
        weight_col_name (str): Name of the column with weights in definition_data (Custom only).
        score_col_name (str): Name for the calculated score column (Custom only).
        mutual_exclusion_rules (list of tuple, optional): List of mutually exclusive category pairs (Custom only).
        return_categories (bool): Whether to return category indicators.
        fix_dot_in_icd_code (bool): Whether to remove dots from ICD codes before processing. Default: False.

    Returns:
        - DataFrame with [id_col, score].
        - DataFrame with category indicators if return_categories is True, else None.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    # remove dots from ICD codes if requested
    if fix_dot_in_icd_code:
        df = df.with_columns(
            pl.col(code_col).str.replace(".", "", literal=True)
        )

    # check that no dots are present in ICD codes (Polars-native)
    contains_dot = df.select(
        pl.col(code_col).str.contains(r"\.").any().alias("contains_dot")
    ).to_dicts()[0]["contains_dot"]
    assert (
        not contains_dot
    ), f"All values in column '{code_col}' must not contain dots ('.'). Consider setting fix_dot_in_icd_code=True."
    
    # strip whitespace from ICD codes, and make uppercase
    df = df.with_columns(
        pl.col(code_col).str.strip_chars().str.to_uppercase()
    )

    # apply ICD modification if requested
    if icd_modification is not None and "10" in icd_version:
        if icd_modification.lower() == "icd10cm":
            df = get_icd10cm(
                data=df,
                code_col=code_col,
                year_col=year_col,
                target_year=icd_modification_target_year,
            )
            code_col = f"icd_{icd_modification_target_year}"
        elif icd_modification.lower() == "icd10gm":
            df = get_icd10gm(
                data=df,
                code_col=code_col,
                year_col=year_col,
                target_year=icd_modification_target_year,
            )
            code_col = f"icd_{icd_modification_target_year}"
        else:
            raise ValueError(f"Unknown icd_modification: '{icd_modification}'. Currently, only 'icd10gm' and 'icd10cm' are supported.") # fmt: skip

    # calculate scores
    score = score.lower()
    if score in (
        "cci",
        "charlson",
        "charlsoncomorbidityindex",
        "charlson_comorbidity_index",
    ):
        if age_col not in df.columns:
            raise ValueError(f"Column '{age_col}' (age) must be present in input DataFrame for Charlson calculation.") # fmt: skip
        return_df = CharlsonComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            age_col=age_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            implementation=implementation or "quan",
            return_categories=return_categories,
        )
    elif score in (
        "eci",
        "elixhauser",
        "elixhausercomorbidityindex",
        "elixhauser_comorbidity_index",
    ):
        return_df = ElixhauserComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            implementation=implementation or "quan",
            weights=weights or "van_walraven",
            return_categories=return_categories,
        )
    elif score in (
        "gci",
        "gagne",
        "gagnecomorbidityindex",
        "gagne_comorbidity_index",
        "combined",
        "combinedcomorbidityindex",
        "combined_comorbidity_index",
    ):
        return_df = GagneComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            return_categories=return_categories,
            gagne_name="gagne" in score,
        )
    elif score in (
        "hfrs",
        "hospitalfrailtyriskscore",
        "hospital_frailty_risk_score",
    ):
        return_df = HospitalFrailtyRiskScore(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            return_categories=return_categories,
        )
    elif score in (
        "custom",
        "customcomorbidityindex",
        "custom_comorbidity_index",
    ):
        return_df = CustomComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            definition_data=definition_data or definition_file_path,
            weight_col_name=weight_col_name,
            score_col_name=score_col_name,
            mutual_exclusion_rules=mutual_exclusion_rules,
            return_categories=return_categories,
        )
    else:
        raise ValueError(
            f"Unknown score: '{score}'. Must be one of: "
            "'charlson', 'elixhauser', 'gagne', 'hfrs' or 'custom'."
        )

    if is_pandas:
        return return_df.to_pandas()

    return return_df
