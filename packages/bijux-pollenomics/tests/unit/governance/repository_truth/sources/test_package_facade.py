"""Verify the stable repository source-assessment facade."""

from __future__ import annotations

from bijux_pollenomics.governance.repository_truth import sources
from bijux_pollenomics.governance.repository_truth.sources import (
    acquisition,
    atlas_inputs,
    cross_domain,
    ecosystems,
    explainers,
    family_matrix,
    scientific_progress,
)


def test_sources_facade_exports_each_owned_assessment_pair() -> None:
    expected = [
        "build_repository_source_explainer_audit",
        "render_repository_source_explainer_audit_markdown",
        "build_repository_source_ecosystem_review",
        "render_repository_source_ecosystem_review_markdown",
        "build_repository_source_family_matrix",
        "render_repository_source_family_matrix_markdown",
        "build_repository_atlas_input_audit",
        "render_repository_atlas_input_audit_markdown",
        "build_repository_cross_domain_evidence_matrix",
        "render_repository_cross_domain_evidence_matrix_markdown",
        "build_repository_source_acquisition_queue",
        "render_repository_source_acquisition_queue_markdown",
        "build_repository_scientific_progress_audit",
        "render_repository_scientific_progress_audit_markdown",
    ]

    owners = (
        explainers,
        ecosystems,
        family_matrix,
        atlas_inputs,
        cross_domain,
        acquisition,
        scientific_progress,
    )
    assert sources.__all__ == expected
    assert [name for owner in owners for name in owner.__all__] == expected
    for owner in owners:
        for name in owner.__all__:
            assert getattr(sources, name) is getattr(owner, name)
