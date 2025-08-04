"""Top-level package for comorbidipy."""

__author__ = """Finn Fassbender"""
__email__ = "finn.fassbender@charite.de"
__version__ = "0.4.1"

from .CharlsonComorbidityIndex import CharlsonComorbidityIndex
from .ElixhauserComorbidityIndex import ElixhauserComorbidityIndex
from .GagneComorbidityIndex import GagneComorbidityIndex
from .HospitalFrailtyRiskScore import HospitalFrailtyRiskScore


def comorbidity(
    score: str,
    df,
    id_col="id",
    code_col="code",
    age_col="age",
    icd_version="icd10",
    icd_version_col=None,
    implementation=None,
    weights=None,
    return_categories=False,
):
    """
    Unified wrapper to calculate a comorbidity or frailty score.

    Args:
        score (str): Which score to calculate.
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col] (and age_col for Charlson).
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        age_col (str): Name of the column containing patient ages (Charlson only). Default: "age".
        icd_version (str): ICD version. Default: "icd10".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        implementation (str, optional): Implementation variant (see individual index docs).
        weights (str, optional): Weighting scheme (Elixhauser only).
        return_categories (bool): Whether to return category indicators.

    Returns:
        - DataFrame with [id_col, score].
        - DataFrame with category indicators if return_categories is True, else None.
    """
    score = score.lower()
    if score in (
        "cci",
        "charlson",
        "charlsoncomorbidityindex",
        "charlson_comorbidity_index",
    ):
        if age_col not in df.columns:
            raise ValueError(
                f"Column '{age_col}' (age) must be present in input DataFrame for Charlson calculation."
            )
        return CharlsonComorbidityIndex(
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
        return ElixhauserComorbidityIndex(
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
        return GagneComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            return_categories=return_categories,
        )
    elif score in (
        "hfrs",
        "hospitalfrailtyriskscore",
        "hospital_frailty_risk_score",
    ):
        return HospitalFrailtyRiskScore(
            df=df,
            id_col=id_col,
            code_col=code_col,
            icd_version=icd_version,
            return_categories=return_categories,
        )
    else:
        raise ValueError(
            f"Unknown score: '{score}'. Must be one of: "
            "'charlson', 'elixhauser', 'gagne', 'hfrs'."
        )
