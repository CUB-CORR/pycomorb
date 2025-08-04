# Reference for GCI:
# 1. Gagne JJ, Glynn RJ, Avorn J, Levin R, Schneeweiss S.
#    A combined comorbidity score predicted mortality in elderly patients better than existing scores.
#    J Clin Epidemiol. 2011 Jul;64(7):749-59.
#    doi: 10.1016/j.jclinepi.2010.10.004. Epub 2011 Jan 5. PMID: 21208778; PMCID: PMC3100405.
#
# Reference for source ICD-9-CM Coding Algorithms:
# 2. Romano PS, Roos LL, Jollis JG.
#    Adapting a clinical comorbidity index for use with ICD-9-CM administrative data: differing perspectives.
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

import pandas as pd
import polars as pl

# Import the generalized function
from .CustomComorbidityIndex import CustomComorbidityIndex


def GagneComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    icd_version: str = "icd9",
    icd_version_col: str = None,
    return_categories=False,
):
    """
    Calculate the Gagne Comorbidity Index using ICD codes.

    Args:
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col].
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        icd_version (str): ICD version ('icd9', 'icd10', or 'icd9_10'). Default: "icd9".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        return_categories (bool): If True, also return presence indicators for each Gagne category.

    Returns:
        - DataFrame with [id_col, "Gagne Score"].
        - DataFrame with category indicators if return_categories is True, else None.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    assert (
        id_col in df.columns
    ), f"Column '{id_col}' (ID) must be present in input DataFrame."
    assert (
        code_col in df.columns
    ), f"Column '{code_col}' (ICD code) must be present in input DataFrame."

    definition_file = "GAGNE.csv"
    definition_file_path = Path(__file__).parent / f"common/{definition_file}"
    weight_col_name = "weights"
    score_col_name = "Gagne Score"

    # Define mutual exclusion rules for Gagne
    mutual_exclusion_rules = [
        ("Complicated diabetes", "Uncomplicated diabetes")
    ]

    # Call the generalized function
    df_gagne = CustomComorbidityIndex(
        df=df,
        id_col=id_col,
        code_col=code_col,
        icd_version=icd_version,
        icd_version_col=icd_version_col,
        definition_data=definition_file_path,
        weight_col_name=weight_col_name,
        score_col_name=score_col_name,
        mutual_exclusion_rules=mutual_exclusion_rules,
        return_categories=return_categories,
    )

    if is_pandas:
        return df_gagne.to_pandas()

    return df_gagne
