"""Ownership checks for animal-atlas evidence row modules."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.reporting.adna import atlas_evidence_rows

_OWNED_MODULES = frozenset(
    {
        "chronology.py",
        "coordinate_review.py",
        "localities.py",
        "models.py",
        "row_factory.py",
        "sample_support.py",
        "service.py",
        "source_records.py",
        "validation.py",
    }
)


def test_modules_have_bounded_intent_ownership() -> None:
    package_root = Path(atlas_evidence_rows.__file__).parent
    modules = {
        path.name: len(path.read_text(encoding="utf-8").splitlines())
        for path in package_root.glob("*.py")
        if path.name != "__init__.py"
    }

    assert frozenset(modules) == _OWNED_MODULES
    assert len(modules) <= 10
    assert max(modules.values()) <= 220
