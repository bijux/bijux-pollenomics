from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition import full


def test_full_acquisition_modules_are_bounded_and_intent_owned() -> None:
    package_root = Path(full.__file__).parent
    modules = sorted(package_root.glob("*.py"))
    assert [module.name for module in modules] == [
        "__init__.py",
        "model.py",
        "publication.py",
        "reconciliation.py",
        "retrieval.py",
        "serialization.py",
        "validation.py",
    ]
    assert all(
        len(module.read_text(encoding="utf-8").splitlines()) <= 250
        for module in modules
    )


def test_full_acquisition_modules_are_valid_python() -> None:
    package_root = Path(full.__file__).parent
    for module in package_root.glob("*.py"):
        ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
