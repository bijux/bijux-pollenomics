"""Compatibility and topology guarantees for the scientific-review package."""

from __future__ import annotations

import ast
import inspect

from bijux_pollenomics.evidence import scientific_review
from tests.support.repository import REPOSITORY_ROOT

_PUBLIC_API = (
    "AnimalCoordinateVisibilityReview",
    "ChronologyOverlapRow",
    "EvidenceUncertaintyRow",
    "NordicScenarioAssessment",
    "ScientificReviewSurface",
    "SpeciesCountryCoverageRow",
    "SpeciesPeriodCoverageRow",
    "build_scientific_review_surface",
)
_LEGACY_PRIVATE_API = (
    "_build_chronology_overlaps",
    "_build_country_coverage",
    "_build_period_coverage",
    "_build_scenarios",
    "_build_uncertainties",
    "_context_point_interval",
    "_locality_interval",
    "_locality_overlaps_point",
    "_period_label_for",
    "_validated_interval",
)
_PACKAGE_ROOT = (
    REPOSITORY_ROOT
    / "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/scientific_review"
)


def test_facade_preserves_public_and_relied_on_private_imports() -> None:
    assert tuple(scientific_review.__all__) == _PUBLIC_API
    assert all(hasattr(scientific_review, name) for name in _PUBLIC_API)
    assert all(
        callable(getattr(scientific_review, name)) for name in _LEGACY_PRIVATE_API
    )


def test_surface_builder_preserves_the_legacy_signature() -> None:
    signature = inspect.signature(scientific_review.build_scientific_review_surface)
    assert tuple(signature.parameters) == (
        "countries",
        "human_localities",
        "animal_localities",
        "context_points",
        "animal_coordinate_review",
        "include_tracked_nonhuman_review",
    )
    assert signature.parameters["animal_localities"].default == ()
    assert signature.parameters["animal_coordinate_review"].default is None
    assert signature.parameters["include_tracked_nonhuman_review"].default is True


def test_each_legacy_definition_has_one_intent_owner() -> None:
    expected_owners = {
        "AnimalCoordinateVisibilityReview": "models.py",
        "SpeciesCountryCoverageRow": "models.py",
        "SpeciesPeriodCoverageRow": "models.py",
        "ChronologyOverlapRow": "models.py",
        "EvidenceUncertaintyRow": "models.py",
        "NordicScenarioAssessment": "models.py",
        "ScientificReviewSurface": "models.py",
        "build_scientific_review_surface": "surface.py",
        "_build_country_coverage": "country_coverage.py",
        "_build_period_coverage": "period_coverage.py",
        "_build_chronology_overlaps": "chronology.py",
        "_build_uncertainties": "uncertainty.py",
        "_build_scenarios": "scenarios.py",
        "_period_label_for": "temporal.py",
        "_locality_overlaps_point": "temporal.py",
        "_locality_interval": "temporal.py",
        "_context_point_interval": "temporal.py",
        "_validated_interval": "temporal.py",
    }
    owners: dict[str, list[str]] = {name: [] for name in expected_owners}
    for path in _PACKAGE_ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if (
                isinstance(node, (ast.ClassDef, ast.FunctionDef))
                and node.name in owners
            ):
                owners[node.name].append(path.name)
    assert owners == {name: [owner] for name, owner in expected_owners.items()}


def test_package_has_bounded_intent_modules() -> None:
    modules = sorted(path for path in _PACKAGE_ROOT.glob("*.py"))
    assert {path.stem for path in modules} == {
        "__init__",
        "chronology",
        "country_coverage",
        "models",
        "period_coverage",
        "scenarios",
        "surface",
        "temporal",
        "uncertainty",
    }
    assert (
        max(len(path.read_text(encoding="utf-8").splitlines()) for path in modules)
        <= 180
    )
