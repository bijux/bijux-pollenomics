"""Paper-level aggregation of project sample-yield recovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_paper_yield_review(output_root: Path, *, surface: Any) -> dict[str, Any]:
    project_rows = surface.build_project_expected_sample_yield_review(output_root)[
        "rows"
    ]
    paper_rows = {
        row.paper_doi: row for row in surface.build_paper_registry(output_root)
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in project_rows:
        paper_doi = str(row.get("paper_doi") or "").strip()
        if not paper_doi:
            continue
        grouped.setdefault(paper_doi, []).append(row)

    rows: list[dict[str, Any]] = []
    for paper_doi, items in sorted(grouped.items()):
        paper_row = paper_rows.get(paper_doi)
        rows.append(
            {
                "paper_doi": paper_doi,
                "paper_title": "" if paper_row is None else paper_row.title,
                "project_accessions": sorted(
                    str(item["project_accession"]) for item in items
                ),
                "sample_extractability": (
                    "unknown" if paper_row is None else paper_row.sample_extractability
                ),
                "article_download_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.article_download_status
                ),
                "supplementary_download_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.supplementary_download_status
                ),
                "supplement_parse_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.supplement_parse_status
                ),
                "recovered_final_sample_count": sum(
                    surface._int_value(item["final_sample_count"]) for item in items
                ),
                "exact_expected_sample_count_total": sum(
                    surface._int_value(item["expected_sample_count"])
                    for item in items
                    if item["expected_sample_count"] is not None
                ),
                "projects_with_unknown_expected_total": sum(
                    1 for item in items if item["expected_sample_count"] is None
                ),
                "projects_with_implausibly_low_recovery": sum(
                    1 for item in items if bool(item["implausibly_low_recovery"])
                ),
                "yield_recovery_posture": surface._paper_yield_recovery_posture(items),
                "expected_contribution_surfaces": sorted(
                    {
                        contribution_surface
                        for item in items
                        for contribution_surface in item[
                            "expected_contribution_surfaces"
                        ]
                    }
                ),
            }
        )
    return {
        "schema_version": "animal-paper-expected-sample-yield-review.v1",
        "row_count": len(rows),
        "counts": {
            "paper_rows_with_implausibly_low_recovery": sum(
                1
                for row in rows
                if surface._int_value(row["projects_with_implausibly_low_recovery"]) > 0
            ),
            "paper_rows_with_unknown_expected_totals": sum(
                1
                for row in rows
                if surface._int_value(row["projects_with_unknown_expected_total"]) > 0
            ),
        },
        "rows": rows,
    }
