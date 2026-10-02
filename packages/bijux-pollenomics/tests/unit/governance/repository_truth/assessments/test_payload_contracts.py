"""Repository truth renderers refuse malformed documentation and score payloads."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.governance.repository_truth import documentation, integrity
from bijux_pollenomics.governance.repository_truth.metrics import _build_core_counts
from tests.support.repository import REPOSITORY_ROOT


def test_docs_restoration_requires_integer_status_counts() -> None:
    with pytest.raises(ValueError, match="status counts"):
        documentation.render_repository_docs_restoration_ledger_markdown(
            {
                "rule": "retained",
                "row_count": 1,
                "status_counts": {"verified_replacement": True},
                "rows": [],
            }
        )


def test_docs_scope_requires_record_rows_and_text_lists() -> None:
    with pytest.raises(ValueError, match="rows"):
        documentation.render_repository_docs_scope_validation_markdown(
            {"rule": "retained", "overall_ok": False, "rows": "not rows"}
        )
    with pytest.raises(ValueError, match="missing_pages"):
        documentation.render_repository_docs_scope_validation_markdown(
            {
                "rule": "retained",
                "overall_ok": False,
                "rows": [
                    {
                        "display_name": "X",
                        "landing_path": "docs/x",
                        "required_page_count": 1,
                        "missing_pages": [1],
                        "missing_links": [],
                    }
                ],
            }
        )


def test_docs_scope_refuses_nontext_landing_path() -> None:
    with (
        patch.object(
            documentation,
            "_docs_breadth_expectations",
            return_value=[{"landing_path": 3}],
        ),
        pytest.raises(ValueError, match="landing_path"),
    ):
        documentation.build_repository_docs_scope_validation(
            data_root=REPOSITORY_ROOT / "data",
            docs_root=REPOSITORY_ROOT / "docs",
            report_root=REPOSITORY_ROOT / "docs" / "report",
        )


def test_integrity_refuses_boolean_score_count_and_nonrecord_rows() -> None:
    repo = Path(REPOSITORY_ROOT)
    counts = _build_core_counts(repo / "data", repo / "docs", repo / "docs" / "report")
    counts["papers_with_archived_supplements"] = True
    with (
        patch.object(integrity, "_build_core_counts", return_value=counts),
        pytest.raises(ValueError, match="papers_with_archived_supplements"),
    ):
        integrity.build_repository_recovery_review(
            data_root=repo / "data",
            docs_root=repo / "docs",
            report_root=repo / "docs" / "report",
        )
    with pytest.raises(ValueError, match="rows"):
        integrity.render_repository_governance_artifact_review_markdown(
            {"rows": ["not a row"]}
        )
