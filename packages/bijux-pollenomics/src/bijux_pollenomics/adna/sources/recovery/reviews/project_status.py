"""Project stage, yield, and species-deficit accounting."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def build_stage_review(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface._project_recovery_rows(output_root)
    summary = {
        "complete_projects": 0,
        "blocked_projects": 0,
        "in_progress_projects": 0,
        "ready_for_publication_review": 0,
    }
    stage_totals = {
        stage: {"complete": 0, "blocked": 0, "in_progress": 0, "not_required": 0}
        for stage in surface.ADNA_INTAKE_STAGE_KEYS
    }
    for row in rows:
        overall = str(row["overall_recovery_status"])
        if overall in summary:
            summary[overall] += 1
        for stage, status in row["stage_statuses"].items():
            stage_totals[str(stage)][str(status)] += 1
    return {
        "schema_version": "animal-project-recovery-stage-review.v1",
        "row_count": len(rows),
        "summary": summary,
        "stage_totals": stage_totals,
        "rows": rows,
    }


def build_expected_yield_review(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface._project_recovery_rows(output_root)
    exact_expected_total = sum(
        surface._int_value(row["expected_sample_count"])
        for row in rows
        if row["expected_sample_count"] is not None
    )
    recovered_total = sum(surface._int_value(row["final_sample_count"]) for row in rows)
    minimum_gap_total = sum(
        surface._int_value(row["minimum_gap_count"] or 0) for row in rows
    )
    implausibly_low_rows = [
        row for row in rows if bool(row["implausibly_low_recovery"])
    ]
    return {
        "schema_version": "animal-project-expected-sample-yield-review.v1",
        "row_count": len(rows),
        "counts": {
            "tracked_project_count": len(rows),
            "projects_with_exact_expected_count": sum(
                1 for row in rows if row["expected_sample_count"] is not None
            ),
            "projects_with_minimum_expected_floor": sum(
                1 for row in rows if row["minimum_expected_sample_count"] is not None
            ),
            "projects_with_implausibly_low_recovery": len(implausibly_low_rows),
            "exact_expected_sample_total": exact_expected_total,
            "recovered_final_sample_total": recovered_total,
            "minimum_gap_total": minimum_gap_total,
        },
        "rows": rows,
    }


def build_species_deficit_ledger(output_root: Path, *, surface: Any) -> dict[str, Any]:
    rows = surface._project_recovery_rows(output_root)
    species_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        species = str(row["species_latin_name"])
        counts = species_counts.setdefault(
            species,
            {
                "project_count": 0,
                "projects_with_sample_gap": 0,
                "projects_with_site_gap": 0,
                "projects_with_chronology_gap": 0,
                "projects_blocked_before_publication": 0,
            },
        )
        counts["project_count"] += 1
        if surface._int_value(row["minimum_gap_count"] or 0) > 0:
            counts["projects_with_sample_gap"] += 1
        if surface._int_value(row["lacking_defensible_site_assignment_count"]) > 0:
            counts["projects_with_site_gap"] += 1
        if surface._int_value(row["missing_chronology_count"]) > 0:
            counts["projects_with_chronology_gap"] += 1
        if str(row["publication_readiness_status"]) != "complete":
            counts["projects_blocked_before_publication"] += 1
    payload_rows = [
        {
            "species_latin_name": str(row["species_latin_name"]),
            "project_accession": str(row["project_accession"]),
            "paper_doi": row["paper_doi"],
            "final_sample_count": row["final_sample_count"],
            "expected_sample_count": row["expected_sample_count"],
            "minimum_expected_sample_count": row["minimum_expected_sample_count"],
            "minimum_gap_count": row["minimum_gap_count"],
            "lacking_defensible_site_assignment_count": row[
                "lacking_defensible_site_assignment_count"
            ],
            "missing_chronology_count": row["missing_chronology_count"],
            "chronology_conflict_count": row["chronology_conflict_count"],
            "chronology_ambiguity_count": row["chronology_ambiguity_count"],
            "coordinate_blocked_count": row["coordinate_blocked_count"],
            "publication_readiness_status": row["publication_readiness_status"],
            "major_deficit_reasons": row["major_deficit_reasons"],
        }
        for row in rows
    ]
    return {
        "schema_version": "animal-species-project-deficit-ledger.v1",
        "row_count": len(payload_rows),
        "species_counts": species_counts,
        "rows": payload_rows,
    }
