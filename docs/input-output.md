# Input and output

## Input

One row per diagnosis, in long format:

| id | code | age | year |
|---|---|---|---|
| 1 | I21 | 66 | 2012 |
| 1 | E11.9 | 66 | 2012 |
| 2 | C349 | 81 | 2010 |

- `id_col` and `code_col` are required; `age_col` (Charlson) and `year_col` (year-specific implementations, [ICD modification](icd-modification.md)) only where the score needs them. Age and year repeat on every row of a patient.
- polars and pandas DataFrames are accepted. The result has the type of the input.
- **Codes must be strings.** Numeric columns are rejected with a `ValueError`, because `250.1` and `"250.10"` are different ICD-9 codes. Categorical columns are converted.

### How codes are matched

Codes are cleaned (dots removed, whitespace stripped, upper-cased) and then matched by **prefix**: the definition `I21` matches `I21`, `I219` and `I21.9`. A code belongs to every category that lists any of its prefixes. `E11.9` and `E119` are the same code. Missing and blank codes match nothing; their patients stay in the result with all categories 0.

## Output

One row per patient:

| Score | Columns without `return_categories` | Added by `return_categories=True` |
|---|---|---|
| `charlson` | `id`, `Charlson Comorbidity Index`, `Charlson Age-Comorbidity Score` | one 0/1 column per category (before the index), `Age Score` |
| `elixhauser` | `id`, `Elixhauser Comorbidity Index` | one 0/1 column per category |
| `combined` | `id`, `Combined Comorbidity Score` | one 0/1 column per category |
| `hfrs` | `id`, `HFRS Score` | one 0/1 column per category |
| `custom` | `id`, `score_col_name` | one 0/1 column per category |

- The Charlson index is the sum of the category weights; the *Age-Comorbidity Score* adds the age points.
- Patients without a matching code are kept, with all categories 0.
- **The row order of the result is not the order of the input.** Sort or join on `id` if you need an order.

## Warnings and errors

| Type | Message | Cause |
|---|---|---|
| `ValueError` | Unknown score | `score` is not one of `charlson`, `elixhauser`, `combined` (`gagne`), `hfrs`, `custom` |
| `ValueError` | Column 'age' (age) must be present in input DataFrame for Charlson calculation | Charlson without `age_col` |
| `ValueError` | Column 'code' must contain ICD codes as strings | Numeric code column |
| `AssertionError` | implementation must be one of: … | Unknown `implementation` (or `weights`) |
| `AssertionError` | Implementation 'sokolowski' requires a 'year_col' column | Year-specific implementation (`sokolowski`, `ahrq_icd10`) without the year column |
| `AssertionError` | icd_version must be 'icd10' for HFRS | `hfrs` with another ICD version |
| `AssertionError` | Target year must be between 2015 and 2027 | `icd_modification_target_year` outside the table. The message shows the range of the chosen modification: 2004–2026 for `icd10gm`, 2015–2027 for `icd10cm` |
| `AssertionError` | All values in column 'code' must start with an uppercase letter (A-Z) | ICD modification on codes that are not ICD-10 (e.g. ICD-9 codes with `icd_version="icd10"`) |
| `ValueError` | Unknown icd_modification: … | `icd_modification` is not `icd10gm` or `icd10cm` |
| `ValueError` | weights='ahrq' requires icd_version 'icd9' or 'icd10' | `weights="ahrq"` with `icd_version="icd9_10"` |
| `AssertionError` | For icd9_10, … (ICD version) column must be present | `icd_version="icd9_10"` without `icd_version_col` |
| `UserWarning` | Implementation 'deyo' only uses ICD-9. Setting ICD version to 'icd9' | The implementation covers one ICD version only; your `icd_version` was replaced |
| `UserWarning` | Implementation 'rcs' requires 'rcs_weights'. Overriding weights=… | `weights` other than the implementation's own for `rcs`, `uk_shmi`, `ahrq_icd9`, `ahrq_icd10` |
| `UserWarning` | Codes with year(s) [2030] in column 'year' lie outside the transfer table (2015-2027) and are used unchanged | [ICD modification](icd-modification.md) for years the table does not cover |

## Validation

The scoring is tested against an independent re-implementation in plain Python that reads the same mapping and weight files, for every implementation and weighting scheme and for every category. The test suite requires 100 % coverage and runs on Python 3.10–3.13, including the lowest supported polars version. See [Development](development.md) to run it.
