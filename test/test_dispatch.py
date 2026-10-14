"""The comorbidity() entry point: score names, defaults, column names, input and output types."""

import pytest
from helpers import (
    ANY_VERSION,
    BAD,
    CHARLSON,
    COMBINED,
    ELIXHAUSER,
    HFRS,
    ICD9,
    ICD10,
    SCORES,
    ids,
    is_pandas,
)

import pycomorb as pc

# --- score names and defaults ---------------------------------------------------------


ALIASES = {
    CHARLSON: (
        "cci charlson CharlsonComorbidityIndex charlson_comorbidity_index CHARLSON"
    ),
    ELIXHAUSER: (
        "eci elixhauser elixhausercomorbidityindex elixhauser_comorbidity_index"
    ),
    COMBINED: (
        "ccs combined combinedcomorbidityindex combined_comorbidity_index "
        "combinedcomorbidityscore combined_comorbidity_score "
        "gagne gagnecomorbidityindex gagne_comorbidity_index"
    ),
    HFRS: "hfrs hospitalfrailtyriskscore hospital_frailty_risk_score",
}


# (name of the score column, alias)
FLAT = [(column, alias) for column, names in ALIASES.items() for alias in names.split()]


@pytest.mark.parametrize("column,alias", FLAT)
def test_alias_resolves_to_the_score(column, alias):
    assert column in pc.comorbidity(alias, ICD10).columns


@pytest.mark.parametrize(
    "alias", ["custom", "customcomorbidityindex", "custom_comorbidity_index"]
)
def test_custom_aliases(alias, tmp_path):
    f = tmp_path / "defs.csv"
    f.write_text("category,icd10_codes,weights\nx,E11,3\n")
    assert pc.comorbidity(alias, ICD10, definition_data=f).shape[0] == 4


@pytest.mark.parametrize("bad", ["", "foo", "ccsr", "charlson2"])
def test_unknown_score(bad):
    with pytest.raises(ValueError, match="Unknown score"):
        pc.comorbidity(bad, ICD10)


def test_defaults_match_explicit():
    a = pc.comorbidity("charlson", ICD10)
    b = pc.comorbidity(
        "charlson",
        ICD10,
        implementation="quan",
        weights="charlson",
        icd_version="icd10",
    )
    assert a.sort("id").equals(b.sort("id"))
    a = pc.comorbidity("elixhauser", ICD9, icd_version="icd9")
    b = pc.comorbidity(
        "elixhauser",
        ICD9,
        icd_version="icd9",
        implementation="quan",
        weights="van_walraven",
    )
    assert a.sort("id").equals(b.sort("id"))


# --- column names and frame types -----------------------------------------------------


@pytest.mark.parametrize("score", SCORES)
def test_custom_column_names(score, to_frame):
    d = ICD10.rename({"id": "pid", "code": "dx", "age": "a", "year": "y"})
    res = pc.comorbidity(
        score, to_frame(d), id_col="pid", code_col="dx", age_col="a", year_col="y"
    )
    assert "pid" in res.columns


@pytest.mark.parametrize("score", SCORES)
def test_pandas_in_pandas_out_and_return_categories(score):
    plain = pc.comorbidity(score, ICD10.to_pandas())
    cats = pc.comorbidity(score, ICD10.to_pandas(), return_categories=True)
    assert is_pandas(plain) and is_pandas(cats) and len(plain) == len(cats) == 4
    assert set(plain.columns) < set(cats.columns)


@pytest.mark.parametrize("score", ANY_VERSION)
def test_icd10_year_col_is_optional_for_default_impl(score, to_frame):
    assert len(ids(pc.comorbidity(score, to_frame(ICD10.drop("year"))))) == 4


def test_year_required_for_year_dependent_variants(to_frame):
    d = to_frame(ICD10.drop("year"))
    with pytest.raises(BAD):
        pc.comorbidity("charlson", d, implementation="sokolowski")
    with pytest.raises(BAD):
        pc.comorbidity("elixhauser", d, implementation="ahrq_icd10", weights="ahrq")


@pytest.mark.parametrize("v,df", [("icd9", ICD9), ("icd10", ICD10)])
def test_scoring_does_not_mutate_the_input(v, df, to_frame):
    d = to_frame(df)
    before = d.copy() if is_pandas(d) else d.clone()
    for s in ANY_VERSION:
        pc.comorbidity(s, d, icd_version=v)
    assert d.equals(before)
