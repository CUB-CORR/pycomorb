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

Categories are: `Myocardial infarction`, `Congestive heart failure`, `Peripheral vascular disease`, `Cerebrovascular disease`, `Dementia`, `Chronic pulmonary disease`, `Rheumatic disease`, `Peptic ulcer disease`, `Mild liver disease`, `Diabetes without chronic complication`, `Diabetes with chronic complication`, `Hemiplegia or paraplegia`, `Renal disease`, `Any malignancy, including lymphoma and leukemia, except malignant neoplasm of skin`, `Moderate or severe liver disease`, `Metastatic solid tumor`, `AIDS/HIV`.

- **Mappings**:
  - Quan et al. 2005 ([Quan 2005](https://doi.org/10.1097/01.mlr.0000182534.19832.83))
  - Deyo et al. 1992 ([Deyo 1992](https://doi.org/10.1016/0895-4356(92)90133-8))
  - Romano et al. 1993 ([Romano 1993](https://doi.org/10.1016/0895-4356(93)90103-8))
  - Australia (Sundararajan et al. 2004, ICD-10-AM) ([Sundararajan 2004](https://doi.org/10.1016/j.jclinepi.2004.03.012))
  - Sweden (Ludvigsson et al. 2021, ICD-10) ([Ludvigsson 2021](https://doi.org/10.2147/CLEP.S282475))
  - UK SHMI (NHS Digital, v1.55)
- **Weights**:
  - Charlson et al. 1987 ([Charlson 1987](https://doi.org/10.1016/0021-9681(87)90171-8))
  - Quan et al. 2011 ([Quan 2011](https://doi.org/10.1097/MLR.0b013e31821c2e56))
  - SHMI (NHS Digital, v1.55)
  - Modified SHMI (NHS Digital, v1.55)

### Elixhauser Comorbidity Index

Categories are: `Congestive heart failure`, `Cardiac arrhythmias`, `Valvular disease`, `Pulmonary circulation disorders`, `Peripheral vascular disorders`, `Hypertension uncomplicated`, `Hypertension complicated`, `Paralysis`, `Other neurological disorders`, `Chronic pulmonary disease`, `Diabetes uncomplicated`, `Diabetes complicated`, `Hypothyroidism`, `Renal failure`, `Liver disease`, `Peptic ulcer disease excluding bleeding`, `AIDS/HIV`, `Lymphoma`, `Metastatic cancer`, `Solid tumor without metastasis`, `Rheumatoid arthritis/collagen vascular diseases`, `Coagulopathy`, `Obesity`, `Weight loss`, `Fluid and electrolyte disorders`, `Blood loss anemia`, `Deficiency anemia`, `Alcohol abuse`, `Drug abuse`, `Psychoses`, `Depression`.

- **Mappings**:
  - Quan et al. 2005 ([Quan 2005](https://doi.org/10.1097/01.mlr.0000182534.19832.83))
  - Original Elixhauser et al. 1998 (ICD-9) ([Elixhauser 1998](https://doi.org/10.1097/00005650-199801000-00004))
- **Weights**:
  - van Walraven et al. 2009 ([van Walraven 2009](https://doi.org/10.1097/MLR.0b013e31819432e5))
  - Thompson et al. 2015 ([Thompson 2015](https://doi.org/10.1097/MLR.0000000000000326))
  - AHRQ (Moore et al. 2017, [AHRQ Comorbidity Software](https://hcup-us.ahrq.gov/toolssoftware/comorbidityicd10/comorbidity_icd10.jsp))

### Combined Comorbidity Score

Categories are: `Alcohol abuse`, `Any tumor`, `Cardiac arrhythmias`, `Chronic pulmonary disease`, `Coagulopathy`, `Complicated diabetes`, `Congestive heart failure`, `Deficiency anemia`, `Dementia`, `Fluid and electrolyte disorders`, `Hemiplegia`, `HIV/AIDS`, `Hypertension`, `Liver disease`, `Metastatic cancer`, `Peripheral vascular disease`, `Psychosis`, `Pulmonary circulation disorders`, `Renal failure`, `Weight loss`.

- Gagne et al. 2011 ([Gagne 2011](https://doi.org/10.1016/j.jclinepi.2010.10.004)), with ICD-9 and ICD-10 support ([Sun 2017](https://doi.org/10.1097/MLR.0000000000000824))

### Hospital Frailty Risk Score

- Gilbert et al. 2018, ICD-10 ([Gilbert 2018](https://doi.org/10.1016/S0140-6736(18)30668-8))

## Installation

You can install `pycomorb` via pip:

```bash
pip install pycomorb
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