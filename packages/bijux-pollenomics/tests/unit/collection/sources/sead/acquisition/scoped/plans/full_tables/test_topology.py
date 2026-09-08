"""Topology contracts for the full-evidence plan package."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans import (
    full_tables,
)


def test_package_is_split_by_relational_responsibility() -> None:
    package_root = Path(full_tables.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "foundations.py",
        "lookup_relations.py",
        "observation_values.py",
        "required_relations.py",
        "semantic_dimensions.py",
        "stewardship.py",
        "taxonomy.py",
    }


def test_source_modules_remain_bounded() -> None:
    package_root = Path(full_tables.__file__).parent
    line_counts = {
        path.name: len(path.read_text().splitlines())
        for path in package_root.glob("*.py")
    }
    assert max(line_counts.values()) <= 220, line_counts
