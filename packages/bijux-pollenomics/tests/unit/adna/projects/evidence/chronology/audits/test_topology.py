"""Intent-ownership constraints for chronology audits."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.projects.evidence.chronology import audits


def test_audits_are_grouped_by_durable_evidence_responsibility() -> None:
    package_root = Path(audits.__file__).parent
    files = tuple(package_root.glob("*.py"))

    assert {path.name for path in files} == {
        "__init__.py",
        "completeness.py",
        "counting.py",
        "precision.py",
        "provenance.py",
        "review.py",
        "summary.py",
    }
    assert len(files) <= 10


def test_direct_modules_remain_bounded() -> None:
    package_root = Path(audits.__file__).parent
    line_counts = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
    }

    assert max(line_counts.values()) <= 220, line_counts
