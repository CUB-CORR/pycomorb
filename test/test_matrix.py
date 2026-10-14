"""Cross-product of every comorbidity() argument: each combination must return a valid frame or the documented error."""

import warnings

import pytest
from helpers import (
    BAD,
    CHARLSON_FILES,
    CHARLSON_WEIGHTS,
    ELIXHAUSER_FILES,
    ELIXHAUSER_WEIGHTS,
    ICD9,
    ICD9_ONLY,
    ICD10,
    ICD10_ONLY,
    MIXED,
    ids,
    is_pandas,
)

import pycomorb as pc

VERSIONS = ["icd9", "icd10", "icd9_10"]


DATA = {"icd9": ICD9, "icd10": ICD10, "icd9_10": MIXED}


# icd9_10 rows are split on this column; every other value is treated as ICD-10
KW_VER = {"icd9_10": {"icd_version_col": "ver"}}


def run(score, version, to_frame=lambda d: d, **kw):
    """Result of comorbidity() on the test data plus the warnings it raised."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        res = pc.comorbidity(
            score,
            to_frame(DATA[version]),
            icd_version=version,
            **KW_VER.get(version, {}),
            **kw,
        )
    return res, any(issubclass(x.category, UserWarning) for x in w)


def coerced(impl, version):
    """Implementations limited to one ICD version coerce other versions (with a warning)."""
    return (impl in ICD9_ONLY and version != "icd9") or (
        impl in ICD10_ONLY and version != "icd10"
    )


def check_ok(res, version, to_frame=lambda d: d):
    # output type follows input type
    assert is_pandas(res) == is_pandas(to_frame(ICD10))
    # one row per patient
    assert len(ids(res)) == len(set(ids(res))) == DATA[version]["id"].n_unique()


@pytest.mark.parametrize("w", CHARLSON_WEIGHTS)
@pytest.mark.parametrize("impl", CHARLSON_FILES)
@pytest.mark.parametrize("version", VERSIONS)
def test_charlson_matrix(version, impl, w):
    res, warned = run(
        "charlson", version, implementation=impl, weights=w, return_categories=True
    )
    check_ok(res, version)
    assert {
        "Charlson Age-Comorbidity Score",
        "Charlson Comorbidity Index",
        "Age Score",
    } <= set(res.columns)
    assert warned or not coerced(impl, version)


@pytest.mark.parametrize("w", ELIXHAUSER_WEIGHTS)
@pytest.mark.parametrize("impl", ELIXHAUSER_FILES)
@pytest.mark.parametrize("version", VERSIONS)
def test_elixhauser_matrix(version, impl, w):
    # mixed input has no single AHRQ weight column
    if w == "ahrq" and version == "icd9_10" and impl == "quan":
        with pytest.raises(ValueError):
            run("elixhauser", version, implementation=impl, weights=w)
        return
    res, warned = run(
        "elixhauser", version, implementation=impl, weights=w, return_categories=True
    )
    check_ok(res, version)
    assert "Elixhauser Comorbidity Index" in res.columns
    assert warned or not coerced(impl, version)


@pytest.mark.parametrize("version", VERSIONS)
def test_combined_matrix(version):
    res, _ = run("gagne", version, return_categories=True)
    check_ok(res, version)
    assert "Combined Comorbidity Score" in res.columns


def test_hfrs_icd10(to_frame):
    res, _ = run("hfrs", "icd10", to_frame)
    check_ok(res, "icd10", to_frame)
    assert "HFRS Score" in res.columns


@pytest.mark.parametrize("version", ["icd9", "icd9_10"])
def test_hfrs_rejects_other_versions(version, to_frame):
    with pytest.raises(BAD):
        run("hfrs", version, to_frame)


@pytest.mark.parametrize("w,impl", [("rcs", "uk_shmi"), ("uk_shmi", "rcs")])
def test_charlson_mismatched_weights_warn(w, impl, to_frame):
    assert run("charlson", "icd10", to_frame, implementation=impl, weights=w)[1]
