"""pytest wiring: make the mapping files available to the package and provide fixtures."""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# The package reads mapping files from pycomorb/common, which the build step copies from ./common.
# When running from a source checkout, link them instead of building.
_link = ROOT / "pycomorb" / "common"
if not _link.exists():
    os.symlink(ROOT / "common", _link)


@pytest.fixture(params=["polars", "pandas"])
def to_frame(request):
    """Convert a polars frame to the parametrized input type."""
    return (lambda d: d) if request.param == "polars" else (lambda d: d.to_pandas())
