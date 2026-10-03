# pycomorb

Python package to calculate comorbidity and frailty scores using ICD codes and polars DataFrames.

## Overview

`pycomorb` provides fast, flexible, and reproducible calculation of clinical risk scores from ICD-coded data. It supports multiple comorbidity and frailty indices, including several international variants.

It is inspired by the R package [`comorbidity`](https://github.com/ellessenne/comorbidity) by Alessandro Gasparini and the corresponding Python rewrite [`comorbidipy`](https://github.com/vvcb/comorbidipy) by Vishnu V Chandrabalan.

As a special feature, it also implements the history of the German Modification of the ICD-10 (ICD-10-GM) coding system, allowing users to apply the correct mappings and weights based on the year of diagnosis.

## Included Indices / Scores

- **Charlson Comorbidity Index** (multiple mappings and weights)
- **Elixhauser Comorbidity Index** (multiple mappings and weights)
- **Combined Comorbidity Score** (Gagne et al.)
- **Hospital Frailty Risk Score (HFRS)**

## Supported Variants

See [common/README.md](https://github.com/CUB-CORR/pycomorb/blob/main/src/pycomorb/common/README.md) for more details and references.

### Charlson Comorbidity Index

Categories are: `Myocardial infarction`, `Congestive heart failure`, `Peripheral vascular disease`, `Cerebrovascular disease`, `Dementia`, `Chronic pulmonary disease`, `Rheumatic disease`, `Peptic ulcer disease`, `Mild liver disease`, `Diabetes without chronic complication`, `Diabetes with chronic complication`, `Hemiplegia or paraplegia`, `Renal disease`, `Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin`, `Moderate or severe liver disease`, `Metastatic solid tumor`, `AIDS/HIV`. The Danish/Thygesen variant instead keeps `Any tumor`, `Leukemia`, and `Lymphoma` as three separate categories, as in the original 1987 Charlson paper.

- **Mappings**:
  - Deyo et al. 1992 ([Deyo 1992](https://doi.org/10.1016/0895-4356(92)90133-8)) – ICD-9-CM (`implementation="deyo"`)
  - Romano et al. 1993 ([Romano 1993](https://doi.org/10.1016/0895-4356(93)90103-8)) – ICD-9-CM (`implementation="romano"`)
  - D'Hoore et al. 1996 ([D'Hoore 1996](https://doi.org/10.1016/s0895-4356(96)00271-5)) – ICD-9-CM (`implementation="dhoore"`)
  - Australia, Sundararajan et al. 2004 ([Sundararajan 2004](https://doi.org/10.1016/j.jclinepi.2004.03.012)) – ICD-10-AM (`implementation="australia"`)
  - Quan et al. 2005 ([Quan 2005](https://doi.org/10.1097/01.mlr.0000182534.19832.83)) – ICD-9-CM and ICD-10 (`implementation="quan"`)
  - RCS, Armitage and van der Meulen 2010 ([Armitage & van der Meulen 2010](https://doi.org/10.1002/bjs.6930)) – ICD-10 (always used with RCS weights) (`implementation="rcs"`)
  - Denmark, Thygesen et al. 2011 ([Thygesen 2011](https://doi.org/10.1186/1471-2288-11-83)) – ICD-10 (`implementation="thygesen"`)
  - Sweden, Ludvigsson et al. 2021 ([Ludvigsson 2021](https://doi.org/10.2147/CLEP.S282475)) – ICD-9 and ICD-10 (`implementation="sweden"`)
  - UK SHMI, NHS Digital v1.60 (June 2026) – ICD-10 (always used with SHMI weights) (`implementation="uk_shmi"`)
  - Germany, Sokołowski et al. 2026 ([Sokołowski 2026](https://doi.org/10.2196/93923)) – ICD-10-GM (year-specific; requires `year_col`) (`implementation="sokolowski"`)
- **Weights**:
  - Charlson et al. 1987 ([Charlson 1987](https://doi.org/10.1016/0021-9681(87)90171-8)) (`weights="charlson"`)
  - RCS, Armitage and van der Meulen 2010 ([Armitage & van der Meulen 2010](https://doi.org/10.1002/bjs.6930)) (`weights="rcs"`)
  - Quan et al. 2011 ([Quan 2011](https://doi.org/10.1093/aje/kwq433)) (`weights="quan"`)
  - UK SHMI, NHS Digital v1.60 (June 2026) (negative totals are floored at zero) (`weights="uk_shmi"`)

### Elixhauser Comorbidity Index

Categories are: `Congestive heart failure`, `Cardiac arrhythmias`, `Valvular disease`, `Pulmonary circulation disorders`, `Peripheral vascular disorders`, `Hypertension uncomplicated`, `Hypertension complicated`, `Paralysis`, `Other neurological disorders`, `Chronic pulmonary disease`, `Diabetes uncomplicated`, `Diabetes complicated`, `Hypothyroidism`, `Renal failure`, `Liver disease`, `Peptic ulcer disease excluding bleeding`, `AIDS/HIV`, `Lymphoma`, `Metastatic cancer`, `Solid tumor without metastasis`, `Rheumatoid arthritis/collagen vascular diseases`, `Coagulopathy`, `Obesity`, `Weight loss`, `Fluid and electrolyte disorders`, `Blood loss anemia`, `Deficiency anemia`, `Alcohol abuse`, `Drug abuse`, `Psychoses`, `Depression`.

- **Mappings**:
  - Elixhauser et al. 1998 ([Elixhauser 1998](https://doi.org/10.1097/00005650-199801000-00004)) – ICD-9-CM (`implementation="elixhauser"`)
  - Quan et al. 2005 ([Quan 2005](https://doi.org/10.1097/01.mlr.0000182534.19832.83)) – ICD-9-CM and ICD-10 (`implementation="quan"`)
  - AHRQ v3.7 ([AHRQ Comorbidity Software](https://hcup-us.ahrq.gov/toolssoftware/comorbidity/comorbidity.jsp)) – ICD-9-CM (`implementation="ahrq_icd9"`)
  - AHRQ Refined v2026.1 ([AHRQ Comorbidity Software](https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp)) – ICD-10-CM (year-specific; requires `year_col`) (`implementation="ahrq_icd10"`)
- **Weights**:
  - van Walraven et al. 2009 ([van Walraven 2009](https://doi.org/10.1097/MLR.0b013e31819432e5)) (`weights="van_walraven"`)
  - Thompson et al. 2015 ([Thompson 2015](https://doi.org/10.1097/MLR.0000000000000326)) (`weights="thompson_30"` or `weights="thompson_29"`)
  - AHRQ v3.7, Moore et al. 2017 ([Moore 2017](https://doi.org/10.1097/MLR.0000000000000735)) – ICD-9-CM (`weights="ahrq"`; always used with `implementation="ahrq_icd9"`)
  - AHRQ Refined v2026.1 ([AHRQ Comorbidity Software](https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp)) – ICD-10-CM (`weights="ahrq"`; always used with `implementation="ahrq_icd10"`)
  - Swiss, Sharma et al. 2021 ([Sharma 2021](https://doi.org/10.1186/s12913-020-05999-5)) (`weights="swiss"`)

### Combined Comorbidity Score

Categories are: `Alcohol abuse`, `Any tumor`, `Cardiac arrhythmias`, `Chronic pulmonary disease`, `Coagulopathy`, `Complicated diabetes`, `Congestive heart failure`, `Deficiency anemia`, `Dementia`, `Fluid and electrolyte disorders`, `Hemiplegia`, `HIV/AIDS`, `Hypertension`, `Liver disease`, `Metastatic cancer`, `Peripheral vascular disease`, `Psychosis`, `Pulmonary circulation disorders`, `Renal failure`, `Weight loss`.

- **Mappings**:
  - Gagne et al. 2011 ([Gagne 2011](https://doi.org/10.1016/j.jclinepi.2010.10.004)) – ICD-9-CM (`score="combined"`, `icd_version="icd9"`; Charlson conditions after Romano 1993, Elixhauser conditions after Quan 2005)
  - Sun et al. 2017 ([Sun 2017](https://doi.org/10.1097/MLR.0000000000000824)) – ICD-10-CM (`score="combined"`, `icd_version="icd10"`)
- **Weights**:
  - Gagne et al. 2011 ([Gagne 2011](https://doi.org/10.1016/j.jclinepi.2010.10.004)) (`score="combined"`)

### Hospital Frailty Risk Score

- **Mappings**:
  - Gilbert et al. 2018 ([Gilbert 2018](https://doi.org/10.1016/S0140-6736(18)30668-8)) – ICD-10 (`score="hfrs"`)
- **Weights**:
  - Gilbert et al. 2018 ([Gilbert 2018](https://doi.org/10.1016/S0140-6736(18)30668-8)) (`score="hfrs"`)

## Installation

You can install `pycomorb` via pip:

```bash
pip install pycomorb
```

## R Installation

To install the R version of the package (`rcomorb`), you first need to install the `polars` dependency from the R-multiverse repository, and then install the package locally:

```r
Sys.setenv(NOT_CRAN = "true") # Enable installation with pre-built Rust library binary
install.packages("polars", repos = "https://community.r-multiverse.org")
devtools::install("rcomorb")
```

## Usage

```python
import polars as pl
from pycomorb import comorbidity

# Example: Calculate Charlson score
df = pl.DataFrame({
    "id": [1, 2, 3],
    "code": ["I21", "E119", "C349"],
    "age": [65, 72, 80]
})

charlson = comorbidity(
    score="charlson",
    df=df,
    id_col="id",
    code_col="code",
    age_col="age",
    icd_version="icd10",
    implementation="quan",
    return_categories=True
)
```

See the docstrings in each module for details on arguments and supported variants.

### License and Documentation

---

- Free software: MIT license
- Documentation: (TODO)
- _Die Erstellung erfolgt unter Verwendung der maschinenlesbaren Fassung des Bundesinstituts für Arzneimittel und Medizinprodukte (BfArM)._