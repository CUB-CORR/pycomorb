# Development

```bash
git clone https://github.com/CUB-CORR/pycomorb
cd pycomorb
pip install -e ".[test]"
pytest                     # 100 % coverage required (pyproject.toml)
```

The definition and weight files live in `common/` and are copied into the package at build time (see `_build_backend.py`). `common/README.md` documents where each file comes from.

## Documentation

```bash
pip install -e ".[docs]"
zensical serve             # live preview at http://127.0.0.1:8000
zensical build --clean     # as in CI
```

The API page is generated from the Google-style docstrings; everything else is in `docs/`. Pushes to `main` deploy the site to GitHub Pages.

## Changes

Release notes: [GitHub releases](https://github.com/CUB-CORR/pycomorb/releases). Versions follow `1.YYYYMMDD.N` and are derived from git tags.

## Citation

Please cite the software via [CITATION.cff](https://github.com/CUB-CORR/pycomorb/blob/main/CITATION.cff) (Zenodo DOI [10.5281/zenodo.23436346](https://doi.org/10.5281/zenodo.23436346)) and the original publication of each variant you use ([References](references.md)).
