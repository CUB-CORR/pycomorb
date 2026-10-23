# Reporting of comorbidity scores: everything needed to reproduce a score is written to a report.

from importlib import import_module
from pathlib import Path

import polars as pl

from .CustomComorbidityIndex import weighted_definitions

# The package attributes of the same names are the score functions, not the modules
charlson = import_module(".CharlsonComorbidityIndex", __package__)
elixhauser = import_module(".ElixhauserComorbidityIndex", __package__)

NHS = "NHS Digital SHMI specification v1.60 (June 2026)"
AGE_POINTS = "Age points: 0 (<50 years), 1 (50-59), 2 (60-69), 3 (70-79), 4 (>=80)"

# ICD version -> the code systems it covers; each has a column of codes in the definitions
ICD_PARTS = {
    "icd9": ["ICD-9-CM"],
    "icd10": ["ICD-10"],
    "icd9_10": ["ICD-9-CM", "ICD-10"],
}
ICD_BY_PARTS = {frozenset(parts): version for version, parts in ICD_PARTS.items()}
CODE_COLUMNS = {"ICD-9-CM": "icd9_codes", "ICD-10": "icd10_codes"}

# Report domains: those that depend on the study data (unknown to the score), and all in order
STUDY_INFO = {
    "data_sources": "Data source(s)",
    "method_of_data_extraction": "Method of data extraction",
    "coding_practice": "Coding practice",
    "look_back_period": "Look-back period",
    "timing_of_data_extraction": "Timing of data extraction",
}
REPORT_DOMAINS = [
    "Data source(s)",
    "Method of data extraction",
    "Comorbidity weighting reference",
    "Comorbidity weighting list",
    "Disease classification system",
    "Disease code reference",
    "Disease code list",
    "Coding practice",
    "Age adjustment",
    "Hierarchy rules",
    "Look-back period",
    "Timing of data extraction",
    "Software",
]

