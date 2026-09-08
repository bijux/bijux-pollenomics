"""Intent-ownership constraints for the SEAD join-plan package."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.scoped.plans import joins


def test_join_plans_are_grouped_by_relational_responsibility() -> None:
    package_root = Path(joins.__file__).parent
    files = tuple(package_root.glob("*.py"))

    assert {path.name for path in files} == {
        "__init__.py",
        "datasets.py",
        "measurements.py",
        "taxonomy.py",
        "values.py",
    }
    assert len(files) <= 10


def test_direct_modules_remain_bounded() -> None:
    package_root = Path(joins.__file__).parent
    line_counts = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert max(line_counts.values()) <= 220, line_counts
