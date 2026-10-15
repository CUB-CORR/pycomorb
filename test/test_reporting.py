import sys

import polars as pl
import pytest

from pycomorb import comorbidity, comorbidity_reporting, read_reporting
from pycomorb.Reporting import markdown_table


def template(*args, **kwargs):
    return dict(comorbidity_reporting(*args, **kwargs)[0].iter_rows())


def test_template_lists_all_domains(tmp_path):
    template, *_ = comorbidity_reporting(
        "charlson", "quan", "quan", path=tmp_path, look_back_period="index stay"
    )
    info = dict(template.iter_rows())
    assert list(info)[:3] == [
        "Data source(s)",
        "Method of data extraction",
        "Comorbidity weighting reference",
    ]
    assert info["Comorbidity weighting reference"] == "Quan et al. (2011)"
    assert info["Look-back period"] == "index stay"
    assert info["Data source(s)"] == ""
    for file in ("template.md", "weights.csv", "codes.csv", "hierarchy.csv"):
        assert (tmp_path / file).is_file()
    lines = (tmp_path / "template.md").read_text(encoding="utf-8").splitlines()
    assert lines[:2] == ["| domain | information |", "|---|---|"]
    assert "| Look-back period | index stay |" in lines


def test_markdown_table_escapes_pipes():
    table = pl.DataFrame({"a": ["x|y"], "b": ["one\ntwo"]})
    assert markdown_table(table).splitlines()[2] == "| x\\|y | one two |"


@pytest.mark.parametrize("score", ["charlson", "elixhauser", "combined", "hfrs"])
def test_every_score(score):
    template, weights, *_ = comorbidity_reporting(score)
    assert template.height == 13
    assert weights["weight"].null_count() < weights.height


def test_implementation_overrides():
    info = template("charlson", "rcs", "charlson")
    assert info["Age adjustment"] == "Not applied"
    assert (
        info["Comorbidity weighting reference"] == "Armitage and van der Meulen (2010)"
    )
    assert template("charlson", "deyo")["Disease classification system"] == "ICD-9-CM"
    assert (
        template("charlson", icd_modification="icd10gm")[
            "Disease classification system"
        ]
        == "ICD-10, mapped with icd10gm"
    )
    _, ahrq_weights, *_ = comorbidity_reporting("elixhauser", "ahrq_icd10", "swiss")
    assert (
        template("elixhauser", "ahrq_icd10", "swiss")["Comorbidity weighting reference"]
        == "Moore et al. (2017)"
    )
    assert ahrq_weights["weight"].null_count() < ahrq_weights.height
    _, _, both, _ = comorbidity_reporting("combined", icd_version="icd9_10")
    assert set(both["icd_version"]) == {"ICD-9-CM", "ICD-10"}
    assert both["code"].str.contains(r"\|").sum() == 0
    assert (
        template("combined", icd_version="icd9_10")["Disease classification system"]
        == "ICD-9-CM and ICD-10"
    )


def test_returns_four_tables():
    result = comorbidity_reporting("charlson")
    assert isinstance(result, tuple) and len(result) == 4


def test_invalid_input():
    with pytest.raises(AssertionError):
        comorbidity_reporting("charlson", data_source="x")
    with pytest.raises(AssertionError):
        comorbidity_reporting("combined", "quan")
    with pytest.raises(AssertionError):
        comorbidity_reporting("nope")


@pytest.mark.parametrize(
    "score, implementation, weights, score_col",
    [
        ("charlson", "quan", "quan", "Charlson Comorbidity Index"),
        ("charlson", "sokolowski", "charlson", "Charlson Comorbidity Index"),
        ("charlson", "deyo", "charlson", "Charlson Comorbidity Index"),
        ("elixhauser", "quan", "van_walraven", "Elixhauser Comorbidity Index"),
        ("elixhauser", "ahrq_icd10", "ahrq", "Elixhauser Comorbidity Index"),
    ],
)
def test_reporting_reproduces_score(
    tmp_path, score, implementation, weights, score_col
):
    _, _, reported_codes, _ = comorbidity_reporting(
        score, implementation, weights, path=tmp_path
    )
    codes = reported_codes.group_by("category").first().sort("category")
    df = pl.DataFrame(
        {
            "id": range(codes.height),
            "code": codes["code"],
            "age": 65,
            "year": 2020,
        }
    ).vstack(
        pl.DataFrame(
            {
                "id": [-1, -1],
                "code": reported_codes["code"].head(2),
                "age": 65,
                "year": 2020,
            }
        )
    )
    expected = comorbidity(
        score,
        df,
        implementation=implementation,
        weights=weights,
        return_categories=True,
    )
    result = comorbidity(
        "custom",
        df,
        score_col_name=score_col,
        return_categories=True,
        **read_reporting(tmp_path),
    )
    assert result.sort("id").equals(expected.select(result.columns).sort("id"))


def test_read_reporting_rejects_bad_directories(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_reporting(tmp_path)
    comorbidity_reporting("hfrs", path=tmp_path)
    pl.read_csv(tmp_path / "weights.csv").head(1).write_csv(tmp_path / "weights.csv")
    with pytest.raises(ValueError):
        read_reporting(tmp_path)


def test_read_reporting_rejects_unknown_icd_version(tmp_path):
    comorbidity_reporting("hfrs", path=tmp_path)
    codes = pl.read_csv(tmp_path / "codes.csv")
    codes.with_columns(icd_version=pl.lit("ICD-11")).write_csv(tmp_path / "codes.csv")
    with pytest.raises(ValueError, match="icd_version"):
        read_reporting(tmp_path)


def test_software_version(monkeypatch):
    assert template("hfrs")["Software"].startswith("pycomorb ")
    monkeypatch.setitem(sys.modules, "pycomorb._version", None)  # as without a build
    assert template("hfrs")["Software"] == "pycomorb (version unknown)"


def test_invalid_icd_version():
    with pytest.raises(AssertionError):
        comorbidity_reporting("charlson", icd_version="icd11")
