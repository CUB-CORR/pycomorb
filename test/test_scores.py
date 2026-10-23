"""Scores: published weights, scoring rules and the 10-year survival formula."""

import math

import polars as pl
import pytest
from helpers import (
    CHARLSON,
    ELIXHAUSER,
    SCORES,
    first_code,
    patient,
    quiet,
    read,
    score_of,
    scored,
)

import pycomorb as pc
from pycomorb.CharlsonComorbidityIndex import CharlsonComorbidity_10year_survival


def test_unrelated_codes_score_zero():
    for score in SCORES:
        res = quiet(score, patient(["Z00.0", "Z76.2", "Z23", "R51"]))
        assert res.drop("id").row(0)[0] == 0, score


# --- published weights (one representative Quan ICD-10 code per category) -------------


# category: (code, Charlson 1987 weight, Quan 2011 weight)
CHARLSON_REPR = {
    "Myocardial infarction": ("I21.0", 1, 0),
    "Congestive heart failure": ("I50.0", 1, 2),
    "Peripheral vascular disease": ("I70.2", 1, 0),
    "Cerebrovascular disease": ("I63.9", 1, 0),
    "Dementia": ("F03", 1, 2),
    "Chronic pulmonary disease": ("J44.9", 1, 1),
    "Rheumatic disease": ("M05.9", 1, 1),
    "Peptic ulcer disease": ("K25.9", 1, 0),
    "Mild liver disease": ("K73.9", 1, 2),
    "Diabetes without chronic complication": ("E11.9", 1, 0),
    "Diabetes with chronic complication": ("E11.2", 2, 1),
    "Hemiplegia or paraplegia": ("G81.9", 2, 2),
    "Renal disease": ("N18.9", 2, 1),
    "Moderate or severe liver disease": ("I85.0", 3, 4),
    "Metastatic solid tumor": ("C78.0", 6, 6),
    "AIDS/HIV": ("B20", 6, 4),
}


# category: (code, van Walraven 2009 weight)
ELIX_VW = {
    "Congestive heart failure": ("I50.0", 7),
    "Cardiac arrhythmias": ("I48", 5),
    "Valvular disease": ("I34.0", -1),
    "Pulmonary circulation disorders": ("I26.9", 4),
    "Peripheral vascular disorders": ("I70.2", 2),
    "Paralysis": ("G81.9", 7),
    "Other neurological disorders": ("G40.9", 6),
    "Chronic pulmonary disease": ("J44.9", 3),
    "Renal failure": ("N18.9", 5),
    "Liver disease": ("K70.3", 11),
    "Lymphoma": ("C81.9", 9),
    "Metastatic cancer": ("C78.0", 12),
    "Solid tumor without metastasis": ("C50.9", 4),
    "Coagulopathy": ("D68.4", 3),
    "Obesity": ("E66.9", -4),
    "Weight loss": ("R63.4", 6),
    "Fluid and electrolyte disorders": ("E87.1", 5),
    "Drug abuse": ("F11.2", -7),
    "Depression": ("F32.9", -3),
}


# Gagne 2011: metastatic cancer 5; heart failure, dementia, renal failure, weight loss 2
GAGNE_WEIGHTS = {"C78.0": 5, "I50.0": 2, "F03": 2, "N18.9": 2, "R63.4": 2}


def test_charlson_published_weights():
    for category, (code, w1987, wquan) in CHARLSON_REPR.items():
        for weights, expected in (("charlson", w1987), ("quan", wquan)):
            res = quiet(
                "charlson", patient([code]), weights=weights, return_categories=True
            )
            assert res[category][0] == 1, category
            assert res[CHARLSON][0] == expected, (category, weights)


def test_elixhauser_van_walraven_weights():
    for category, (code, weight) in ELIX_VW.items():
        res = quiet("elixhauser", patient([code]), return_categories=True)
        assert res[category][0] == 1, category
        assert res[ELIXHAUSER][0] == weight, category


def test_gagne_published_weights():
    for code, weight in GAGNE_WEIGHTS.items():
        assert score_of(quiet("gagne", patient([code]))) == weight, code


def test_hfrs_published_weights():
    # Gilbert 2018: Alzheimer dementia (F00) 7.1, hemiplegia (G81) 4.4
    res = quiet("hfrs", patient(["F00.1", "G81.9"]))
    assert score_of(res) == pytest.approx(7.1 + 4.4)


# --- scoring rules --------------------------------------------------------------------


def test_charlson_age_points():
    # <50: 0, 50-59: 1, 60-69: 2, 70-79: 3, >=80: 4
    ages = [45, 55, 65, 75, 85]
    df = pl.DataFrame({"id": range(5), "code": ["Z00"] * 5, "age": ages})
    assert scored("charlson", df)[CHARLSON].to_list() == [0, 1, 2, 3, 4]


def test_charlson_sums_categories_and_age():
    res = pc.comorbidity("charlson", patient(["I21.0", "B20", "J44.9"], age=65))
    assert res[CHARLSON][0] == 1 + 6 + 1 + 2


@pytest.mark.parametrize(
    "codes,expected",
    [
        (["E11.9", "E11.2"], 2),  # complicated diabetes replaces uncomplicated
        (["K73.9", "I85.0"], 3),  # severe liver disease replaces mild
        (["C50.9", "C78.0"], 6),  # metastatic tumor replaces any malignancy
    ],
)
def test_charlson_mutual_exclusion_keeps_more_severe(codes, expected):
    assert score_of(quiet("charlson", patient(codes))) == expected


def test_rcs_counts_conditions_without_age():
    df = patient(["I21.0", "J44.9"], age=85)
    res = pc.comorbidity("charlson", df, implementation="rcs", weights="rcs")
    assert res[CHARLSON][0] == 2


@pytest.mark.parametrize("weights,age_points", [("charlson", 4), ("schneeweiss", 0), ("quan", 0), ("rcs", 0), ("uk_shmi", 0)])
def test_age_points_only_with_charlson_weights(weights, age_points):
    res = quiet("charlson", patient(["Z00.0"], age=85), weights=weights, return_categories=True)
    assert res["Age Score"][0] == age_points


def test_uk_shmi_negative_total_is_floored():
    category = "Diabetes complications"  # SHMI weights this category at -1
    row = next(r for r in read("CHARLSON_UK_SHMI_v1.60") if r["category"] == category)
    res = quiet(
        "charlson",
        patient([first_code(row["icd10_codes"])]),
        implementation="uk_shmi",
        return_categories=True,
    )
    assert res[category][0] == 1
    assert res["Charlson Comorbidity Index"][0] == 0


def test_code_with_several_categories_and_normalization():
    df = pl.DataFrame({"id": [1], "code": [" i130 "]})
    res = pc.comorbidity("elixhauser", df, return_categories=True)
    assert res["Congestive heart failure"][0] == 1
    assert res["Hypertension complicated"][0] == 1


# --- 10-year survival -----------------------------------------------------------------


@pytest.mark.parametrize("cci", range(6))
def test_ten_year_survival(cci):
    # Charlson 1994: 0.983 ** exp(0.9 * CCI)
    df = pl.DataFrame({"id": [1], CHARLSON: [cci]})
    res = CharlsonComorbidity_10year_survival(df, precalculated_df=True)
    expected = round(0.983 ** math.exp(0.9 * cci), 3)
    assert res["10-year survival probability"][0] == expected


def test_ten_year_survival_from_codes():
    res = CharlsonComorbidity_10year_survival(patient(["Z00.0"], age=30))
    assert res.columns == ["id", "10-year survival probability"]
    assert res["10-year survival probability"][0] == 0.983  # CCI 0
