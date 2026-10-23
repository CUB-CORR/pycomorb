# ICD modification

ICD-10-GM and ICD-10-CM change every year: codes are added, split and removed. A mapping written for one year therefore misses codes from other years. With `icd_modification`, every code is first mapped from the year it was recorded in (`year_col`) to one target year, and the score is then calculated on the mapped codes.

```python
from pycomorb import comorbidity

result = comorbidity(
    "charlson", df, id_col="id", code_col="code", age_col="age", year_col="year",
    icd_version="icd10", icd_modification="icd10gm",
    icd_modification_target_year=2024,
)
```

| `icd_modification` | Classification | Supported years | Default target year |
|---|---|---|---|
| `icd10gm` | ICD-10-GM (Germany) | 2004–2026 | 2004 |
| `icd10cm` | ICD-10-CM (US) | 2015–2027 | 2015 |

The mapping needs a `year_col` column with the year of each code, without missing values, and codes that start with a letter (A–Z) after cleaning; otherwise an `AssertionError` is raised. It is applied to ICD-10 codes only: with `icd_version="icd9"` it is skipped silently, and with `icd_version="icd9_10"`, rows labelled `"ICD-9"` keep their codes.

!!! warning
    The default target year is the **earliest** one (2004 / 2015). For `icd10cm`, a code that did not exist in the target year is mapped to the placeholder `UNDEF2015` and then matches no category: with the default, `I21.9` recorded in 2018 is not counted as myocardial infarction, with `icd_modification_target_year=2018` or later it is. Set the target year explicitly, usually to the latest year of your data.

## What the mapping does

The mapping follows the official transfer tables (BfArM for ICD-10-GM, the CMS ICD-10-CM conversion table for ICD-10-CM). Codes not found in the table are returned unchanged (without dots). For ICD-10-GM, a code that was **split** is returned once per successor, so the number of rows can grow; a category still counts once per patient.

```python
import polars as pl
from pycomorb import get_icd10gm

df = pl.DataFrame({"id": [1, 2], "code": ["A04.7", "I21"], "year": [2012, 2012]})
get_icd10gm(df, target_year=2024)
```

```
┌─────┬───────┬──────┬──────────┐
│ id  ┆ code  ┆ year ┆ icd_2024 │
╞═════╪═══════╪══════╪══════════╡
│ 1   ┆ A04.7 ┆ 2012 ┆ A0470    │
│ 1   ┆ A04.7 ┆ 2012 ┆ A0471    │
│ 1   ┆ A04.7 ┆ 2012 ┆ A0472    │
│ 1   ┆ A04.7 ┆ 2012 ┆ A0473    │
│ 1   ┆ A04.7 ┆ 2012 ┆ A0479    │
│ 2   ┆ I21   ┆ 2012 ┆ I21      │
└─────┴───────┴──────┴──────────┘
```

Mapped codes are written to a new column `icd_<target_year>` (without dots). `comorbidity()` uses it as the code column. `get_icd10gm()` and `get_icd10cm()` return the DataFrame with this column:

```python
get_icd10gm(df, code_col="code", year_col="year", target_year=2024)
```

Note that their default target year is 2024, not the earliest year.

Codes with a year outside the table (for example 2030 for ICD-10-CM) are used unchanged and a `UserWarning` lists the years.

A target year outside the supported range raises an `AssertionError`.

!!! note
    The ICD-10-GM transfer tables are published by the BfArM; see [NOTICE](https://github.com/CUB-CORR/pycomorb/blob/main/NOTICE) for the attribution.

## Year-specific implementations

`charlson` with `implementation="sokolowski"` and `elixhauser` with `implementation="ahrq_icd10"` have mappings that themselves depend on the year of the code, so they need `year_col` even without `icd_modification`.
