from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.collection.sources.landclim import collection


EXPECTED_MODULES = {
    "__init__.py",
    "archive_identity.py",
    "archive_validation.py",
    "asset_identity.py",
    "authority.py",
    "dataset_authority.py",
    "model.py",
    "raw_receipt.py",
    "receipt_publication.py",
    "receipt_structure.py",
    "surface_summary.py",
    "surfaces.py",
}


def test_collection_is_an_intent_owned_bounded_package() -> None:
    package_root = Path(collection.__file__).parent

    assert {path.name for path in package_root.glob("*.py")} == EXPECTED_MODULES
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )


def test_facade_owns_only_compatibility_workflows() -> None:
    module = ast.parse(Path(collection.__file__).read_text(encoding="utf-8"))
    function_names = {
        node.name for node in module.body if isinstance(node, ast.FunctionDef)
    }

    assert function_names == {
        "_build_landclim_archive_receipt",
        "_build_landclim_raw_receipt",
        "_object_rows",
        "_safe_receipt_filename",
        "_validate_landclim_receipt_datasets",
        "collect_landclim_data",
        "download_landclim_raw_assets",
        "materialize_landclim_repository_surfaces",
        "resolve_landclim_asset_urls",
        "validate_landclim_raw_receipt",
    }
