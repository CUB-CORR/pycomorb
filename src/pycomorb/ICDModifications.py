# Reference for ICD-10-CM modifications:
# CMS: https://www.cms.gov/medicare/coding-billing/icd-10-codes

# Reference for ICD-10-GM modifications:
# BfArM: https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html

from pathlib import Path

import polars as pl


def get_icdmodification(
    data: pl.DataFrame,
    transfer_file_path: str,
    code_col="code",
    year_col="year",
    target_year=2024,
) -> pl.DataFrame:
    """Map ICD codes to a target year using official transfer files.

    Args:
        data (pl.DataFrame): Input data containing at least ``code_col`` and ``year_col``.
        transfer_file_path (str | Path): Path to a CSV file with ICD transfer mappings.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        year_col (str, optional): Column name containing the year of each ICD code. Defaults to ``"year"``.
        target_year (int, optional): Target year for the mapped ICD codes. Defaults to ``2024``.

    Returns:
        pl.DataFrame: Input DataFrame with an additional ``f"icd_{target_year}"`` column containing mapped codes.

    Raises:
        AssertionError: If required columns are missing or ICD codes do not match the expected format.
    """

    assert (
        code_col in data.columns
    ), f"Column '{code_col}' (ICD code) must be present in input DataFrame."
    assert (
        data.height
        == data.filter(pl.col(code_col).str.contains(r"^[A-Z]")).height
    ), f"All values in column '{code_col}' must start with an uppercase letter (A-Z)."
    assert (
        year_col in data.columns
    ), f"Column '{year_col}' (year) must be present in input DataFrame."

    # Unpivot the data to long format
    transfer_data = (
        pl.read_csv(transfer_file_path, null_values=["", " "], separator=",")
        .unpivot(
            index=str(target_year),
            variable_name=year_col,
            value_name=code_col,
        )
        .cast({year_col: int})
        .rename({str(target_year): f"icd_{target_year}"})
    )

    return (
        data.join(transfer_data, on=[code_col, year_col], how="left")
        # Prefer mapped code, but fall back to original if no mapping available
        .with_columns(
            pl.coalesce(pl.col(f"icd_{target_year}"), pl.col(code_col)).alias(
                f"icd_{target_year}"
            )
        )
    )


def get_icd10gm(
    data: pl.DataFrame, code_col="code", year_col="year", target_year=2024
) -> pl.DataFrame:
    """Map ICD-10-GM codes to a target year using official transfer files.

    Args:
        data (pl.DataFrame): Input data containing at least ``code_col`` and ``year_col``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        year_col (str, optional): Column name containing the year of each ICD code. Defaults to ``"year"``.
        target_year (int, optional): Target ICD-10-GM year. Defaults to ``2024``.

    Returns:
        pl.DataFrame: Input DataFrame with an additional ``f"icd_{target_year}"`` column containing mapped ICD-10-GM codes.

    Raises:
        AssertionError: If ``target_year`` is outside the supported range or required columns are missing.
    """

    assert target_year in range(
        2004, 2026
    ), "Target year must be between 2004 and 2025."

    # Load all transfer files into a dictionary of DataFrames
    transfer_file_path = Path(__file__).parent / "modification_DE/icd10gm.csv" # fmt: skip

    return get_icdmodification(
        data=data,
        transfer_file_path=transfer_file_path,
        code_col=code_col,
        year_col=year_col,
        target_year=target_year,
    )


def get_icd10cm(
    data: pl.DataFrame, code_col="code", year_col="year", target_year=2024
) -> pl.DataFrame:
    """Map ICD-10-CM codes to a target year using official transfer files.

    Args:
        data (pl.DataFrame): Input data containing at least ``code_col`` and ``year_col``.
        code_col (str, optional): Column name containing ICD codes. Defaults to ``"code"``.
        year_col (str, optional): Column name containing the year of each ICD code. Defaults to ``"year"``.
        target_year (int, optional): Target ICD-10-CM year. Defaults to ``2024``.

    Returns:
        pl.DataFrame: Input DataFrame with an additional ``f"icd_{target_year}"`` column containing mapped ICD-10-CM codes.

    Raises:
        AssertionError: If ``target_year`` is outside the supported range or required columns are missing.
    """

    assert target_year in range(
        2015, 2026
    ), "Target year must be between 2004 and 2025."

    # Load all transfer files into a dictionary of DataFrames
    transfer_file_path = Path(__file__).parent / "modification_US/icd10cm.csv" # fmt: skip

    return get_icdmodification(
        data=data,
        transfer_file_path=transfer_file_path,
        code_col=code_col,
        year_col=year_col,
        target_year=target_year,
    )