# What the report needs to know about each score. Scores with one definition and one weighting
# (Combined, HFRS) are entries like the others, with ``None`` as their only implementation and weights.
#   files: implementation -> definition file
#   prefix: Weights/aliases files shared by the implementations; None if the definition file holds the weights
#   rules: Hierarchy rules in canonical category names, translated to the implementation's own names
#   code_refs / weight_refs: implementation / weights -> reference
#   default: (implementation, weights) used when none are given
#   icd_version: Implementations that only have one ICD version
#   own_weights: Implementations that always use their own weights
#   weight_col: Column holding the weights; weight_cols: the same for weights where it differs
#   age: weights -> description of the age adjustment; None is used for all weights not listed
SCORES = {
    "charlson": {
        "files": charlson.DEFINITION_FILES,
        "prefix": "CHARLSON",
        "rules": charlson.CANONICAL_RULES,
        "code_refs": {
            "quan": "Quan et al. (2005)",
            "deyo": "Deyo et al. (1992)",
            "romano": "Romano et al. (1993)",
            "dhoore": "D'Hoore et al. (1996)",
            "australia": "Sundararajan et al. (2004)",
            "sweden": "Ludvigsson et al. (2021)",
            "rcs": "Armitage and van der Meulen (2010)",
            "uk_shmi": NHS,
            "sokolowski": "Sokołowski et al. (2026)",
            "thygesen": "Thygesen et al. (2011)",
        },
        "weight_refs": {
            "charlson": "Charlson et al. (1987)",
            "schneeweiss": "Schneeweiss et al. (2003)",
            "quan": "Quan et al. (2011)",
            "rcs": "Armitage and van der Meulen (2010)",
            "uk_shmi": NHS,
        },
        "default": ("quan", "charlson"),
        "icd_version": {
            **dict.fromkeys(charlson.ICD9_ONLY, "icd9"),
            **dict.fromkeys(charlson.ICD10_ONLY, "icd10"),
        },
        "own_weights": {"rcs": "rcs", "uk_shmi": "uk_shmi"},
        "weight_col": "{weights}_weights",
        "weight_cols": {},
        "age": {None: AGE_POINTS, "rcs": "Not applied"},
    },
    "elixhauser": {
        "files": elixhauser.DEFINITION_FILES,
        "prefix": "ELIXHAUSER",
        "rules": elixhauser.CANONICAL_RULES,
        "code_refs": {
            "quan": "Quan et al. (2005)",
            "elixhauser": "Elixhauser et al. (1998)",
            "ahrq_icd9": "AHRQ Elixhauser Comorbidity Software v3.7 (ICD-9-CM)",
            "ahrq_icd10": "AHRQ Elixhauser Comorbidity Software Refined for ICD-10-CM v2026.1",
        },
        "weight_refs": {
            "van_walraven": "van Walraven et al. (2009)",
            "thompson_30": "Thompson et al. (2015)",
            "thompson_29": "Thompson et al. (2015)",
            "ahrq": "Moore et al. (2017)",
            "swiss": "Sharma et al. (2021)",
        },
        "default": ("quan", "van_walraven"),
        "icd_version": {
            **dict.fromkeys(elixhauser.ICD9_ONLY, "icd9"),
            **dict.fromkeys(elixhauser.ICD10_ONLY, "icd10"),
        },
        "own_weights": {"ahrq_icd9": "ahrq", "ahrq_icd10": "ahrq"},
        "weight_col": "{weights}_weights",
        # The AHRQ weights come in an ICD-9 and an ICD-10 column
        "weight_cols": {"ahrq": "ahrq_{icd_version}_weights"},
        "age": {None: "Not applicable"},
    },
    "combined": {
        "files": {None: "GAGNE.csv"},
        "prefix": None,
        "code_refs": {
            None: "Romano et al. (1993) and Quan et al. (2005) for ICD-9-CM; Sun et al. (2017) for ICD-10-CM"
        },
        "weight_refs": {None: "Gagne et al. (2011)"},
        "default": (None, None),
        "icd_version": {},
        "own_weights": {},
        "weight_col": "weights",
        "weight_cols": {},
        "age": {None: "Not applicable"},
    },
    "hfrs": {
        "files": {None: "HFRS.csv"},
        "prefix": None,
        "code_refs": {None: "Gilbert et al. (2018)"},
        "weight_refs": {None: "Gilbert et al. (2018)"},
        "default": (None, None),
        "icd_version": {None: "icd10"},
        "own_weights": {},
        "weight_col": "weight",
        "weight_cols": {},
        "age": {None: "Not applicable"},
    },
}


def score_setup(score, implementation, weights, icd_version):
    """Definitions, hierarchy rules and references of a score, with the defaults and overrides of the score functions."""

    # Input validation
    spec = SCORES[score]
    implementation = implementation or spec["default"][0]
    weights = weights or spec["default"][1]
    assert implementation in spec["files"], f"implementation must be one of: {list(spec['files'])}."  # fmt: skip
    assert weights in spec["weight_refs"], f"weights must be one of: {list(spec['weight_refs'])}."  # fmt: skip
    weights = spec["own_weights"].get(implementation, weights)
    icd_version = spec["icd_version"].get(implementation, icd_version)

    # Load definitions
    file = spec["files"][implementation]
    if spec["prefix"]:
        definitions, rules = weighted_definitions(
            spec["prefix"], file, implementation, spec["rules"]
        )
    else:
        definitions = pl.read_csv(Path(__file__).parent / "common" / file)
        rules = []

    weight_col = spec["weight_cols"].get(weights, spec["weight_col"])

    return {
        # The Charlson age row only holds placeholders
        "definitions": definitions.filter(pl.col("category") != "Age"),
        "weight_col": weight_col.format(weights=weights, icd_version=icd_version),
        "rules": rules,
        "icd_version": icd_version,
        "code_ref": spec["code_refs"][implementation],
        "weight_ref": spec["weight_refs"][weights],
        "age": spec["age"].get(weights, spec["age"][None]),
    }


