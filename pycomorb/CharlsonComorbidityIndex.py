# Reference for CCI:
# 1. Charlson ME, Pompei P, Ales KL, MacKenzie CR.
#    A new method of classifying prognostic comorbidity in longitudinal studies: development and validation.
#    J Chronic Dis. 1987;40(5):373-83.
#    doi: 10.1016/0021-9681(87)90171-8. PMID: 3558716.
# 2. Charlson M, Szatrowski TP, Peterson J, Gold J.
#    Validation of a combined comorbidity index.
#    J Clin Epidemiol. 1994 Nov;47(11):1245-51.
#    doi: 10.1016/0895-4356(94)90129-5. PMID: 7722560.
#
# Reference for ICD-9-CM and ICD-10 Coding Algorithms for Charlson Comorbidities:
# 3. Deyo RA, Cherkin DC, Ciol MA.
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative databases.
#    J Clin Epidemiol. 1992 Jun;45(6):613-9.
#    doi: 10.1016/0895-4356(92)90133-8. PMID: 1607900.
# 4. Romano PS, Roos LL, Jollis JG.
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative data: differing perspectives.
#    J Clin Epidemiol. 1993 Oct;46(10):1075-9; discussion 1081-90.
#    doi: 10.1016/0895-4356(93)90103-8. PMID: 8410092.
# 5. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA.
#    Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data.
#    Med Care. 2005 Nov;43(11):1130-9.
#    doi: 10.1097/01.mlr.0000182534.19832.83. PMID: 16224307.
# 7. Armitage JN, van der Meulen JH; Royal College of Surgeons Co-morbidity Consensus Group.
#    Identifying co-morbidity in surgical patients using administrative data with the Royal College of Surgeons Charlson Score.
#    Br J Surg. 2010 May;97(5):772-81.
#    doi: 10.1002/bjs.6930. PMID: 20306528.
# 8. Thygesen SK, Christiansen CF, Christensen S, Lash TL, Sørensen HT.
#    The predictive value of ICD-10 diagnostic coding used to assess Charlson comorbidity index conditions in the population-based Danish National Registry of Patients.
#    BMC Med Res Methodol. 2011 Dec;11(1):83.
#    doi: 10.1186/1471-2288-11-83.

import warnings
from itertools import product
from pathlib import Path

import polars as pl
import yaml

from .CustomComorbidityIndex import CustomComorbidityIndex

SCORE_COL_NAME = "Charlson Comorbidity Index"
FINAL_SCORE_COL_NAME = "Charlson Age-Comorbidity Score"


def CharlsonComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    icd_version: str = "icd10",
    icd_version_col: str | None = None,
    year_col: str | None = None,
    implementation: str = "quan",
    weights: str = "charlson",
    return_categories: bool = False,
):
    """Calculate the Charlson Comorbidity Index (CCI) using ICD codes and age.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col``, ``code_col``, and ``age_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        age_col (str, optional): Column name containing patient ages. Defaults to ``"age"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        year_col (str, optional): Column name with each record's ICD-10-GM catalogue year. Required when ``implementation`` is ``"sokolowski"`` (ignored otherwise), since that mapping is year-specific. Defaults to ``None``.
        implementation (str, optional): Definition set to use; ``"quan"``, ``"deyo"``, ``"romano"``, ``"dhoore"``, ``"australia"``, ``"sweden"``, ``"rcs"``, ``"uk_shmi"``, ``"sokolowski"``, or ``"thygesen"``. Defaults to ``"quan"``.
        weights (str, optional): Weighting scheme. For Charlson, weights are determined by the implementation; this parameter is accepted for API consistency. Defaults to ``None``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each CCI category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the ``"Charlson Age-Comorbidity Score"`` column, and, when ``return_categories`` is ``True``, category indicators and the ``"Age Score"`` column.

    Raises:
        AssertionError: If required columns are missing.
        ValueError: If ``implementation`` is unsupported.
    """

    # Change ICD to ICD-9 for Deyo, D'Hoore and Romano
    if icd_version in ("icd10", "icd9_10") and implementation in [
        "deyo",
        "dhoore",
        "romano",
    ]:
        warnings.warn(
            f"Implementation '{implementation}' only uses ICD-9. Setting ICD version to 'icd9'.",
            UserWarning,
            stacklevel=2,
        )
        icd_version = "icd9"
    # Change ICD to ICD-10 for Australian, UK, Sokołowski and Thygesen versions
    elif icd_version in ("icd9", "icd9_10") and implementation in [
        "australia",
        "rcs",
        "uk_shmi",
        "sokolowski",
        "thygesen",
    ]:
        warnings.warn(
            f"Implementation '{implementation}' only uses ICD-10. Setting ICD version to 'icd10'.",
            UserWarning,
            stacklevel=2,
        )
        icd_version = "icd10"

    # Input validation specific to Charlson
    assert implementation in [
        "quan",
        "deyo",
        "romano",
        "dhoore",
        "australia",
        "sweden",
        "rcs",
        "uk_shmi",
        "sokolowski",
        "thygesen",
    ], "implementation must be one of: 'quan', 'deyo', 'romano', 'dhoore', 'australia', 'sweden', 'rcs', 'uk_shmi', 'sokolowski', or 'thygesen'."
    assert weights in [
        "charlson",
        "quan",
        "rcs",
        "uk_shmi",
    ], "weights must be one of: 'charlson', 'quan', 'rcs', or 'uk_shmi'."
    assert age_col in df.columns, f"Column '{age_col}' (age) must be present in input DataFrame." # fmt: skip
    if implementation == "sokolowski":
        assert year_col is not None and year_col in df.columns, "Implementation 'sokolowski' requires a 'year_col' column (ICD-10-GM catalogue year) in the input DataFrame." # fmt: skip

    # STEP 0: diagnoses are handled by CustomComorbidityIndex

    # STEP 1: Calculate Age Score separately (on one age per patient, not per diagnosis row)
    #  < 50: 0
    #  < 60: 1
    #  < 70: 2
    #  < 80: 3
    # >= 80: 4
    age_scores = (
        df.group_by(id_col)
        .agg(pl.col(age_col).max())
        .with_columns(
            pl.when(pl.col(age_col) < 50)
            .then(pl.lit(0))
            .when(pl.col(age_col) < 60)
            .then(pl.lit(1))
            .when(pl.col(age_col) < 70)
            .then(pl.lit(2))
            .when(pl.col(age_col) < 80)
            .then(pl.lit(3))
            .otherwise(pl.lit(4))
            .fill_null(0)  # Assume age 0 if null
            .cast(int)
            .alias("Age Score")
        )
        .select(id_col, "Age Score")
    )

    # STEP 2: Calculate Comorbidity Score using generalized function
    # Determine definition file based on implementation
    if implementation == "quan":
        definition_file = "CHARLSON_QUAN.csv"
    elif implementation == "deyo":
        definition_file = "CHARLSON_DEYO.csv"
    elif implementation == "dhoore":
        definition_file = "CHARLSON_DHOORE.csv"
    elif implementation == "romano":
        definition_file = "CHARLSON_ROMANO.csv"
    elif implementation == "australia":
        definition_file = "CHARLSON_AUSTRALIA.csv"
    elif implementation == "sweden":
        definition_file = "CHARLSON_SWEDEN.csv"
    elif implementation == "rcs":
        definition_file = "CHARLSON_RCS.csv"
    elif implementation == "uk_shmi":
        definition_file = "CHARLSON_UK_SHMI_v1.55.csv"
    elif implementation == "sokolowski":
        definition_file = "CHARLSON_SOKOLOWSKI.csv"
    elif implementation == "thygesen":
        definition_file = "CHARLSON_THYGESEN.csv"
    else:
        # Should be caught by assert earlier
        raise ValueError(f"Unsupported implementation: {implementation}")

    # Determine weight column and score column names based on weights argument
    # rcs/uk_shmi implementations always use their own matching weights
    if implementation in ("rcs", "uk_shmi") and weights != implementation:
        warnings.warn(
            f"Implementation '{implementation}' requires '{implementation}_weights'. Overriding weights='{weights}' with '{implementation}_weights'.",
            UserWarning,
            stacklevel=2,
        )
        weights = implementation
    weight_col_name = f"{weights}_weights"

    # Load definition and weight files
    base_path = Path(__file__).parent / "common"
    definition_file_path = base_path / definition_file
    weights_file_path = base_path / "CHARLSON_WEIGHTS.csv"

    df_definitions = pl.read_csv(definition_file_path)
    df_weights = pl.read_csv(weights_file_path).drop("index")

    # Join definitions and weights
    # Ensure 'category' column exists in both for joining
    if (
        "category" not in df_definitions.columns
        or "category" not in df_weights.columns
    ):
        raise ValueError("Both definition and weight files must contain a 'category' column.") # fmt: skip

    # Alias renamed categories to CHARLSON_WEIGHTS.csv's names for the weight
    # lookup only; see CHARLSON_CATEGORY_ALIASES.yaml for the mapping
    with open(base_path / "CHARLSON_CATEGORY_ALIASES.yaml") as f:
        category_aliases = yaml.safe_load(f).get(implementation, {})

    df_combined = (
        df_definitions.with_columns(
            pl.col("category").replace(category_aliases).alias("__weight_category__")
        )
        .join(df_weights.rename({"category": "__weight_category__"}), on="__weight_category__", how="left")
        .drop("__weight_category__")
    )

    # Mutual exclusion: if both categories of a pair are present, only the first
    # (more severe) is counted. Rules use canonical names, mapped to each
    # implementation's own names via its aliases.
    canonical_rules = [
        ("Diabetes with chronic complication", "Diabetes without chronic complication"),
        ("Moderate or severe liver disease", "Mild liver disease"),
        ("Metastatic solid tumor", "Any malignancy"),
        # Sweden splits Chronic pulmonary disease - no exclusion needed between them,
        # the Swedish SAS code sums "copd" and "other_cpd" (weight 1 each).
    ]
    # own category name -> canonical name
    canonical = {c: category_aliases.get(c, c) for c in df_combined["category"]}
    mutual_exclusion_rules = [
        (severe, mild)
        for severe, mild in product(canonical, repeat=2)
        if (canonical[severe], canonical[mild]) in canonical_rules
    ]

    df_charlson = CustomComorbidityIndex(
        df=df,
        id_col=id_col,
        code_col=code_col,
        icd_version=icd_version,
        icd_version_col=icd_version_col,
        year_col=year_col if implementation == "sokolowski" else None,
        definition_data=df_combined,
        weight_col_name=weight_col_name,
        score_col_name=SCORE_COL_NAME,
        mutual_exclusion_rules=mutual_exclusion_rules,
        return_categories=return_categories,
    )

    # STEP 3: Combine Age Score and Comorbidity Score
    df_charlson = df_charlson.join(
        age_scores, on=id_col, how="left", coalesce=True
    ).with_columns(
        (pl.col(SCORE_COL_NAME) + pl.col("Age Score")).alias(
            FINAL_SCORE_COL_NAME
        )
    )

    # Drop Age Score column if not needed
    if not return_categories:
        df_charlson = df_charlson.drop("Age Score")

    return df_charlson


