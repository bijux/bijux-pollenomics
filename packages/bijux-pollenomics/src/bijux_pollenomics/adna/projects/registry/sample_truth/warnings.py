"""Aggregation-warning accounting for animal sample products."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from .dependencies import SampleTruthDependencies


def build_animal_sample_aggregation_warnings(
    data_root: Path,
    report_root: Path,
    *,
    dependencies: SampleTruthDependencies,
) -> dict[str, object]:
    """Count current outputs that still rely on project- or site-level aggregation."""
    del report_root
    truth = dependencies.build_animal_sample_foundation_truth(data_root)
    project_rows = cast(list[dict[str, object]], truth["project_rows"])
    project_locality_drift_rows = dependencies.build_project_locality_count_drift(
        data_root
    )
    species_sample_drift_rows = dependencies.build_species_sample_count_drift(data_root)
    sample_rows = dependencies._load_all_sample_rows(Path(data_root))
    locality_rows = dependencies._load_all_locality_rows(Path(data_root))
    summary = {
        "total_sample_row_count": len(sample_rows),
        "project_accession_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "project_accession_anchor"
        ),
        "accession_range_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "accession_range_anchor"
        ),
        "sample_accession_anchor_count": sum(
            1
            for row in sample_rows
            if str(row.get("sample_basis", "")) == "sample_accession_anchor"
        ),
        "project_locality_summary_count": sum(
            1
            for row in locality_rows
            if str(row.get("sample_namespace", "")).endswith("project_locality")
        ),
        "projects_with_project_level_sample_anchors": sum(
            1 for row in project_rows if bool(row["uses_project_level_sample_anchor"])
        ),
        "projects_with_locality_count_drift": len(project_locality_drift_rows),
        "species_with_summary_count_drift": len(species_sample_drift_rows),
    }
    warning_rows = [
        {
            "warning_class": "project_level_sample_anchors",
            "count": summary["projects_with_project_level_sample_anchors"],
            "detail": "Projects whose current sample rows are still anchored at project or accession-range level rather than true per-sample identifiers.",
        },
        {
            "warning_class": "project_locality_summary_rows",
            "count": summary["project_locality_summary_count"],
            "detail": "Locality rows that are still summarized at project-locality level rather than explicit per-sample site rows.",
        },
        {
            "warning_class": "locality_count_drift",
            "count": summary["projects_with_locality_count_drift"],
            "detail": "Projects where project-level locality summaries disagree with sample-backed site counts.",
        },
        {
            "warning_class": "species_summary_count_drift",
            "count": summary["species_with_summary_count_drift"],
            "detail": "Species summaries that disagree with the current sample-master counts.",
        },
    ]
    return {
        "schema_version": "animal-sample-aggregation-warnings.v1",
        "summary": summary,
        "warning_rows": warning_rows,
        "project_locality_drift_rows": list(project_locality_drift_rows),
        "species_sample_drift_rows": list(species_sample_drift_rows),
    }
