from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.collection.spatial import country_classification

EXPECTED_MODULES = {
    "__init__.py",
    "boundary_distance.py",
    "containment.py",
    "decision.py",
    "dependencies.py",
    "model.py",
    "partitions.py",
    "proximity.py",
    "validation.py",
}


def test_country_classification_is_a_bounded_intent_owned_package() -> None:
    package_root = Path(country_classification.__file__).parent

    assert {path.name for path in package_root.glob("*.py")} == EXPECTED_MODULES
    assert (
        max(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in package_root.glob("*.py")
        )
        <= 220
    )
