# Scores

`comorbidity(score=..., ...)` calculates one of the scores below. `score` is case-insensitive; the result has one row per `id_col` with the score in the column named in the table.

<div class="wide-2 wide-3" markdown="1">

| `score` | Aliases | Output column | Default `implementation` | Default `weights` |
|---|---|---|---|---|
| `charlson` | `cci`, `charlsoncomorbidityindex`, `charlson_comorbidity_index` | `Charlson Age-Comorbidity Score` | `quan` | `charlson` |
| `elixhauser` | `eci`, `elixhausercomorbidityindex`, `elixhauser_comorbidity_index` | `Elixhauser Comorbidity Index` | `quan` | `van_walraven` |
| `combined` | `ccs`, `gagne`, `combinedcomorbidityscore`, `combined_comorbidity_score` | `Combined Comorbidity Score` | none | none |
| `hfrs` | `hospitalfrailtyriskscore`, `hospital_frailty_risk_score` | `HFRS Score` | none | none |
| `custom` | `customcomorbidityindex` | `score_col_name` (default `Custom Comorbidity Score`) | none | none |

</div>

Options shared by all scores:

<div class="wide-3" markdown="1">

| Argument | Default | Meaning |
|---|---|---|
| `id_col`, `code_col` | `"id"`, `"code"` | Patient identifier and ICD code columns (one row per patient and code) |
| `age_col` | `"age"` | Age in years. Required for `charlson` only |
| `year_col` | `"year"` | Year of the code. Required for the year-specific implementations below and for [ICD modification](icd-modification.md) |
| `icd_version` | `"icd10"` | `"icd9"`, `"icd10"` or `"icd9_10"` (the latter needs `icd_version_col` with the values `"ICD-9"` / `"ICD-10"` per row) |
| `return_categories` | `False` | Also return one 0/1 column per category (and `Age Score` for Charlson) |

</div>

If the chosen `implementation` covers only one ICD version, `icd_version` is switched to it with a `UserWarning`. Full citations are in [References](references.md).

## Charlson Comorbidity Index

