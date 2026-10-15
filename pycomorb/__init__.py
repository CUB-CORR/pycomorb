"""Top-level package for pycomorb."""

__author__ = """Finn S. Fassbender"""
__email__ = "research@finnfassbender.de"

from pathlib import Path

import pandas as pd
import polars as pl

from .CharlsonComorbidityIndex import CharlsonComorbidityIndex
from .Reporting import comorbidity_reporting, read_reporting
from .CombinedComorbidityScore import CombinedComorbidityScore
from .CustomComorbidityIndex import CustomComorbidityIndex
from .ElixhauserComorbidityIndex import ElixhauserComorbidityIndex
from .HospitalFrailtyRiskScore import HospitalFrailtyRiskScore
from .ICDModifications import get_icd10cm, get_icd10gm


def _as_definitions(definition_data, definition_file_path):
    """Definitions as a polars DataFrame or a Path, whichever way they were passed."""
    if definition_data is None:
        definition_data = definition_file_path
    if isinstance(definition_data, str):
        return Path(definition_data)
    if isinstance(definition_data, pd.DataFrame):
        return pl.from_pandas(definition_data)
    return definition_data


# modification name -> (mapping function, earliest target year)
MODIFICATIONS = {"icd10cm": (get_icd10cm, 2015), "icd10gm": (get_icd10gm, 2004)}


def _apply_modification(df, name, code_col, year_col, target_year, version_col=None):
    """Map ICD-10 codes to the target year (rows labelled ICD-9 in ``version_col`` keep their codes)."""
    if name.lower() not in MODIFICATIONS:
        raise ValueError(f"Unknown icd_modification: '{name}'. Currently, only 'icd10gm' and 'icd10cm' are supported.") # fmt: skip
    modify, first_year = MODIFICATIONS[name.lower()]
    target_year = target_year or first_year
    mapped_col = f"icd_{target_year}"
    is_icd9 = pl.lit(False) if version_col is None else pl.col(version_col).cast(str) == "ICD-9"
    icd10 = modify(df.filter(~is_icd9), code_col, year_col, target_year)
    icd9 = df.filter(is_icd9).with_columns(pl.col(code_col).alias(mapped_col))
    return pl.concat([icd10, icd9], how="diagonal_relaxed"), mapped_col


def comorbidity(
    score: str,
    df,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    year_col: str = "year",
    icd_version: str = "icd10",
    icd_version_col: str | None = None,
    icd_modification: str | None = None,
    icd_modification_target_year: int | None = None,
    implementation: str | None = None,
    weights: str | None = None,
    definition_data=None,
    definition_file_path: str | None = None,
    weight_col_name: str = "weights",
    score_col_name: str = "Custom Comorbidity Score",
    mutual_exclusion_rules: list[tuple[str, str]] | None = None,
    return_categories: bool = False,
):
    """Calculate a comorbidity or frailty score from ICD-coded data.

    Args:
        score (str): Name of the score to calculate. Supported values are ``"charlson"``, ``"elixhauser"``, ``"combined"``, ``"hfrs"``, and ``"custom"`` (case-insensitive and including common aliases such as ``"cci"`` or ``"eci"``).
        df (pl.DataFrame | pandas.DataFrame): Input data containing at least ``id_col`` and ``code_col``. Additional columns such as ``age_col`` or ``year_col`` are required depending on the chosen score.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        age_col (str, optional): Column name containing patient ages (required for Charlson calculations). Defaults to ``"age"``.
        year_col (str, optional): Column name containing the year of the ICD code (used when applying ICD modification transfer files). Defaults to ``"year"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels (required for ``"icd9_10"`` inputs). Defaults to ``None``.
        icd_modification (str, optional): ICD modification to apply (``"icd10gm"`` or ``"icd10cm"``). When provided, codes are mapped to the ``icd_modification_target_year``. Defaults to ``None``.
        icd_modification_target_year (int, optional): Target year for ICD modification mappings (ICD-10-GM: 2004-2026, ICD-10-CM: 2015-2027). Defaults to the earliest year of the chosen modification (``2004`` for ``"icd10gm"``, ``2015`` for ``"icd10cm"``).
        implementation (str, optional): Implementation variant for the selected score (for example ``"quan"``, ``"deyo"``, ``"elixhauser"``). Defaults to ``None``.
        weights (str, optional): Weighting scheme for the Elixhauser index. Defaults to ``None``.
        definition_data (pl.DataFrame | pandas.DataFrame | Path | str, optional): Definition table for custom indices, either as a DataFrame or a path to a CSV file. Defaults to ``None``.
        definition_file_path (str, optional): Path to a CSV containing custom index definitions. Ignored when ``definition_data`` is a DataFrame. Defaults to ``None``.
        weight_col_name (str, optional): Column name with weights in ``definition_data``. Defaults to ``"weights"``.
        score_col_name (str, optional): Column name assigned to the calculated score for custom indices. Defaults to ``"Custom Comorbidity Score"``.
        mutual_exclusion_rules (list[tuple[str, str]], optional): Mutually exclusive category pairs for custom indices, where the second entry is suppressed when the first is present. Both categories must exist in the definitions. Defaults to ``None``.
        return_categories (bool, optional): If ``True``, includes category indicator columns in the result. Defaults to ``False``.

    Returns:
        pl.DataFrame | pandas.DataFrame: DataFrame containing the calculated score and, when ``return_categories`` is ``True``, the category indicators. If the input was a pandas DataFrame, the output matches that type.

    Raises:
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

    # apply ICD modification if requested
    if icd_modification is not None and "10" in icd_version:
        version_col = icd_version_col if icd_version == "icd9_10" else None
        df, code_col = _apply_modification(
            df, icd_modification, code_col, year_col, icd_modification_target_year, version_col
        )

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
            year_col=year_col,
            implementation=implementation or "quan",
            weights=weights or "charlson",
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
            year_col=year_col,
            implementation=implementation or "quan",
            weights=weights or "van_walraven",
            return_categories=return_categories,
        )
    elif score in (
        "ccs",
        "combined",
        "combinedcomorbidityindex",
        "combined_comorbidity_index",
        "combinedcomorbidityscore",
        "combined_comorbidity_score",
        "gagne",
        "gagnecomorbidityindex",
        "gagne_comorbidity_index",
    ):
        return_df = CombinedComorbidityScore(
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
            definition_data=_as_definitions(definition_data, definition_file_path),
            year_col=year_col if year_col in df.columns else None,
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
