"""Keep constructed normalized-lake metadata from authorizing a ranked registry."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry import (
    svar,
)


def report() -> dict[str, Any]:
    """Construct the finite metadata contract without any source file or geometry."""
    return {
        "schema_version": "svar-normalized-export-custody.v1",
        "export_generated_on": "2026-09-08",
        "export_lake_count_claim": 40565,
        "review_source_lake_count_claim": 40523,
        "review_subset_feature_count": 99,
        "current_ranked_candidate_count": 0,
        "source_population_reconciled": False,
        "raw_wfs_capture_bound_to_export": False,
        "qualified_review_accepted": False,
        "ranking_admitted": False,
        "inputs": ["constructed-" + str(i) for i in range(6)],
    }


def test_metadata_only_source_contract_accepts_its_literal_refusal() -> None:
    svar.validate_report(report())


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("export_lake_count_claim", 40565.0),
        ("review_source_lake_count_claim", 40565),
        ("review_subset_feature_count", 100),
        ("current_ranked_candidate_count", False),
        ("source_population_reconciled", True),
        ("raw_wfs_capture_bound_to_export", True),
        ("qualified_review_accepted", True),
        ("ranking_admitted", True),
        ("export_generated_on", "2026-09-09"),
        ("inputs", ["short"]),
    ],
)
def test_count_identity_or_ranking_inflation_refuses(key: str, value: Any) -> None:
    value_report = report()
    value_report[key] = value
    with pytest.raises(ReportRebuildError):
        svar.validate_report(value_report)
