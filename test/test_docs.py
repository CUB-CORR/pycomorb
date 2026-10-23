"""The documentation lists every option and its code examples run."""

import inspect
import re

import polars as pl
import pytest
from helpers import CHARLSON_FILES, CHARLSON_WEIGHTS, ELIXHAUSER_FILES, ELIXHAUSER_WEIGHTS, ROOT

import pycomorb as pc

DOCS = ROOT / "docs"
pytestmark = pytest.mark.skipif(not DOCS.is_dir(), reason="docs/ is not part of the installed package")

# Example data the page snippets build on, unless they define their own
EXAMPLE = {
    "df": pl.DataFrame(
        {"id": [1, 1, 2], "code": ["I21", "E119", "C349"], "age": [66, 66, 81], "year": [2012, 2012, 2010]}
    )
}


def test_scores_page_lists_every_option_and_default():
    page = (DOCS / "scores.md").read_text(encoding="utf-8")
    for options in (CHARLSON_FILES, ELIXHAUSER_FILES, CHARLSON_WEIGHTS, ELIXHAUSER_WEIGHTS):
        for option in options:
            assert f"`{option}`" in page, f"{option} is not documented in docs/scores.md"
    for score in (pc.CharlsonComorbidityIndex, pc.ElixhauserComorbidityIndex):
        for argument in ("implementation", "weights"):
            default = inspect.signature(score).parameters[argument].default
            assert f"`{default}` (default)" in page, f"default {argument} {default} is not marked in docs/scores.md"


@pytest.mark.parametrize("page", sorted(DOCS.glob("*.md")), ids=lambda p: p.name)
def test_page_examples_run(page, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # examples may write files
    namespace = dict(EXAMPLE)
    for block in re.findall(r"```python\n(.*?)```", page.read_text(encoding="utf-8"), flags=re.S):
        exec(compile(block, page.name, "exec"), namespace)


def _dois(text):
    return {doi.rstrip(".,") for doi in re.findall(r"10\.\d{4,}/[^\s)\]]+", text)}


def test_references_match_common_readme():
    """docs/references.md repeats the citations of common/README.md: same DOIs, same authors, title, journal and PMID."""
    common = (ROOT / "common" / "README.md").read_text(encoding="utf-8")
    references = (DOCS / "references.md").read_text(encoding="utf-8")
    assert _dois(common) == _dois(references)

    for entry in re.findall(r"^<a id=.*10\.\d{4,}/.*$", references, flags=re.M):  # NHS and AHRQ have no DOI
        source = next(line for line in common.splitlines() if next(iter(_dois(entry))) in line)
        body = re.sub(r"^.*?\*\*[^*]+\*\*[^:]*: ", "", entry).split(" doi:")[0].split(" Erratum")[0].replace("*", "")
        for part in body.split(". "):
            assert re.search(r"\d{4};", part) or part in source, f"'{part}' differs from common/README.md"
        assert re.search(r"PMID: \d+", entry).group() in source
