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

from pathlib import Path

import pandas as pd
import polars as pl

# Import the generalized function
from .CustomComorbidityIndex import CustomComorbidityIndex


def CharlsonComorbidityIndex(
    df: pl.DataFrame,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    icd_version: str = "icd10",
    icd_version_col: str = None,
    implementation: str = "quan",
    return_categories: bool = False,
):
    """
    Calculate the Charlson Comorbidity Index (CCI) using ICD codes and age.

    Args:
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col, age_col].
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        age_col (str): Name of the column containing patient ages. Default: "age".
        icd_version (str): ICD version ('icd9', 'icd10', or 'icd9_10'). Default: "icd10".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        implementation (str): CCI implementation ('quan', 'deyo', 'romano', 'australia', 'sweden', 'uk_shmi'). Default: "quan".
        return_categories (bool): If True, also return presence indicators for each CCI category.

    Returns:
        - DataFrame with [id_col, "Charlson Score"].
        - DataFrame with category indicators if return_categories is True, else None.
    """

    # Check if input is pandas DataFrame and convert to polars
    is_pandas = pd and isinstance(df, pd.DataFrame)
    if is_pandas:
        df = pl.from_pandas(df)

    # Change ICD to ICD-9 for Deyo, D'Hoore and Romano
    if icd_version == "icd10" and implementation in [
        "deyo",
        "dhoore",
        "romano",
    ]:
        print(f"Warning: Implementation '{implementation}' only uses ICD-9. Setting ICD version to 'icd9'.") # fmt: skip
        icd_version = "icd9"
    # Change ICD to ICD-10 for Australian, Swedish and UK versions
    elif icd_version == "icd9" and implementation in [
        "australia",
        "sweden",
        "uk_shmi",
    ]:
        print(f"Warning: Implementation '{implementation}' only uses ICD-10. Setting ICD version to 'icd10'.") # fmt: skip
        icd_version = "icd10"

    # Input validation specific to Charlson
    assert implementation in [
        "quan",
        "deyo",
        "romano",
        "australia",
        "sweden",
        "uk_shmi",
    ], (
        "implementation must be one of: "
        "'quan', 'deyo', 'romano', 'australia', 'sweden', or 'uk_shmi'."
    )
    assert (
        age_col in df.columns
    ), f"Column '{age_col}' (age) must be present in input DataFrame."
    assert (
        id_col in df.columns
    ), f"Column '{id_col}' (ID) must be present in input DataFrame."

    # STEP 0: select relevant columns and rename diagnosis code column
    # diagnoses handled by CustomComorbidityIndex
    patient_ages = df.select(id_col, age_col)

    # STEP 1: Calculate Age Score separately
    # <= 50: 0
    # <= 60: 1
    # <= 70: 2
    # <= 80: 3
    #  > 80: 4
    age_scores = (
        patient_ages.with_columns(
            pl.col(age_col)
            .cut(
                breaks=[50, 60, 70, 80],
                labels=["0", "1", "2", "3", "4"],
                left_closed=False,  # Age > 50 gets score 1, etc.
            )
            .fill_null("0")  # Assume age 0 if null
            .cast(int)
            .alias("Age Score")
        )
        .group_by(id_col)
        .agg(pl.col("Age Score").max().alias("Age Score"))
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
    elif implementation == "uk_shmi":
        definition_file = "CHARLSON_UK_SHMI_v1.55.csv"
    else:
        # Should be caught by assert earlier
        raise ValueError(f"Unsupported implementation: {implementation}")

    definition_file_path = Path(__file__).parent / f"common/{definition_file}"
    weight_col_name = "weights"

    # Use a temporary score name before adding age score
    score_col_name = "Charlson Comorbidity Score"

    # Define mutual exclusion rules for Charlson
    # These category names are common across Quan, Romano, Deyo
    mutual_exclusion_rules = [
        (
            "Diabetes with chronic complication",
            "Diabetes without chronic complication",
        ),
        ("Moderate or severe liver disease", "Mild liver disease"),
    ]
    # Adjust rules for specific implementations if category names differ
    if implementation == "australia" or implementation == "uk_shmi":
        mutual_exclusion_rules = [
            ("Diabetes complications", "Diabetes"),
            ("Severe liver disease", "Liver disease"),
        ]
    elif implementation == "sweden":
        mutual_exclusion_rules = [
            ("Diabetes with end organ damage", "Diabetes"),
            # Sweden uses 'Moderate or severe kidney disease' - no specific liver exclusion rule needed based on provided names
            # Sweden splits Pulmonary disease - no exclusion needed between them
        ]

    df_charlson = CustomComorbidityIndex(
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

    # STEP 3: Combine Age Score and Comorbidity Score
    final_score_col_name = "Charlson Score"
    df_charlson = df_charlson.join(
        age_scores, on=id_col, how="left", coalesce=True
    ).with_columns(
        (pl.col(score_col_name) + pl.col("Age Score")).alias(
            final_score_col_name
        )
    )

    # Drop Age Score column if not needed
    if not return_categories:
        df_charlson = df_charlson.drop("Age Score")

    if is_pandas:
        return df_charlson.to_pandas()

    return df_charlson


# region 10y survival
def CharlsonComorbidity_10year_survival(
    df: pl.DataFrame = None,
    id_col: str = "id",
    code_col: str = "code",
    age_col: str = "age",
    icd_version: str = "icd10",
    icd_version_col: str = None,
    implementation: str = "quan",
    precalculated_df: bool = False,
) -> pl.DataFrame:
    """
    Calculate the 10-year survival probability based on the Charlson Comorbidity Index.

    Args:
        df (pl.DataFrame): DataFrame with at least columns [id_col, code_col, age_col] or [id_col, "Charlson Score"] if precalculated_df is True.
        id_col (str): Name of the column containing unique identifier. Default: "id".
        code_col (str): Name of the column containing ICD codes. Default: "code".
        age_col (str): Name of the column containing patient ages. Default: "age".
        icd_version (str): ICD version ('icd9', 'icd10', or 'icd9_10'). Default: "icd10".
        icd_version_col (str, optional): Name of the column with ICD version for 'icd9_10'. Default: None.
        implementation (str): The Charlson implementation. Default: "quan".
        precalculated_df (bool): If True, df is expected to contain a "Charlson Score" column instead of ICD codes and age.

    Returns:
        pl.DataFrame: DataFrame with columns [id_col, "10-year survival probability"].
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
            "Charlson Score" in df.columns
        ), "Input DataFrame must contain column 'Charlson Score'."
        assert (
            id_col in df.columns
        ), f"Input DataFrame must contain column '{id_col}'."

    # Formula: 0.983 ^ (CCI Score * 0.9)
    return df.with_columns(
        (pl.lit(0.983) ** (pl.col("Charlson Score").clip(lower_bound=0) * 0.9))
        .round(3)
        .alias("10-year survival probability")
    ).select(id_col, "10-year survival probability")
