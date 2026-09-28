"""Public capability cells must keep support and file presence independent."""

from __future__ import annotations

from bijux_pollenomics_dev.source_completion.capability_publication import render


def test_publication_separates_partial_support_from_partial_files() -> None:
    report = {
        "source_count": 1,
        "dimension_count": 2,
        "audit_row_count": 2,
        "rows": [
            {
                "source_key": "example",
                "dimension": "identity",
                "support": "supported",
                "materialization": "partial",
                "present_evidence_paths": ["data/present.json"],
                "missing_evidence_paths": ["data/missing.json"],
                "human_review_required": True,
            },
            {
                "source_key": "example",
                "dimension": "time",
                "support": "partial",
                "materialization": "missing",
                "present_evidence_paths": [],
                "missing_evidence_paths": ["data/time.json"],
                "human_review_required": False,
            },
        ],
    }
    page = render(report, "abcd")
    assert "| example | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 |" in page
    assert "| example | identity | supported | partial | 1 | 1 | required |" in page
    assert "| example | time | partial | missing | 0 | 1 | not flagged |" in page
    assert "Review SHA-256: `abcd`" in page