# region 10y survival
def CharlsonComorbidity_10year_survival(
    df: pl.DataFrame = None,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    icd_version: str = "icd10",
    icd_version_col: str | None = None,
    implementation: str = "quan",
    precalculated_df: bool = False,
) -> pl.DataFrame:
    """Estimate 10-year survival probabilities from the Charlson Comorbidity Index.

    Args:
        df (pl.DataFrame | None, optional): Source data with ICD codes, ages, and identifiers, or a precomputed Charlson score table when ``precalculated_df`` is ``True``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        age_col (str, optional): Column name containing patient ages. Defaults to ``"age"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str | None, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``.
        implementation (str, optional): Charlson definition set passed to :func:`CharlsonComorbidityIndex`. Defaults to ``"quan"``.
        precalculated_df (bool, optional): If ``True``, assumes ``df`` already includes a ``"Charlson Age-Comorbidity Score"`` column. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame with two columns: ``id_col`` and ``"10-year survival probability"``.

    Raises:
        AssertionError: If required columns are missing when ``precalculated_df`` is ``True``.
    """

    if not precalculated_df:
        df, _ = CharlsonComorbidityIndex(
            df=df,
            id_col=id_col,
            code_col=code_col,
            age_col=age_col,
            icd_version=icd_version,
            icd_version_col=icd_version_col,
            implementation=implementation,
            return_categories=False,
        )
    else:
        assert (
            FINAL_SCORE_COL_NAME in df.columns
        ), "Input DataFrame must contain column 'Charlson Score'."
        assert (
            id_col in df.columns
        ), f"Input DataFrame must contain column '{id_col}'."

    # Formula: 0.983 ^ (CCI Score * 0.9)
    return df.with_columns(
        (0.983 ** (pl.col(FINAL_SCORE_COL_NAME) * 0.9))
        .round(3)
        .alias("10-year survival probability")
    ).select(id_col, "10-year survival probability")