Score = sum of category weights + age points. The original index is [Charlson 1987](references.md#charlson1987) (see also [Charlson 1994](references.md#charlson1994)). Age points are 0 (<50), 1 (50–59), 2 (60–69), 3 (70–79), 4 (≥80) and are added for `weights="charlson"` only. `schneeweiss`, `quan`, `rcs` and `uk_shmi` define no age points; the implementations (code lists) never define age points themselves. A patient's age is the highest value in their rows; a missing age gives 0 points.

Hierarchy: *diabetes with chronic complication* replaces *diabetes without*, *moderate or severe liver disease* replaces *mild liver disease*, and *metastatic solid tumor* replaces *any malignancy*.

### `implementation`

<div class="wide-4" markdown="1">

| Value | Reference | ICD | Notes |
|---|---|---|---|
| `quan` (default) | [Quan 2005](references.md#quan2005) | ICD&#8209;9&#8209;CM, ICD&#8209;10 | |
| `deyo` | [Deyo 1992](references.md#deyo1992) | ICD&#8209;9&#8209;CM | |
| `romano` | [Romano 1993](references.md#romano1993) | ICD&#8209;9&#8209;CM | Codes as in the revision of the paper; no *rheumatic disease* or *AIDS* codes in the original table |
| `dhoore` | [D'Hoore 1996](references.md#dhoore1996) | ICD&#8209;9&#8209;CM | |
| `australia` | [Sundararajan 2004](references.md#sundararajan2004) | ICD&#8209;10&#8209;AM | Categories renamed (e.g. *Cancer*, *HIV*) |
| `thygesen` | [Thygesen 2011](references.md#thygesen2011) | ICD&#8209;10 | Denmark; *Any tumor*, *Leukemia*, *Lymphoma* kept separate |
| `sweden` | [Ludvigsson 2021](references.md#ludvigsson2021) | ICD&#8209;9, ICD&#8209;10 | Swedish ICD-9; pulmonary disease split in two categories |
| `rcs` | [Armitage 2010](references.md#armitage2010) | ICD&#8209;10 | Always RCS weights; no *peptic ulcer*; liver disease and diabetes not split by severity |
| `uk_shmi` | [NHS Digital 2026](references.md#nhs2026) | ICD&#8209;10 | Version 1.60 (June 2026). Always SHMI weights |
| `sokolowski` | [Sokołowski 2026](references.md#sokolowski2026) | ICD&#8209;10&#8209;GM | Germany; year-specific, **requires `year_col`** |

</div>

### `weights`

| Value | Reference | Notes |
|---|---|---|
| `charlson` (default) | [Charlson 1987](references.md#charlson1987) | |
| `schneeweiss` | [Schneeweiss 2003](references.md#schneeweiss2003) | No age points |
| `quan` | [Quan 2011](references.md#quan2011) | No age points |
| `rcs` | [Armitage 2010](references.md#armitage2010) | Every category counts 1; no age points |
| `uk_shmi` | [NHS Digital 2026](references.md#nhs2026) | Negative totals are set to 0 |

`rcs` and `uk_shmi` implementations always use their own weights; another `weights` value is replaced with a `UserWarning`.

## Elixhauser Comorbidity Index

Score = sum of category weights (no age). The original index is [Elixhauser 1998](references.md#elixhauser1998).

Hierarchy: *complicated* replaces *uncomplicated* diabetes and hypertension, and *metastatic cancer* replaces *solid tumor without metastasis*. `ahrq_icd10` adds severity tiers for liver disease and renal failure and an in-situ tumor tier.

### `implementation`

<div class="wide-4" markdown="1">

| Value | Reference | ICD | Notes |
|---|---|---|---|
| `quan` (default) | [Quan 2005](references.md#quan2005) | ICD&#8209;9&#8209;CM, ICD&#8209;10 | |
| `elixhauser` | [Elixhauser 1998](references.md#elixhauser1998) | ICD&#8209;9&#8209;CM | |
| `ahrq_icd9` | [AHRQ v3.7](references.md#ahrq-icd9) | ICD&#8209;9&#8209;CM | No *cardiac arrhythmias*. Always AHRQ weights |
| `ahrq_icd10` | [AHRQ&nbsp;Refined v2026.1](references.md#ahrq-icd10) | ICD&#8209;10&#8209;CM | Year-specific, **requires `year_col`**. Always AHRQ weights. Different category set: no *cardiac arrhythmias* or *fluid and electrolyte disorders*; adds e.g. *dementia*, *leukemia*, *seizures and epilepsy* |

</div>

### `weights`

<div class="wide-2 wide-3" markdown="1">

| Value | Reference | Notes |
|---|---|---|
| `van_walraven` (default) | [van Walraven 2009](references.md#vanwalraven2009) | |
| `thompson_30` | [Thompson 2015](references.md#thompson2015) | |
| `thompson_29` | [Thompson 2015](references.md#thompson2015) | |
| `swiss` | [Sharma 2021](references.md#sharma2021) | |
| `ahrq` | [Moore 2017](references.md#moore2017) (ICD-9-CM), [AHRQ&nbsp;Refined v2026.1](references.md#ahrq-icd10) (ICD-10-CM) | Picked by `icd_version`; `ahrq_icd9` / `ahrq_icd10` enforce it |

</div>

The `ahrq_icd9` / `ahrq_icd10` implementations also replace any other `weights` value with a `UserWarning`. `weights="ahrq"` does not work with `icd_version="icd9_10"` (`ValueError`).

## Combined Comorbidity Score

20 categories, no `implementation` or `weights` options. `icd_version` selects the mapping:

<div class="wide-3" markdown="1">

| `icd_version` | Reference | Notes |
|---|---|---|
| `icd9` | [Gagne 2011](references.md#gagne2011) | Charlson conditions after Romano 1993, Elixhauser conditions after Quan 2005 |
| `icd10` | [Sun 2017](references.md#sun2017) | ICD&#8209;10&#8209;CM |

</div>

Weights are those of [Gagne 2011](references.md#gagne2011).

## Hospital Frailty Risk Score

ICD-10 only; no `implementation` or `weights` options. Mapping and weights from [Gilbert 2018](references.md#gilbert2018) (supplementary appendix).

## Category lists

The category names of every variant are listed in the [README](https://github.com/CUB-CORR/pycomorb#supported-variants) and are returned as column names with `return_categories=True`. For the exact codes and weights behind any variant, use [`comorbidity_reporting`](reporting.md).
