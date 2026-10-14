"""ICD modification: transfer tables and their use through comorbidity()."""

import csv
import random
import warnings

import polars as pl
import pytest
from helpers import (
    ANY_VERSION,
    COMMON,
    ICD9,
    ICD10,
    MIXED,
    patient,
    scored,
)

import pycomorb as pc
from pycomorb.ICDModifications import get_icd10cm, get_icd10gm

# --- crosswalk tables (oracle: the transfer tables themselves) ------------------------


CROSSWALKS = [
    # function, file, target years to check, target years the function must accept
    (get_icd10gm, "modification_DE/icd10gm.csv", [2004, 2020, 2026], range(2004, 2027)),
    (get_icd10cm, "modification_US/icd10cm.csv", [2015, 2020, 2027], range(2015, 2028)),
]


def read_crosswalk(name):
    """(years, rows) of a transfer table; every row lists one code per year."""
    with open(COMMON / name, encoding="utf-8") as f:
        reader = csv.reader(f)
        return [int(year) for year in next(reader)], list(reader)


def allowed_targets(table, source, target):
    """{code in the source year: set of codes it may map to in the target year}."""
    allowed = {}
    for row in table:
        allowed.setdefault(row[source].strip(), set()).add(row[target].strip())
    return allowed


def sample_codes(table, source, rnd):
    """Codes of the source year (UNDEF marks codes that do not exist in that year)."""
    codes = {row[source].strip() for row in rnd.sample(table, 300)}
    return sorted(c for c in codes if c and not c.startswith("UNDEF"))


@pytest.mark.parametrize("fn,name,targets,valid", CROSSWALKS)
def test_modification_matches_transfer_table(fn, name, targets, valid):
    years, table = read_crosswalk(name)
    # the accepted target years are exactly the table's columns
    assert years == list(valid)
    rnd = random.Random(0)
    for target in targets:
        for source_year in rnd.sample(years, 3):
            source, column = years.index(source_year), years.index(target)
            allowed = allowed_targets(table, source, column)
            codes = sample_codes(table, source, rnd)
            if not codes:  # e.g. the first ICD-10-CM year is mostly UNDEF placeholders
                continue
            df = pl.DataFrame({"code": codes, "year": [source_year] * len(codes)})
            out = fn(df, target_year=target)
            # 1:n splits add rows, none may be lost
            assert set(out["code"]) == set(codes)
            for code, mapped in zip(out["code"], out[f"icd_{target}"]):
                undefined = any(a.startswith("UNDEF") for a in allowed[code])
                # codes without a counterpart are kept unchanged
                assert mapped in allowed[code] or (undefined and mapped == code)


@pytest.mark.parametrize("fn,name,targets,valid", CROSSWALKS)
def test_modification_rejects_target_years_outside_the_table(fn, name, targets, valid):
    df = pl.DataFrame({"code": ["A00"], "year": [2020]})
    for bad in (valid[0] - 1, valid[-1] + 1):
        with pytest.raises(AssertionError):
            fn(df, target_year=bad)


# --- through comorbidity() ------------------------------------------------------------


@pytest.mark.parametrize("mod", ["icd10gm", "ICD10GM", "icd10cm", "Icd10CM"])
def test_modification_runs(mod, to_frame):
    kw = dict(icd_modification=mod, icd_modification_target_year=2023)
    for score in ANY_VERSION:
        res = pc.comorbidity(score, to_frame(ICD10), **kw)
        assert len(res) == 4


@pytest.mark.parametrize("mod", ["icd10gm", "icd10cm"])
def test_default_target_year_is_valid_for_each_modification(mod):
    assert len(pc.comorbidity("charlson", ICD10, icd_modification=mod)) == 4


@pytest.mark.parametrize("year", [2016, 2023, 2026])
def test_year_specific_variants_run_for_catalogue_years(year):
    codes = ["I50.0", "E11.65"]
    df = patient(codes, age=60, year=year).with_columns(pl.Series("id", [1, 2]))
    gm = dict(implementation="sokolowski", icd_modification="icd10gm")
    cm = dict(implementation="ahrq_icd10", weights="ahrq", icd_modification="icd10cm")
    with warnings.catch_warnings():
        # years inside both transfer tables must not warn
        warnings.simplefilter("error")
        for score, kw in (("charlson", gm), ("elixhauser", cm)):
            res = pc.comorbidity(score, df, icd_modification_target_year=year, **kw)
            assert res.height == 2


@pytest.mark.parametrize("bad", ["icd10xx", "gm", ""])
def test_unknown_modification(bad):
    with pytest.raises(ValueError, match="Unknown icd_modification"):
        pc.comorbidity("charlson", ICD10, icd_modification=bad)


def test_modification_is_ignored_for_icd9():
    plain = scored("charlson", ICD9, icd_version="icd9")
    modified = scored("charlson", ICD9, icd_version="icd9", icd_modification="icd10gm")
    assert plain.equals(modified)


# --- input problems -------------------------------------------------------------------


def test_modification_needs_year_col():
    with pytest.raises(AssertionError, match="year"):
        pc.comorbidity("charlson", ICD10.drop("year"), icd_modification="icd10gm")


def test_null_year_with_modification_names_the_problem():
    d = ICD10.with_columns(pl.lit(None, dtype=pl.Int64).alias("year"))
    with pytest.raises((AssertionError, ValueError), match="year"):
        pc.comorbidity("charlson", d, icd_modification="icd10gm")


@pytest.mark.parametrize("year", [1999, 2100])
def test_year_outside_the_crosswalk_warns(year):
    d = ICD10.with_columns(pl.lit(year).alias("year"))
    with pytest.warns(UserWarning, match="year"):
        pc.comorbidity(
            "charlson", d, icd_modification="icd10gm", icd_modification_target_year=2020
        )


def test_modification_only_touches_icd10_rows_of_mixed_input():
    res = pc.comorbidity(
        "charlson",
        MIXED,
        icd_version="icd9_10",
        icd_version_col="ver",
        icd_modification="icd10cm",
    )
    assert len(res) == 4


def test_mixed_mode_modification_without_icd10_rows():
    icd9 = MIXED.filter(pl.col("ver") == "ICD-9")
    kw = dict(icd_version="icd9_10", icd_version_col="ver")
    modified = scored("charlson", icd9, icd_modification="icd10gm", **kw)
    assert modified.equals(scored("charlson", icd9, **kw))
