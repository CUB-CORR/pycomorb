# Reference for ICD-10-CM modifications:
# CMS: https://www.cms.gov/medicare/coding-billing/icd-10-codes

# Reference for ICD-10-GM modifications:
# BfArM: https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html

import warnings
from pathlib import Path

import polars as pl


def check_code_dtype(df: pl.DataFrame, code_col: str) -> pl.DataFrame:
    """Cast categorical codes to strings and reject numbers (250.1 and '250.10' are different codes)."""
    dtype = df.schema[code_col]
    if dtype in (pl.Categorical, pl.Enum):
        return df.with_columns(pl.col(code_col).cast(pl.String))
    if dtype not in (pl.String, pl.Null):
        raise ValueError(
            f"Column '{code_col}' must contain ICD codes as strings, got {dtype}. Convert it explicitly "
            "(numbers cannot be converted safely: 250.1 and '250.10' are different ICD-9 codes)."
        )
    return df


def clean_code_expr(code_col: str) -> pl.Expr:
    return (
        pl.col(code_col)
        .str.replace_all(".", "", literal=True)
        .str.strip_chars()
        .str.to_uppercase()
    )


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

    assert code_col in data.columns, f"Column '{code_col}' (ICD code) must be present in input DataFrame." # fmt: skip
    assert year_col in data.columns, f"Column '{year_col}' (year) must be present in input DataFrame." # fmt: skip

    table = pl.read_csv(transfer_file_path, null_values=["", " "], separator=",")
    table_years = [int(c) for c in table.columns]
    assert target_year in table_years, f"Target year must be between {min(table_years)} and {max(table_years)}." # fmt: skip

    data = check_code_dtype(data, code_col)
    assert data[year_col].null_count() == 0, f"Column '{year_col}' (year) must not contain missing values when an ICD modification is applied." # fmt: skip

    # Validate and clean the unique (code, year) pairs only; the crosswalk is joined on the cleaned code
    pairs = data.select(code_col, year_col).unique().with_columns(clean_code_expr(code_col).alias("clean"))
    assert pairs["clean"].filter(pairs["clean"] != "").str.contains(r"^[A-Z]").all(), f"All values in column '{code_col}' must start with an uppercase letter (A-Z)." # fmt: skip

    # Unpivot the data to long format
    transfer_data = (
        table.with_columns(pl.col(pl.String).str.strip_chars())
        .unpivot(
            index=str(target_year),
            variable_name=year_col,
            value_name=code_col,
        )
        .cast({year_col: int})
        .rename({str(target_year): f"icd_{target_year}"})
    )

    outside = sorted(set(pairs[year_col].to_list()) - set(table_years))
    if outside:
        warnings.warn(
            f"Codes with year(s) {outside} in column '{year_col}' lie outside the transfer table "
            f"({min(table_years)}-{max(table_years)}) and are used unchanged.",
            UserWarning,
            stacklevel=3,
        )

    mapped = (
        pairs.join(
            transfer_data.rename({code_col: "clean"}),
            on=["clean", year_col],
            how="left",
        )
        # Prefer mapped code, but fall back to the cleaned original if no mapping available
        .select(
            code_col,
            year_col,
            pl.coalesce(pl.col(f"icd_{target_year}"), pl.col("clean")).alias(
                f"icd_{target_year}"
            ),
        )
    )

    return data.join(mapped, on=[code_col, year_col], how="left")


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

    # Load all transfer files into a dictionary of DataFrames
    transfer_file_path = Path(__file__).parent / "common/modification_DE/icd10gm.csv" # fmt: skip

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

    # Load all transfer files into a dictionary of DataFrames
    transfer_file_path = Path(__file__).parent / "common/modification_US/icd10cm.csv" # fmt: skip

    return get_icdmodification(
        data=data,
        transfer_file_path=transfer_file_path,
        code_col=code_col,
        year_col=year_col,
        target_year=target_year,
    )
