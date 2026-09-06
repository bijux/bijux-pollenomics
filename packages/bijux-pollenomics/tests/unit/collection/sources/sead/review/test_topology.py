from __future__ import annotations

import ast
from pathlib import Path

import pytest

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


def test_review_publication_validates_stable_site_identity_before_writes(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="site_uuid is missing"):
        review.write_sead_review_outputs(tmp_path, rows=[{"site_id": 1}], records=[])
    assert not (tmp_path / "review").exists()

    duplicate_rows = [
        {"site_id": 1, "site_uuid": "duplicate"},
        {"site_id": 2, "site_uuid": "duplicate"},
    ]
    with pytest.raises(ValueError, match="site_uuid is duplicated"):
        review.write_sead_review_outputs(
            tmp_path, rows=duplicate_rows, records=[]
        )
    assert not (tmp_path / "review").exists()