def software_version():
    try:
        from ._version import __version__
    except ImportError:  # Source tree without a build
        return "pycomorb (version unknown)"
    return f"pycomorb {__version__}"


def report_tables(setup):
    """Weights, codes and hierarchy tables of a score setup."""

    # Tie each weight and code to its definition row (needed for and_group)
    definitions = setup["definitions"].with_row_index("row")
    extra_cols = [c for c in ("year", "and_group") if c in definitions.columns]
    weights = definitions.select(
        "row", "category", pl.col(setup["weight_col"]).alias("weight")
    )
    codes = pl.concat(
        definitions.select(
            "row",
            "category",
            *extra_cols,
            pl.lit(label).alias("icd_version"),
            pl.col(CODE_COLUMNS[label]).str.split("|").alias("code"),
        )
        .drop_nulls("code")
        .explode("code")
        for label in ICD_PARTS[setup["icd_version"]]
    )
    hierarchy = pl.DataFrame(setup["rules"], schema=["severe", "mild"], orient="row")
    return {"weights": weights, "codes": codes, "hierarchy": hierarchy}


def report_template(setup, icd_modification, study_info):
    """Template of the report; the domains about the study data are left to the user."""

    classification = " and ".join(ICD_PARTS[setup["icd_version"]])
    if icd_modification:
        classification += f", mapped with {icd_modification}"
    hierarchy = "; ".join(
        f"'{severe}' replaces '{mild}'" for severe, mild in setup["rules"]
    )

    answers = {name: str(study_info.get(key, "")) for key, name in STUDY_INFO.items()}
    answers |= {
        "Comorbidity weighting reference": setup["weight_ref"],
        "Comorbidity weighting list": "weights.csv",
        "Disease classification system": classification,
        "Disease code reference": setup["code_ref"],
        "Disease code list": "codes.csv",
        "Age adjustment": setup["age"],
        "Hierarchy rules": hierarchy or "Not applied",
        "Software": software_version(),
    }
    return pl.DataFrame(
        {"domain": REPORT_DOMAINS, "information": [answers[d] for d in REPORT_DOMAINS]}
    )


def markdown_table(table):
    """Format a DataFrame as a markdown table with one line per row."""

    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(table.columns) + " |",
        "|" + "---|" * len(table.columns),
        *("| " + " | ".join(cell(v) for v in row) + " |" for row in table.rows()),
    ]
    return "\n".join(lines) + "\n"


