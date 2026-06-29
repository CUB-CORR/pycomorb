# Reference for CCS:
# 1. Gagne JJ, Glynn RJ, Avorn J, Levin R, Schneeweiss S.
#    A combined comorbidity score predicted mortality in elderly patients better than existing scores.
#    J Clin Epidemiol. 2011 Jul;64(7):749-59.
#    doi: 10.1016/j.jclinepi.2010.10.004. Epub 2011 Jan 5. PMID: 21208778; PMCID: PMC3100405.
#
# Reference for source ICD-9-CM Coding Algorithms:
# 2. Romano PS, Roos LL, Jollis JG.
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative databases.
#    J Clin Epidemiol. 1993 Oct;46(10):1075-9; discussion 1081-90.
#    doi: 10.1016/0895-4356(93)90103-8. PMID: 8410092.
# 3. Quan H, Sundararajan V, Halfon P, Fong A, Burnand B, Luthi JC, Saunders LD, Beck CA, Feasby TE, Ghali WA.
#    Coding algorithms for defining comorbidities in ICD-9-CM and ICD-10 administrative data.
#    Med Care. 2005 Nov;43(11):1130-9.
#    doi: 10.1097/01.mlr.0000182534.19832.83. PMID: 16224307.
#
# Reference for ICD-9 / ICD-10 mapping:
# 4. Sun JW, Rogers JR, Her Q, Welch EC, Panozzo CA, Toh S, Gagne JJ.
#    Adaptation and Validation of the Combined Comorbidity Score for ICD-10-CM.
#    Med Care. 2017 Dec;55(12):1046-1051.
#    doi: 10.1097/MLR.0000000000000824. PMID: 29087983.

from pathlib import Path

import polars as pl

from .CustomComorbidityIndex import CustomComorbidityIndex

SCORE_COL_NAME = "Combined Comorbidity Score"


def CombinedComorbidityScore(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd9",
    icd_version_col: str = None,
    return_categories=False,
):
    """Calculate the Combined Comorbidity Score using ICD codes.

    Args:
        df (pl.DataFrame): Input data containing at least ``id_col`` and ``code_col``.
        id_col (str, optional): Column name containing unique identifiers. Defaults to ``"id"``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        icd_version (str, optional): ICD version; one of ``"icd9"``, ``"icd10"``, or ``"icd9_10"``. Defaults to ``"icd9"``.
        icd_version_col (str, optional): Column name with ICD version labels when ``icd_version`` is ``"icd9_10"``. Defaults to ``None``.
        return_categories (bool, optional): If ``True``, includes indicator columns for each Combined Comorbidity Score category. Defaults to ``False``.

    Returns:
        pl.DataFrame: DataFrame containing ``id_col``, the calculated score column, and, when ``return_categories`` is ``True``, category indicators.

    Raises:
        AssertionError: If required columns are missing.
    """

    definition_file = "GAGNE.csv"
    definition_file_path = Path(__file__).parent / "common" / definition_file
    weight_col_name = "weights"

    # Define mutual exclusion rules for combined score
    mutual_exclusion_rules = [
        ("Complicated diabetes", "Uncomplicated diabetes")
    ]

    # Call the generalized function
    df_ccs = CustomComorbidityIndex(
        df=df,
        id_col=id_col,
        code_col=code_col,
        icd_version=icd_version,
        icd_version_col=icd_version_col,
        definition_data=definition_file_path,
        weight_col_name=weight_col_name,
        score_col_name=SCORE_COL_NAME,
        mutual_exclusion_rules=mutual_exclusion_rules,
        return_categories=return_categories,
    )

    return df_ccs
