"""Topology contracts for LandClim temporal-grid modules."""

from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.collection.sources.landclim import time_windows


def test_package_is_grouped_by_source_and_scientific_responsibility() -> None:
    package_root = Path(time_windows.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "features.py",
        "landclim_i.py",
        "landclim_ii.py",
        "marquer.py",
        "values.py",
    }


def test_time_window_modules_are_valid_and_bounded() -> None:
    package_root = Path(time_windows.__file__).parent
    for module in package_root.glob("*.py"):
        source = module.read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 220, module.name
        ast.parse(source, filename=str(module))