def comorbidity_reporting(
    score: str,
    implementation: str | None = None,
    weights: str | None = None,
    icd_version: str = "icd10",
    icd_modification: str | None = None,
    path: Path | str | None = None,
    **study_info: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """Reporting template for a comorbidity score, with the information needed to reproduce it.

    Args:
        score (str): ``"charlson"``, ``"elixhauser"``, ``"combined"`` or ``"hfrs"``.
        implementation (str, optional): As in the score function. Defaults to its default (none for ``"combined"`` and ``"hfrs"``).
        weights (str, optional): As in the score function. Defaults to its default (none for ``"combined"`` and ``"hfrs"``).
        icd_version (str, optional): ICD version of the data; replaced by the one the implementation uses if it supports a single version only. Defaults to ``"icd10"``.
        icd_modification (str, optional): ICD modification, e.g. ``"icd10gm"``, if the codes were mapped to a target year first. Defaults to ``None``.
        path (Path | str, optional): Directory to write the tables to, as ``template.md`` (a markdown table), ``weights.csv``, ``codes.csv`` and ``hierarchy.csv``. Defaults to ``None`` (nothing is written).
        **study_info (str): Answers for the domains that depend on the study data: ``data_sources``, ``method_of_data_extraction``, ``coding_practice``, ``look_back_period`` and ``timing_of_data_extraction``. Unanswered domains are left empty.

    Returns:
        tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]: ``template`` (domain, information), ``weights`` (row, category, weight), ``codes`` (row, category, icd_version, code; one row per ICD code) and ``hierarchy`` (severe, mild). ``row`` is the definition row a weight and its codes belong to.

    Raises:
        AssertionError: If ``score``, ``implementation``, ``weights``, ``icd_version`` or a ``study_info`` key is not supported.
    """

    # Input validation
    assert score in SCORES, f"score must be one of: {list(SCORES)}."  # fmt: skip
    assert icd_version in ICD_PARTS, f"icd_version must be one of: {list(ICD_PARTS)}."  # fmt: skip
    assert study_info.keys() <= STUDY_INFO.keys(), f"study_info keys must be among: {list(STUDY_INFO)}."  # fmt: skip

    # STEP 1: Collect what is needed to reproduce the score
    setup = score_setup(score, implementation, weights, icd_version)

    # STEP 2: Build the template and the tables
    tables = {
        "template": report_template(setup, icd_modification, study_info),
        **report_tables(setup),
    }

    # STEP 3: Write the files
    if path is not None:
        Path(path).mkdir(parents=True, exist_ok=True)
        for name, table in tables.items():
            if name == "template":
                (Path(path) / "template.md").write_text(markdown_table(table), encoding="utf-8")  # fmt: skip
            else:
                table.write_csv(Path(path) / f"{name}.csv")
    return tuple(tables.values())


def read_reporting(path: Path | str) -> dict:
    """Read the tables written by ``comorbidity_reporting`` back in.

    The result holds the arguments of a custom score that reproduces the reported one::

        comorbidity("custom", df, **read_reporting(path))

    ``icd_version`` is the one the report used, so do not pass it again; ``icd_version_col`` is still needed for ``"icd9_10"``.
    Records need a year column (``year_col``, default ``"year"``) if the codes have a ``year``.

    Returns:
        dict: ``icd_version``, ``definition_data``, ``weight_col_name`` and ``mutual_exclusion_rules``.

    Raises:
        FileNotFoundError: If one of the tables is missing in ``path``.
        ValueError: If the tables do not belong together.
    """

    # Input validation
    path = Path(path)
    for name in ("weights", "codes", "hierarchy"):
        if not (path / f"{name}.csv").is_file():
            raise FileNotFoundError(f"'{name}.csv' not found in '{path}'.")

    # Load the tables; codes stay strings (e.g. ICD-9 "0010" is not a number)
    weights = pl.read_csv(path / "weights.csv")
    rules = pl.read_csv(path / "hierarchy.csv")
    codes = pl.read_csv(
        path / "codes.csv",
        schema_overrides={"code": pl.String, "and_group": pl.String},
    )
    if not set(codes["row"]) <= set(weights["row"]):
        raise ValueError("codes.csv has rows that are not in weights.csv.")
    icd_version = ICD_BY_PARTS.get(frozenset(codes["icd_version"]))
    if icd_version is None:
        raise ValueError(f"icd_version in codes.csv must be among: {list(CODE_COLUMNS)}.")  # fmt: skip

    # Rebuild the definitions. One definition row per code row: its codes joined by "|", one column per ICD version
    code_lists = (
        codes.group_by("row", "icd_version", maintain_order=True)
        .agg(pl.col("code").str.join("|"))
        .pivot(on="icd_version", index="row", values="code")
        .rename(CODE_COLUMNS, strict=False)
    )
    definitions = (
        codes.drop("icd_version", "code")
        .unique("row", maintain_order=True)
        .join(code_lists, on="row")
        .join(weights.select("row", "weight"), on="row")
        .drop("row")
    )

    return {
        "icd_version": icd_version,
        "definition_data": definitions,
        "weight_col_name": "weight",
        "mutual_exclusion_rules": rules.rows(),
    }
