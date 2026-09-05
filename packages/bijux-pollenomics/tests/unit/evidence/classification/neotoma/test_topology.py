"""Intent-ownership constraints for Neotoma classification accounting."""

from __future__ import annotations

from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT


_SOURCE_ROOT = (
    REPOSITORY_ROOT
    / "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma"
)


def test_neotoma_classification_is_an_intent_owned_package() -> None:
    assert _SOURCE_ROOT.is_dir()
    assert not _SOURCE_ROOT.with_suffix(".py").exists()
    assert {path.name for path in _python_files()} == {
        "__init__.py",
        "accounting.py",
        "concepts.py",
        "countries.py",
        "partitions.py",
        "rows.py",
    }


def test_source_modules_remain_bounded() -> None:
    line_counts = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in _python_files()
    }

    assert max(line_counts.values()) <= 220, line_counts


def _python_files() -> tuple[Path, ...]:
    return tuple(sorted(_SOURCE_ROOT.glob("*.py")))
