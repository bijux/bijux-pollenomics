"""Chronology precision-posture audit and exact denominator counts."""

from __future__ import annotations

from pathlib import Path


def _build_sample_chronology_precision_audit(output_root: Path) -> dict[str, object]:
    from . import (
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        _counts_by_key,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if row.chronology_precision_posture == "sample_precise_point":
                precision_bucket = "sample_precise_point"
            elif row.chronology_precision_posture == "sample_precise_interval":
                precision_bucket = "sample_precise_interval"
            elif row.chronology_precision_posture == "sample_approximate_or_modeled":
                precision_bucket = "sample_approximate_or_modeled"
            elif row.chronology_precision_posture == "contextual_interval":
                precision_bucket = "contextual_interval"
            elif row.chronology_precision_posture == "broad_period_only":
                precision_bucket = "broad_period_only"
            else:
                precision_bucket = "unresolved"
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_text": row.chronology_text,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "dating_basis": row.dating_basis,
                    "precision_bucket": precision_bucket,
                    "precision_review_note": row.review_note,
                    "chronology_conflict_note": row.chronology_conflict_note,
                }
            )
    precision_counts = _counts_by_key(
        rows,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        lambda row: str(row["chronology_precision_posture"]),
    )
    return {
        "schema_version": "animal-sample-chronology-precision-audit.v1",
        "row_count": len(rows),
        "precision_counts": precision_counts,
        "rows": rows,
    }
