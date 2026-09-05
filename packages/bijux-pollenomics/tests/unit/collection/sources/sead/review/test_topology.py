from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.collection.sources.sead import review


def test_review_modules_are_bounded_and_intent_owned() -> None:
    package_root = Path(review.__file__).parent
    modules = sorted(package_root.glob("*.py"))
    assert [module.name for module in modules] == [
        "__init__.py",
        "access.py",
        "inventory.py",
        "legibility.py",
        "publication.py",
        "recovery.py",
        "temporal.py",
    ]
    assert all(
        len(module.read_text(encoding="utf-8").splitlines()) <= 250
        for module in modules
    )


def test_review_modules_are_valid_python() -> None:
    package_root = Path(review.__file__).parent
    for module in package_root.glob("*.py"):
        ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
