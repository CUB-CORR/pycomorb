"""Input handling: invalid arguments, unusable values and invariances of the result."""

import pandas as pd
import polars as pl
import pytest
from helpers import (
    ANY_VERSION,
    BAD,
    ICD10,
    MIXED,
    SCORES,
    by_id,
    ids,
    scored,
)

import pycomorb as pc

# --- invalid arguments ----------------------------------------------------------------


@pytest.mark.parametrize(
    "kw",
    [
        {"implementation": "nope"},
        {"weights": "nope"},
        {"icd_version": "icd11"},
    ],
)
@pytest.mark.parametrize("score", ["charlson", "elixhauser"])
def test_unknown_values(score, kw, to_frame):
    with pytest.raises(BAD):
        pc.comorbidity(score, to_frame(ICD10), **kw)


@pytest.mark.parametrize("score", SCORES)
@pytest.mark.parametrize("missing", ["id", "code"])
def test_missing_columns(score, missing, to_frame):
    with pytest.raises(BAD + (pl.exceptions.PolarsError, KeyError)):
        pc.comorbidity(score, to_frame(ICD10.drop(missing)))


def test_charlson_needs_age(to_frame):
    with pytest.raises(ValueError, match="age"):
        pc.comorbidity("charlson", to_frame(ICD10.drop("age")))


@pytest.mark.parametrize("score", ANY_VERSION)
def test_icd9_10_needs_version_col(score, to_frame):
    with pytest.raises(BAD):
        pc.comorbidity(score, to_frame(MIXED), icd_version="icd9_10")
    with pytest.raises(BAD):
        pc.comorbidity(
            score, to_frame(MIXED), icd_version="icd9_10", icd_version_col="missing"
        )


# --- patients without a usable diagnosis are scored 0, never dropped ------------------


def with_extra_patient(code, age=50, year=2020):
    """ICD10 plus patient 99, whose only row has the given (invalid or missing) code."""
    extra = pl.DataFrame(
        {"id": [99], "code": [code], "age": [age], "year": [year], "ver": ["ICD-10"]},
        schema=ICD10.schema,
    )
    return pl.concat([ICD10, extra])


@pytest.mark.parametrize("score", SCORES)
@pytest.mark.parametrize("code", [None, "", "   ", "."])
def test_patient_without_valid_code_scores_zero(score, code, to_frame):
    res = pc.comorbidity(score, to_frame(with_extra_patient(code, age=30)))
    assert len(ids(res)) == 5 and by_id(res)[99] == 0


@pytest.mark.parametrize("score", SCORES)
def test_blank_codes_do_not_change_other_scores(score):
    blank = ICD10.with_columns(
        pl.when(pl.col("id") == 3)
        .then(pl.lit(""))
        .otherwise(pl.col("code"))
        .alias("code")
    )
    assert scored(score, blank).equals(scored(score, ICD10))


@pytest.mark.parametrize("score", SCORES)
def test_frame_with_only_blank_codes_scores_zero(score):
    res = pc.comorbidity(
        score,
        pl.DataFrame(
            {"id": [1, 2], "code": ["", None], "age": [50, 50]},
            schema_overrides={"code": pl.Utf8},
        ),
    )
    # Charlson adds the age points of a 50 year old
    expected = 1 if score == "charlson" else 0
    assert by_id(res) == {1: expected, 2: expected}


def test_empty_frame_gives_empty_result(to_frame):
    res = pc.comorbidity("elixhauser", to_frame(ICD10.clear()))
    assert len(res) == 0 and {"id", "Elixhauser Comorbidity Index"} <= set(res.columns)


# --- missing ages ---------------------------------------------------------------------


def test_missing_age_scores_zero_age_points(to_frame):
    d = ICD10.with_columns(
        pl.when(pl.col("id") == 3).then(None).otherwise(pl.col("age")).alias("age")
    )
    res = pc.comorbidity("charlson", to_frame(d), return_categories=True)
    # patient 3 has no diagnoses and an unknown age
    assert by_id(res, "Age Score")[3] == 0


# --- mixed ICD versions ---------------------------------------------------------------


@pytest.mark.parametrize("ver,version", [("ICD-9", "icd9"), ("ICD-10", "icd10")])
def test_mixed_mode_with_only_one_version_present(ver, version):
    one = MIXED.filter(pl.col("ver") == ver)
    mixed = pc.comorbidity(
        "charlson", one, icd_version="icd9_10", icd_version_col="ver"
    )
    assert mixed.sort("id").equals(
        pc.comorbidity("charlson", one, icd_version=version).sort("id")
    )


# --- non-string codes -----------------------------------------------------------------


@pytest.mark.parametrize("codes", [[428, 250], [428.0, 250.1]])
def test_numeric_codes_raise_a_clear_error(codes, to_frame):
    # 250.0 and "250.00" are different codes, so numbers must not be guessed into strings
    d = pl.DataFrame({"id": [1, 2], "code": codes})
    with pytest.raises(ValueError, match="string"):
        pc.comorbidity("elixhauser", to_frame(d), icd_version="icd9")


@pytest.mark.parametrize("score", SCORES)
def test_categorical_codes_are_accepted(score):
    categorical = ICD10.with_columns(pl.col("code").cast(pl.Categorical))
    assert scored(score, categorical).equals(scored(score, ICD10))


# --- direct calls ---------------------------------------------------------------------


def test_hfrs_function_accepts_pandas_directly():
    res = pc.HospitalFrailtyRiskScore(ICD10.to_pandas())
    assert isinstance(res, pd.DataFrame) and len(res) == 4


# --- invariances ----------------------------------------------------------------------


@pytest.mark.parametrize("score", SCORES)
def test_result_independent_of_order_and_duplicates(score):
    base = scored(score, ICD10)
    assert scored(score, ICD10.sample(fraction=1.0, shuffle=True, seed=1)).equals(base)
    assert scored(score, pl.concat([ICD10, ICD10])).equals(base)


@pytest.mark.parametrize("score", SCORES)
def test_patients_are_scored_independently(score):
    whole = scored(score, ICD10)
    for patient_id in ICD10["id"].unique():
        alone = pc.comorbidity(score, ICD10.filter(pl.col("id") == patient_id))
        assert alone.equals(whole.filter(pl.col("id") == patient_id))


@pytest.mark.parametrize("score", SCORES)
def test_pandas_and_polars_agree_for_string_ids(score):
    df = ICD10.with_columns(("p" + pl.col("id").cast(pl.Utf8)).alias("id"))
    from_pandas = pl.from_pandas(pc.comorbidity(score, df.to_pandas())).sort("id")
    assert from_pandas.equals(scored(score, df))
