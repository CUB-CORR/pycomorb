"""Shared constants, sample data and helper functions of the tests."""

import csv
import warnings
from pathlib import Path

import pandas as pd
import polars as pl
import yaml

import pycomorb as pc

ROOT = Path(__file__).resolve().parent.parent
COMMON = ROOT / "common"

# Definition file of every implementation, the versions each one supports, and the weighting schemes
CHARLSON_FILES = {
    "quan": "CHARLSON_QUAN",
    "deyo": "CHARLSON_DEYO",
    "romano": "CHARLSON_ROMANO",
    "dhoore": "CHARLSON_DHOORE",
    "australia": "CHARLSON_AUSTRALIA",
    "sweden": "CHARLSON_SWEDEN",
    "rcs": "CHARLSON_RCS",
    "uk_shmi": "CHARLSON_UK_SHMI_v1.60",
    "sokolowski": "CHARLSON_SOKOLOWSKI",
    "thygesen": "CHARLSON_THYGESEN",
}
ELIXHAUSER_FILES = {
    "quan": "ELIXHAUSER_QUAN",
    "elixhauser": "ELIXHAUSER",
    "ahrq_icd9": "ELIXHAUSER_AHRQ_ICD9",
    "ahrq_icd10": "ELIXHAUSER_AHRQ_ICD10",
}
CHARLSON_WEIGHTS = ["charlson", "schneeweiss", "rcs", "quan", "uk_shmi"]
ELIXHAUSER_WEIGHTS = ["van_walraven", "thompson_30", "thompson_29", "ahrq", "swiss"]
# Implementations limited to one ICD version; other versions are coerced with a warning
ICD9_ONLY = {"deyo", "romano", "dhoore", "elixhauser", "ahrq_icd9"}
ICD10_ONLY = {"australia", "rcs", "uk_shmi", "sokolowski", "thygesen", "ahrq_icd10"}


SCORES = ["charlson", "elixhauser", "gagne", "hfrs"]
# Name of the final score column of each score
CHARLSON, ELIXHAUSER, COMBINED, HFRS = (
    "Charlson Age-Comorbidity Score",
    "Elixhauser Comorbidity Index",
    "Combined Comorbidity Score",
    "HFRS Score",
)
ANY_VERSION = SCORES[:3]  # these accept icd9, icd10 and icd9_10; HFRS is ICD-10 only
# Sub-scores use assert, the dispatcher uses ValueError
BAD = (AssertionError, ValueError)


def read(stem):
    """Rows of common/<stem>.csv as dicts."""
    with open(COMMON / f"{stem}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aliases(name, impl):
    """Category renames of one implementation from common/<name> (a *_CATEGORY_ALIASES.yaml)."""
    with open(COMMON / name, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get(impl, {})


def first_code(codes):
    return codes.split("|")[0].strip() if codes else ""


def versions_of(impl):
    """ICD versions an implementation natively supports."""
    return (
        ["icd9"]
        if impl in ICD9_ONLY
        else ["icd10"]
        if impl in ICD10_ONLY
        else ["icd9", "icd10"]
    )


def _frame(rows):
    return pl.DataFrame(rows, schema=["id", "code", "age", "year", "ver"], orient="row")


# id 1: CHF + hypertension complicated (I13.0 / 402.91), id 2: diabetes, id 3: no hit, id 4: AIDS/HIV
ICD10 = _frame(
    [
        (1, "I13.0", 65, 2022, "ICD-10"),
        (1, "E11.9", 65, 2022, "ICD-10"),
        (2, "E11.65", 72, 2023, "ICD-10"),
        (2, "J44.9", 72, 2023, "ICD-10"),
        (3, "Z00.0", 40, 2023, "ICD-10"),
        (4, "B20", 55, 2020, "ICD-10"),
        (4, "C50.9", 55, 2020, "ICD-10"),
    ]
)
ICD9 = _frame(
    [
        (1, "402.91", 65, 2005, "ICD-9"),
        (1, "250.00", 65, 2005, "ICD-9"),
        (2, "250.40", 72, 2005, "ICD-9"),
        (2, "496", 72, 2005, "ICD-9"),
        (3, "V70.0", 40, 2005, "ICD-9"),
        (4, "042", 55, 2005, "ICD-9"),
        (4, "174.9", 55, 2005, "ICD-9"),
    ]
)
# Patient ids overlap on purpose: ids 1-4 appear in both eras
MIXED = pl.concat([ICD9, ICD10])


def col(result, name):
    """Values of one column of a polars or pandas result."""
    values = result[name]
    return values.to_list() if isinstance(result, pl.DataFrame) else values.tolist()


def ids(result):
    return sorted(col(result, "id"))


def is_pandas(x):
    return isinstance(x, pd.DataFrame)


def by_id(res, column=None):
    """{patient id: value} of one result column (default: the last one, i.e. the final score)."""
    return dict(zip(col(res, "id"), col(res, column or res.columns[-1])))


def patient(codes, age=30, **cols):
    """Frame of a single patient (id 1) with one row per code."""
    n = len(codes)
    return pl.DataFrame(
        {
            "id": [1] * n,
            "code": codes,
            "age": [age] * n,
            **{k: [v] * n for k, v in cols.items()},
        }
    )


def quiet(score, df, **kw):
    """comorbidity() with the (expected) coercion warnings silenced."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pc.comorbidity(score, df, **kw)


def score_of(res):
    """Final score of a single-patient result."""
    return res[res.columns[-1]][0]


def scored(score, df, **kw):
    """comorbidity() result sorted by patient id."""
    return pc.comorbidity(score, df, **kw).sort("id")
