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
# Reference for ICD Coding Algorithms for Charlson Comorbidities (implementation=...):
# 3. Deyo RA, Cherkin DC, Ciol MA. (ICD-9-CM; 'deyo')
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative databases.
#    J Clin Epidemiol. 1992 Jun;45(6):613-9.
#    doi: 10.1016/0895-4356(92)90133-8. PMID: 1607900.
# 4. Romano PS, Roos LL, Jollis JG. (ICD-9-CM; 'romano')
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative data: differing perspectives.
#    J Clin Epidemiol. 1993 Oct;46(10):1075-9; discussion 1081-90.
#    doi: 10.1016/0895-4356(93)90103-8. PMID: 8410092.
# 5. D'Hoore W, Bouckaert A, Tilquin C. (ICD-9-CM; 'dhoore')
#    Practical considerations on the use of the Charlson comorbidity index with administrative data bases.
#    J Clin Epidemiol. 1996 Dec;49(12):1429-33.
#    doi: 10.1016/s0895-4356(96)00271-5. PMID: 8991959.
# 6. Sundararajan V, Henderson T, Perry C, Muggivan A, Quan H, Ghali WA. (ICD-10-AM; 'australia')
#    New ICD-10 version of the Charlson comorbidity index predicted in-hospital mortality.
#    J Clin Epidemiol. 2004 Dec;57(12):1288-94.
#    doi: 10.1016/j.jclinepi.2004.03.012. PMID: 15617955.
# 7. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA. (ICD-9-CM and ICD-10; 'quan')
#    Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data.
#    Med Care. 2005 Nov;43(11):1130-9.
#    doi: 10.1097/01.mlr.0000182534.19832.83. PMID: 16224307.
# 8. Armitage JN, van der Meulen JH; Royal College of Surgeons Co-morbidity Consensus Group. (ICD-10; 'rcs')
#    Identifying co-morbidity in surgical patients using administrative data with the Royal College of Surgeons Charlson Score.
#    Br J Surg. 2010 May;97(5):772-81.
#    doi: 10.1002/bjs.6930. PMID: 20306528.
# 9. Thygesen SK, Christiansen CF, Christensen S, Lash TL, Sørensen HT. (ICD-10; 'thygesen')
#    The predictive value of ICD-10 diagnostic coding used to assess Charlson comorbidity index conditions in the population-based Danish National Registry of Patients.
#    BMC Med Res Methodol. 2011 May 28;11:83.
#    doi: 10.1186/1471-2288-11-83. PMID: 21619668; PMCID: PMC3125388.
# 10. Ludvigsson JF, Appelros P, Askling J, Byberg L, Carrero JJ, Ekström AM, Ekström M, Smedby KE, Hagström H, James S, Järvholm B, Michaelsson K, Pedersen NL, Sundelin H, Sundquist K, Sundström J. (ICD-9 [Swedish] and ICD-10; 'sweden')
#     Adaptation of the Charlson Comorbidity Index for Register-Based Research in Sweden.
#     Clin Epidemiol. 2021 Jan 12;13:21-41.
#     doi: 10.2147/CLEP.S282475. PMID: 33469380; PMCID: PMC7812935.
# 11. NHS Digital. Summary Hospital-level Mortality Indicator (SHMI) specification v1.60, June 2026. (ICD-10; 'uk_shmi')
#     https://digital.nhs.uk/data-and-information/publications/statistical/shmi
# 12. Sokołowski PP, Hagmann M, Maros ME, Kamdje Wabo G, Meerjanssen JM, Siegel F. (ICD-10-GM; 'sokolowski')
#     Developing Country-Specific Charlson Comorbidity Index Mappings for Use With German Administrative Data: Methodological Comparative Study.
#     JMIR Med Inform. 2026 Sep 3;14:e93923.
#     doi: 10.2196/93923. PMID: 42593349; PMCID: PMC13586706.
#
# Reference for Charlson weights (weights=...):
# 13. Schneeweiss S, Wang PS, Avorn J, Glynn RJ. ('schneeweiss')
#     Improved comorbidity adjustment for predicting mortality in Medicare populations.
#     Health Serv Res. 2003 Aug;38(4):1103-20.
#     doi: 10.1111/1475-6773.00165. PMID: 12968819; PMCID: PMC1360935.
# 14. Quan H, Li B, Couris CM, Fushimi K, Graham P, Hider P, Januel JM, Sundararajan V. ('quan')
#     Updating and validating the Charlson comorbidity index and score for risk adjustment in hospital discharge abstracts using data from 6 countries.
#     Am J Epidemiol. 2011 Mar 15;173(6):676-82.
#     doi: 10.1093/aje/kwq433. Epub 2011 Feb 17. PMID: 21330339.
# ('charlson' = ref. 1, 'rcs' = ref. 8, 'uk_shmi' = ref. 11)

import warnings

import polars as pl

from .CustomComorbidityIndex import (
    CustomComorbidityIndex,
    coerce_icd_version,
    weighted_definitions,
)

