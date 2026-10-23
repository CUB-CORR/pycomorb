# Custom index

`score="custom"` scores your own category definitions. Pass them as a polars (or pandas) DataFrame in `definition_data`, or as a CSV in `definition_file_path`.

| column | content |
|---|---|
| `category` | category name |
| `icd9_codes`, `icd10_codes` | code prefixes separated by `\|`; only the column of the chosen `icd_version` is needed |
| weight column | name it with `weight_col_name` (default `"weights"`) |
| `and_group` (optional) | rows of one `category` with the same non-empty `and_group` count only if **all** are present |
| `year` (optional) | a row applies from this year on. Needs a year column in the data: `year_col` (default `"year"`) is used automatically if that column exists |

A category is present if any of its rows matches (OR). Codes are matched by [prefix](input-output.md#how-codes-are-matched).

```python
import polars as pl
from pycomorb import comorbidity

definitions = pl.DataFrame({
    "category": ["Heart", "Cancer", "Advanced cancer"],
    "icd10_codes": ["I21|I22", "C", "C77|C78"],
    "weights": [2, 1, 3],
})

comorbidity(
    "custom", df, id_col="id", code_col="code",
    definition_data=definitions, weight_col_name="weights",
    mutual_exclusion_rules=[("Advanced cancer", "Cancer")],
    score_col_name="My score", return_categories=True,
)
```

`mutual_exclusion_rules` is a list of `(keep, suppress)` pairs: if `keep` is present, `suppress` is set to 0 and is not counted. Both categories must exist in the definitions (`ValueError` otherwise).

To publish or reuse a definition, see [Reporting](reporting.md).
