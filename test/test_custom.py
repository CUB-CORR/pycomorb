"""Custom comorbidity indices defined by a table of categories, codes and weights."""

import pandas as pd
import polars as pl
import pytest
from helpers import ICD9, ICD10, MIXED, by_id

import pycomorb as pc

DEFS = pl.DataFrame(
    {
        "category": ["Diabetes", "Hypertension", "Cancer"],
        "icd9_codes": ["250", "401|402", "174"],
        "icd10_codes": ["E10|E11", "I10|I13", "C50"],
        "weights": [2, 1, 5],
    }
)
# Scores of the ICD10 / ICD9 test patients under DEFS
EXPECTED = {1: 3, 2: 2, 3: 0, 4: 5}


def write(tmp_path, definitions=DEFS, **columns):
    """Write definitions (a frame, or given as columns) to a CSV file; return its path."""
    path = tmp_path / "d.csv"
    (pl.DataFrame(columns) if columns else definitions).write_csv(path)
    return path


def custom(df, **kw):
    """{patient id: score} of a custom index."""
    return by_id(pc.comorbidity("custom", df, **kw))


def test_path_definition(tmp_path):
    assert custom(ICD10, definition_data=write(tmp_path)) == EXPECTED


def test_polars_definition():
    assert custom(ICD10, definition_data=DEFS) == EXPECTED


def test_pandas_definition():
    assert custom(ICD10, definition_data=DEFS.to_pandas()) == EXPECTED


def test_str_path_definition(tmp_path):
    scores = custom(ICD10, definition_file_path=str(write(tmp_path)))
    assert scores == EXPECTED


def test_icd9_and_return_categories(tmp_path):
    res = pc.comorbidity(
        "custom",
        ICD9,
        icd_version="icd9",
        definition_data=write(tmp_path),
        return_categories=True,
    )
    assert {"Diabetes", "Hypertension", "Cancer"} <= set(res.columns)
    assert by_id(res) == EXPECTED


def test_mixed_versions(tmp_path):
    kw = dict(icd_version="icd9_10", icd_version_col="ver")
    assert custom(MIXED, definition_data=write(tmp_path), **kw) == EXPECTED


def test_custom_names(tmp_path):
    f = write(tmp_path, DEFS.rename({"weights": "w"}))
    res = pc.comorbidity(
        "custom", ICD10, definition_data=f, weight_col_name="w", score_col_name="S"
    )
    assert by_id(res, "S") == EXPECTED


def test_missing_weight_column(tmp_path):
    f = write(tmp_path, DEFS.drop("weights"))
    with pytest.raises(AssertionError):
        pc.comorbidity("custom", ICD10, definition_data=f)


def test_mutual_exclusion(tmp_path):
    f = write(
        tmp_path,
        category=["Diabetes complicated", "Diabetes uncomplicated"],
        icd10_codes=["E116", "E11"],
        weights=[2, 1],
    )
    df = pl.DataFrame({"id": [1], "code": ["E11.65"]})
    rule = [("Diabetes complicated", "Diabetes uncomplicated")]
    assert custom(df, definition_data=f) == {1: 3}
    assert custom(df, definition_data=f, mutual_exclusion_rules=rule) == {1: 2}


def test_mutual_exclusion_rule_with_unknown_category_is_rejected(tmp_path):
    f = write(tmp_path)
    rule = [("Diabetes", "Typo")]
    with pytest.raises(ValueError, match="Typo"):
        custom(ICD10, definition_data=f, mutual_exclusion_rules=rule)


def test_and_group_requires_all_rows(tmp_path):
    f = write(
        tmp_path,
        category=["X", "X"],
        and_group=["g", "g"],
        icd10_codes=["E11", "I10"],
        weights=[4, 4],
    )
    df = pl.DataFrame({"id": [1, 1, 2], "code": ["E11", "I10", "E11"]})
    assert custom(df, definition_data=f) == {1: 4, 2: 0}


def test_year_gating(tmp_path):
    f = write(tmp_path, category=["X"], year=[2020], icd10_codes=["E11"], weights=[1])
    df = pl.DataFrame({"id": [1, 2], "code": ["E11", "E11"], "year": [2019, 2021]})
    assert custom(df, definition_data=f) == {1: 0, 2: 1}


def test_more_than_63_definitions(tmp_path):
    f = write(
        tmp_path,
        category=[f"c{i}" for i in range(70)],
        icd10_codes=[f"A{i:02d}" for i in range(70)],
        weights=[1] * 70,
    )
    df = pl.DataFrame({"id": [1], "code": ["A69"]})
    assert custom(df, definition_data=f) == {1: 1}


def test_pandas_roundtrip(tmp_path):
    res = pc.comorbidity("custom", ICD10.to_pandas(), definition_data=write(tmp_path))
    assert isinstance(res, pd.DataFrame)
