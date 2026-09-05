"""Recovery depth, missing-source queue, and release guard."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_progress(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface._project_recovery_rows(output_root)
    sample_depth_counts = surface._sample_evidence_depth_counts(output_root)
    return {
        "schema_version": "animal-source-recovery-progress.v1",
        "project_count": len(rows),
        "sample_evidence_depth_counts": sample_depth_counts,
        "project_counts": {
            "projects_with_sample_identity_rows": sum(
                1 for row in rows if surface._int_value(row["final_sample_count"]) > 0
            ),
            "projects_with_defensible_site_rows": sum(
                1
                for row in rows
                if surface._int_value(row["final_sample_count"]) > 0
                and surface._int_value(row["lacking_defensible_site_assignment_count"])
                == 0
            ),
            "projects_with_sample_owned_chronology": sum(
                1
                for row in rows
                if surface._int_value(row["final_sample_count"]) > 0
                and surface._int_value(row["missing_chronology_count"]) == 0
            ),
            "projects_with_mappable_coordinates": sum(
                1
                for row in rows
                if surface._int_value(row["mappable_coordinate_count"]) > 0
            ),
            "projects_ready_for_publication_review": sum(
                1
                for row in rows
                if str(row["publication_readiness_status"]) == "complete"
            ),
        },
        "rows": [
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "completed_stage_count": row["completed_stage_count"],
                "required_stage_count": row["required_stage_count"],
                "recovery_depth_score": row["recovery_depth_score"],
                "final_sample_count": row["final_sample_count"],
                "minimum_gap_count": row["minimum_gap_count"],
                "publication_readiness_status": row["publication_readiness_status"],
            }
            for row in rows
        ],
    }


def build_missing_queue(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface._project_recovery_rows(output_root)
    queued_rows = []
    for row in rows:
        category = surface._missing_source_queue_category(row)
        if category == "not_queued":
            continue
        queued_rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "paper_doi": row["paper_doi"],
                "queue_category": category,
                "expected_contributions": row["expected_contributions"],
                "expected_contribution_surfaces": row["expected_contribution_surfaces"],
                "current_capture_state": row["evidence_acquisition_state"],
                "queue_reason": surface._missing_source_queue_reason(category, row),
            }
        )
    return {
        "schema_version": "animal-missing-source-queue.v1",
        "row_count": len(queued_rows),
        "counts": surface._count_rows(queued_rows, key="queue_category"),
        "rows": queued_rows,
    }


def build_release_guard(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface.build_project_expected_sample_yield_review(output_root)["rows"]
    failing_projects = [
        {
            "project_accession": row["project_accession"],
            "species_latin_name": row["species_latin_name"],
            "recovery_gap_status": row["recovery_gap_status"],
            "implausibly_low_recovery_reason": row["implausibly_low_recovery_reason"],
        }
        for row in rows
        if bool(row["implausibly_low_recovery"])
    ]
    return {
        "schema_version": "animal-source-recovery-release-guard.v1",
        "passing": len(failing_projects) == 0,
        "implausibly_low_recovery_project_count": len(failing_projects),
        "failing_projects": failing_projects,
    }