DEFINITION_FILES = {
    "quan": "CHARLSON_QUAN.csv",
    "deyo": "CHARLSON_DEYO.csv",
    "dhoore": "CHARLSON_DHOORE.csv",
    "romano": "CHARLSON_ROMANO.csv",
    "australia": "CHARLSON_AUSTRALIA.csv",
    "sweden": "CHARLSON_SWEDEN.csv",
    "rcs": "CHARLSON_RCS.csv",
    "uk_shmi": "CHARLSON_UK_SHMI_v1.60.csv",
    "sokolowski": "CHARLSON_SOKOLOWSKI.csv",
    "thygesen": "CHARLSON_THYGESEN.csv",
}
ICD9_ONLY = {"deyo", "dhoore", "romano"}
ICD10_ONLY = {"australia", "rcs", "uk_shmi", "sokolowski", "thygesen"}
# (more severe, milder): only the more severe category is counted when both are present.
# Sweden splits Chronic pulmonary disease, but the Swedish SAS code sums both parts (weight 1 each).
CANONICAL_RULES = [
    ("Diabetes with chronic complication", "Diabetes without chronic complication"),
    ("Moderate or severe liver disease", "Mild liver disease"),
    ("Metastatic solid tumor", "Any malignancy"),
]
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
) -> pl.DataFrame:
    """Calculate the Charlson Comorbidity Index (CCI) using ICD codes and age.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col``, ``code_col``, and ``age_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        age_col (str, optional): Column name containing patient ages (age points are only added for ``weights="charlson"``). Defaults to ``"age"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd10"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        year_col (str, optional): Column name with each record's ICD-10-GM catalogue year. Required when ``implementation`` is ``"sokolowski"`` (ignored otherwise), since that mapping is year-specific. Defaults to ``None``.
        implementation (str, optional): Definition set to use; ``"quan"``, ``"deyo"``, ``"romano"``, ``"dhoore"``, ``"australia"``, ``"sweden"``, ``"rcs"``, ``"uk_shmi"``, ``"sokolowski"``, or ``"thygesen"``. Defaults to ``"quan"``.
        weights (str, optional): Weighting scheme; one of ``"charlson"``, ``"schneeweiss"``, ``"rcs"``, ``"quan"``, or ``"uk_shmi"``. The ``"rcs"`` and ``"uk_shmi"`` implementations always use their own weights. Defaults to ``"charlson"``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each CCI category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the ``"Charlson Age-Comorbidity Score"`` column, and, when ``return_categories`` is ``True``, category indicators and the ``"Age Score"`` column.

    Raises:
        AssertionError: If ``implementation`` or ``weights`` is unsupported, or if required columns are missing.
    """

    icd_version = coerce_icd_version(icd_version, implementation, ICD9_ONLY, ICD10_ONLY)

    # Input validation specific to Charlson
    assert implementation in DEFINITION_FILES, f"implementation must be one of: {list(DEFINITION_FILES)}."
    assert weights in [
        "charlson",
        "schneeweiss",
        "rcs",
        "quan",
        "uk_shmi",
    ], "weights must be one of: 'charlson', 'schneeweiss', 'rcs', 'quan', or 'uk_shmi'."
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
        # an unknown age (null or NaN) gives no age points
        .agg(pl.col(age_col).cast(pl.Float64).fill_nan(None).max().fill_null(0))
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
            .cast(int)
            .alias("Age Score")
        )
        .select(id_col, "Age Score")
    )

    # STEP 2: Calculate Comorbidity Score using generalized function
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

    df_combined, mutual_exclusion_rules = weighted_definitions(
        "CHARLSON", DEFINITION_FILES[implementation], implementation, CANONICAL_RULES
    )

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

    # UK SHMI: a negative Charlson Comorbidity Index is assigned a value of zero
    if weights == "uk_shmi":
        df_charlson = df_charlson.with_columns(pl.col(SCORE_COL_NAME).clip(lower_bound=0))

    # STEP 3: Combine Age Score and Comorbidity Score
    # Only the Charlson weights include age points
    if weights != "charlson":
        age_scores = age_scores.with_columns(pl.lit(0).alias("Age Score"))

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
        pl.DataFrame: DataFrame with two columns: ``id_col`` and ``"10-year survival probability"``, calculated as ``0.983 ** exp(0.9 * CCI)`` from the age-adjusted Charlson score (Charlson et al. 1994).

    Raises:
        AssertionError: If required columns are missing when ``precalculated_df`` is ``True``.
    """

    if not precalculated_df:
        df = CharlsonComorbidityIndex(
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
        ), f"Input DataFrame must contain column '{FINAL_SCORE_COL_NAME}'."
        assert (
            id_col in df.columns
        ), f"Input DataFrame must contain column '{id_col}'."

    # Charlson et al. 1994: 10-year survival = 0.983 ^ exp(0.9 * CCI)
    return df.with_columns(
        (pl.lit(0.983) ** (0.9 * pl.col(FINAL_SCORE_COL_NAME)).exp())
        .round(3)
        .alias("10-year survival probability")
    ).select(id_col, "10-year survival probability")
