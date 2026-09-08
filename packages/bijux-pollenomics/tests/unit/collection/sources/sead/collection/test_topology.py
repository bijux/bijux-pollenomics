from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.collection.sources.sead import collection


def test_collection_modules_are_bounded_and_intent_owned() -> None:
    package_root = Path(collection.__file__).parent
    modules = sorted(package_root.glob("*.py"))
    assert [module.name for module in modules] == [
        "__init__.py",
        "archive.py",
        "model.py",
        "publication.py",
        "repository.py",
        "repository_materialization.py",
        "retrieval.py",
        "validation.py",
    ]
    assert all(
        len(module.read_text(encoding="utf-8").splitlines()) <= 320
        for module in modules
    )


def test_collection_modules_are_valid_python() -> None:
    package_root = Path(collection.__file__).parent
    for module in package_root.glob("*.py"):
        ast.parse(module.read_text(encoding="utf-8"), filename=str(module))


def test_repository_surface_transaction_is_grouped_and_bounded() -> None:
    package_root = Path(collection.__file__).parent / "repository_surfaces"
    modules = sorted(package_root.glob("*.py"))
    assert [module.name for module in modules] == [
        "__init__.py",
        "contract.py",
        "identity.py",
        "transaction.py",
        "validation.py",
    ]
    assert all(
        len(module.read_text(encoding="utf-8").splitlines()) <= 220
        for module in modules
    )
