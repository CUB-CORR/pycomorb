# Reporting

`comorbidity_reporting` documents the exact definition behind a score: a methods table for a manuscript plus the weights, code list and hierarchy rules. It returns `(template, weights, codes, hierarchy)` as polars DataFrames and, with `path`, writes them to a folder as `template.md`, `weights.csv`, `codes.csv` and `hierarchy.csv`.

```python
from pycomorb import comorbidity, comorbidity_reporting, read_reporting

comorbidity_reporting(
    "charlson", implementation="quan", icd_version="icd10",
    path="charlson_report",
    data_sources="Example EHR", look_back_period="1 year",  # optional study information
)

custom = comorbidity("custom", df, id_col="id", code_col="code", **read_reporting("charlson_report"))
```

`read_reporting` returns the arguments of a [`"custom"` score](custom.md) that reproduces the reported one (`icd_version`, `definition_data`, `weight_col_name`, `mutual_exclusion_rules`). Do not pass `icd_version` again; `icd_version_col` is still needed for `"icd9_10"`.

## Example output

The call above writes four files. `template.md` is the methods table to paste into a manuscript:

<div class="wide-2" markdown="1">

| domain | information |
|---|---|
| Data source(s) | Example EHR |
| Method of data extraction | |
| Comorbidity weighting reference | Charlson et al. (1987) |
| Comorbidity weighting list | weights.csv |
| Disease classification system | ICD-10 |
| Disease code reference | Quan et al. (2005) |
| Disease code list | codes.csv |
| Coding practice | |
| Age adjustment | Age points: 0 (<50 years), 1 (50-59), 2 (60-69), 3 (70-79), 4 (>=80) |
| Hierarchy rules | 'Diabetes with chronic complication' replaces 'Diabetes without chronic complication'; 'Moderate or severe liver disease' replaces 'Mild liver disease'; 'Metastatic solid tumor' replaces 'Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin' |
| Look-back period | 1 year |
| Timing of data extraction | |
| Software | pycomorb 1.20261001.1 |

</div>

The other files hold the definition itself. `weights.csv` and `codes.csv` have one row per category and per code (first rows shown); `row` links a weight to its codes.

`weights.csv`

```csv
row,category,weight
0,Myocardial infarction,1
1,Congestive heart failure,1
2,Peripheral vascular disease,1
```

`codes.csv`

```csv
row,category,icd_version,code
0,Myocardial infarction,ICD-10,I21
0,Myocardial infarction,ICD-10,I22
0,Myocardial infarction,ICD-10,I252
```

`hierarchy.csv`

```csv
severe,mild
Diabetes with chronic complication,Diabetes without chronic complication
Moderate or severe liver disease,Mild liver disease
Metastatic solid tumor,"Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin"
```

The Software line shows the installed pycomorb version.

Study information you don't pass stays empty in `template.md`, to be filled in by hand. The supported keys are `data_sources`, `method_of_data_extraction`, `coding_practice`, `look_back_period` and `timing_of_data_extraction`.
