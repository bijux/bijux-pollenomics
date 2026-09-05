from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.adna.projects.registry import sample_truth


EXPECTED_MODULES = {
    "__init__.py",
    "classification.py",
    "dependencies.py",
    "drift.py",
    "foundation.py",
    "markdown.py",
    "product_contract.py",
    "repository.py",
    "warnings.py",
}


def test_sample_truth_is_an_intent_owned_bounded_package() -> None:
    package_root = Path(sample_truth.__file__).parent

    assert {path.name for path in package_root.glob("*.py")} == EXPECTED_MODULES
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )


def test_facade_contains_only_compatibility_entry_points() -> None:
    module = ast.parse(Path(sample_truth.__file__).read_text(encoding="utf-8"))
    function_names = {
        node.name for node in module.body if isinstance(node, ast.FunctionDef)
    }

    assert set(EXPECTED_MODULES).isdisjoint(function_names)
    assert set(sample_truth.__all__).issubset(function_names)
    assert "_load_sample_rows" in function_names
    assert "_sample_truth_status" in function_names
