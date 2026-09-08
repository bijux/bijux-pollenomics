"""Compatibility coverage for the decomposed boundary-review package."""

from __future__ import annotations

import importlib


def test_package_preserves_the_documented_public_surface() -> None:
    review = importlib.import_module(
        "bijux_pollenomics.collection.sources.boundaries.review"
    )

    assert review.__all__ == [
        "BoundaryCountryReviewReport",
        "PointEvidence",
        "build_point_country_decision",
        "materialize_boundary_country_review",
    ]
    assert review.BoundaryCountryReviewReport.__name__ == (
        "BoundaryCountryReviewReport"
    )
    assert review.PointEvidence.__name__ == "PointEvidence"
    assert callable(review.build_point_country_decision)
    assert callable(review.materialize_boundary_country_review)


def test_package_preserves_existing_private_imports() -> None:
    review = importlib.import_module(
        "bijux_pollenomics.collection.sources.boundaries.review"
    )

    assert review.BoundaryAuthority.__name__ == "BoundaryAuthority"
    assert callable(review._build_boundary_review)
    assert callable(review._decision_summary)
    assert callable(review._validate_country_geometry)
