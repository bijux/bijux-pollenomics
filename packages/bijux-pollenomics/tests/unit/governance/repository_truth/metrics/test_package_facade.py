"""Verify the stable repository-metrics compatibility facade."""

from __future__ import annotations

from bijux_pollenomics.governance.repository_truth import metrics
from bijux_pollenomics.governance.repository_truth.metrics import (
    claims,
    counts,
    documentation,
    filesystem,
    rows,
)
from bijux_pollenomics.governance.repository_truth.metrics.documentation import (
    breadth,
    restoration,
)
from bijux_pollenomics.governance.repository_truth.metrics.rows import review, sources


def test_metrics_facade_preserves_private_compatibility_imports() -> None:
    owners = {
        "SCORE_MAX": claims,
        "_build_claim_freeze_reasons": claims,
        "_claim_check": claims,
        "_ratio_score": claims,
        "_build_core_counts": counts,
        "_docs_breadth_expectations": documentation,
        "_docs_restoration_expectations": documentation,
        "_docs_restoration_group": documentation,
        "_count_files": filesystem,
        "_count_geojson_features": filesystem,
        "_count_suffix_files": filesystem,
        "_count_tree_files": filesystem,
        "_format_metric_map": filesystem,
        "_load_json": filesystem,
        "_load_json_or_default": filesystem,
        "_artifact_review_row": rows,
        "_atlas_input_row": rows,
        "_build_source_explainer_audit_row": rows,
        "_cross_domain_matrix_row": rows,
        "_recovery_review_row": rows,
        "_source_family_row": rows,
    }

    assert metrics.__all__ == []
    for name, owner in owners.items():
        assert getattr(metrics, name) is getattr(owner, name)


def test_nested_facades_delegate_to_intent_owners() -> None:
    assert (
        documentation._docs_breadth_expectations is breadth._docs_breadth_expectations
    )
    assert (
        documentation._docs_restoration_expectations
        is restoration._docs_restoration_expectations
    )
    assert documentation._docs_restoration_group is restoration._docs_restoration_group
    assert rows._artifact_review_row is review._artifact_review_row
    assert rows._recovery_review_row is review._recovery_review_row
    assert rows._atlas_input_row is sources._atlas_input_row
    assert (
        rows._build_source_explainer_audit_row
        is sources._build_source_explainer_audit_row
    )
    assert rows._cross_domain_matrix_row is sources._cross_domain_matrix_row
    assert rows._source_family_row is sources._source_family_row
