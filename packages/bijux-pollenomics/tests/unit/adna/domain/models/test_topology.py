"""Topology contracts for aDNA scientific domain models."""

from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.adna.domain import models


def test_models_are_grouped_by_durable_scientific_responsibility() -> None:
    package_root = Path(models.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "chronology.py",
        "evidence.py",
        "identity.py",
        "localities.py",
        "samples.py",
        "vocabularies.py",
    }


def test_model_modules_are_valid_and_bounded() -> None:
    package_root = Path(models.__file__).parent
    for module in package_root.glob("*.py"):
        source = module.read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 220, module.name
        ast.parse(source, filename=str(module))
