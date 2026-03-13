"""Top-level package for comorbidipy."""

__author__ = """Finn S. Fassbender"""
__email__ = "finn.fassbender@charite.de"
__version__ = "v1.20260401.0"

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
    """Calculate a comorbidity or frailty score from ICD-coded data.

    Args:
        score (str): Name of the score to calculate. Supported values are ``"charlson"``, ``"elixhauser"``, ``"gagne"``, ``"hfrs"``, and ``"custom"`` (case-insensitive and including common aliases such as ``"cci"`` or ``"eci"``).
        df (pl.DataFrame | pandas.DataFrame): Input data containing at least ``id_col`` and ``code_col``. Additional columns such as ``age_col`` or ``year_col`` are required depending on the chosen score.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        age_col (str, optional): Column name containing patient ages (required for Charlson calculations). Defaults to ``"age"``.
        year_col (str, optional): Column name containing the year of the ICD code (used when applying ICD modification transfer files). Defaults to ``"year"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels (required for ``"icd9_10"`` inputs). Defaults to ``None``.
        icd_modification (str, optional): ICD modification to apply (``"icd10gm"`` or ``"icd10cm"``). When provided, codes are mapped to the ``icd_modification_target_year``. Defaults to ``None``.
        icd_modification_target_year (int, optional): Target year for ICD modification mappings. Defaults to ``2004``.
        implementation (str, optional): Implementation variant for the selected score (for example ``"quan"``, ``"deyo"``, ``"elixhauser"``). Defaults to ``None``.
        weights (str, optional): Weighting scheme for the Elixhauser index. Defaults to ``None``.
        definition_data (pl.DataFrame | pandas.DataFrame | Path | str, optional): Definition table for custom indices, either as a DataFrame or a path to a CSV file. Defaults to ``None``.
        definition_file_path (str, optional): Path to a CSV containing custom index definitions. Ignored when ``definition_data`` is a DataFrame. Defaults to ``None``.
        weight_col_name (str, optional): Column name with weights in ``definition_data``. Defaults to ``"weights"``.
        score_col_name (str, optional): Column name assigned to the calculated score for custom indices. Defaults to ``"Custom Comorbidity Score"``.
        mutual_exclusion_rules (list[tuple[str, str]], optional): Mutually exclusive category pairs for custom indices, where the second entry is suppressed when the first is present. Defaults to ``None``.
        return_categories (bool, optional): If ``True``, includes category indicator columns in the result. Defaults to ``False``.
        fix_dot_in_icd_code (bool, optional): If ``True``, removes dots from ICD codes prior to processing. Defaults to ``False``.

    Returns:
        pl.DataFrame | pandas.DataFrame: DataFrame containing the calculated score and, when ``return_categories`` is ``True``, the category indicators. If the input was a pandas DataFrame, the output matches that type.

    Raises:
        AssertionError: If ICD codes contain dots when ``fix_dot_in_icd_code`` is ``False``.
        ValueError: If the requested ``score`` or ``icd_modification`` is not supported, or required columns are missing.

    Example:
        Compute a Charlson score with category indicators and automatic ICD-10-GM harmonization:

        >>> import polars as pl
        >>> from pycomorb import comorbidity
        >>> diagnoses = pl.DataFrame(
        ...     {
        ...         "id": [1, 1, 2],
        ...         "code": ["I21", "E119", "C349"],
        ...         "age": [66, 66, 81],
        ...         "year": [2012, 2012, 2010],
        ...     }
        ... )
        >>> comorbidity(
        ...     score="charlson",
        ...     df=diagnoses,
        ...     icd_version="icd10",
        ...     icd_modification="icd10gm",
        ...     return_categories=True,
        ... )
        shape: (2, 22)
        ┌─────┬───────────────────────┬──────────────────────────┬───┬───────────┬────────────────┐
        │ id  ┆ Myocardial infarction ┆ Congestive heart failure ┆ … ┆ Age Score ┆ Charlson Score │
        │ --- ┆ ---                   ┆ ---                      ┆   ┆ ---       ┆ ---            │
        │ i64 ┆ i32                   ┆ i32                      ┆   ┆ i64       ┆ i64            │
        ╞═════╪═══════════════════════╪══════════════════════════╪═══╪═══════════╪════════════════╡
        │ 1   ┆ 1                     ┆ 0                        ┆ … ┆ 1         ┆ 3              │
        │ 2   ┆ 0                     ┆ 0                        ┆ … ┆ 2         ┆ 4              │
        └─────┴───────────────────────┴──────────────────────────┴───┴───────────┴────────────────┘
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
