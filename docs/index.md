# pycomorb

Comorbidity and frailty scores (Charlson, Elixhauser, Combined Comorbidity Score, HFRS) from ICD-9/ICD-10 codes, built on [polars](https://pola.rs). Its distinguishing feature is harmonising ICD-10-GM / ICD-10-CM codes across code-set years before scoring.

## Installation

```bash
pip install pycomorb
```

Requires Python 3.10+ and `polars>=1.21.0`; `pandas`, `pyarrow` and `pyyaml` are installed as dependencies.

## Quickstart

One row per patient and code. Polars in, polars out; a pandas DataFrame returns a pandas DataFrame.

```python
import polars as pl
from pycomorb import comorbidity

df = pl.DataFrame({
    "id": [1, 2, 3],
    "code": ["I21", "E119", "C349"],
    "age": [65, 72, 80],
})

result = comorbidity(
    score="charlson", df=df, id_col="id", code_col="code", age_col="age",
    icd_version="icd10", implementation="quan", return_categories=True,
)
```

`return_categories=True` adds one column per comorbidity category next to the score.

## More

- Citation: see [CITATION.cff](https://github.com/CUB-CORR/pycomorb/blob/main/CITATION.cff).
- Data sources and attributions (including BfArM ICD-10-GM): [NOTICE](https://github.com/CUB-CORR/pycomorb/blob/main/NOTICE).
- Citations for every variant: [References](references.md).
- MIT license.
