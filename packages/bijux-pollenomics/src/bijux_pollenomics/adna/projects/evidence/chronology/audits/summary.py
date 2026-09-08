"""Per-project and cross-project chronology audit summaries."""

from __future__ import annotations

from pathlib import Path


def _build_project_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
        ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        ADNA_CHRONOLOGY_STRENGTHS,
        _counts_by_key,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        chronology_rows = build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
        strength_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_STRENGTHS,
            lambda row: row.chronology_strength,
        )
        evidence_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
            lambda row: row.chronology_evidence_class,
        )
        precision_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_PRECISION_POSTURES,
            lambda row: row.chronology_precision_posture,
        )
        normalization_counts = _counts_by_key(
            chronology_rows,
            ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
            lambda row: row.chronology_normalization_status,
        )
        conflict_count = sum(
            1 for row in chronology_rows if row.chronology_conflict_note.strip()
        )
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "recovered_sample_row_count": len(chronology_rows),
                "sample_owned_interval_count": strength_counts["sample_owned_interval"],
                "sample_owned_text_only_count": strength_counts[
                    "sample_owned_text_only"
                ],
                "project_context_interval_count": strength_counts[
                    "project_context_interval"
                ],
                "project_context_text_only_count": strength_counts[
                    "project_context_text_only"
                ],
                "unresolved_count": strength_counts["unresolved"],
                "direct_radiocarbon_date_count": evidence_counts[
                    "direct_radiocarbon_date"
                ],
                "modeled_sample_date_count": evidence_counts["modeled_sample_date"],
                "archaeological_context_date_count": evidence_counts[
                    "archaeological_context_date"
                ],
                "broad_period_label_count": evidence_counts["broad_period_label"],
                "historical_or_recent_date_count": evidence_counts[
                    "historical_or_recent_date"
                ],
                "evidence_class_unresolved_count": evidence_counts["unresolved"],
                "sample_precise_point_count": precision_counts["sample_precise_point"],
                "sample_precise_interval_count": precision_counts[
                    "sample_precise_interval"
                ],
                "sample_approximate_or_modeled_count": precision_counts[
                    "sample_approximate_or_modeled"
                ],
                "contextual_interval_count": precision_counts["contextual_interval"],
                "broad_period_only_count": precision_counts["broad_period_only"],
                "precision_unresolved_count": precision_counts["unresolved"],
                "normalized_interval_count": normalization_counts[
                    "normalized_interval"
                ],
                "normalized_point_count": normalization_counts["normalized_point"],
                "text_only_unparsed_count": normalization_counts["text_only_unparsed"],
                "normalization_unresolved_count": normalization_counts["unresolved"],
                "conflicting_context_count": conflict_count,
            }
        )
    return tuple(rows)


def _build_cross_project_sample_chronology_audit(
    output_root: Path,
) -> dict[str, object]:
    from . import (
        ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
        ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        _counts_by_key,
        build_archive_project_catalog,
        build_project_sample_chronology_review_rows,
        build_project_sample_chronology_rows,
    )

    review_rows = build_project_sample_chronology_review_rows(output_root)
    sample_rows = [
        row
        for project in build_archive_project_catalog()
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        )
    ]
    normalization_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
        lambda row: row.chronology_normalization_status,
    )
    evidence_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
        lambda row: row.chronology_evidence_class,
    )
    precision_counts = _counts_by_key(
        sample_rows,
        ADNA_CHRONOLOGY_PRECISION_POSTURES,
        lambda row: row.chronology_precision_posture,
    )
    projects_requiring_manual_review = [
        row["project_accession"]
        for row in review_rows
        if row["text_only_unparsed_count"]
        or row["normalization_unresolved_count"]
        or row["conflicting_context_count"]
    ]
    return {
        "schema_version": "animal-sample-chronology-normalization-audit.v1",
        "sample_row_count": len(sample_rows),
        "normalized_interval_count": normalization_counts["normalized_interval"],
        "normalized_point_count": normalization_counts["normalized_point"],
        "text_only_unparsed_count": normalization_counts["text_only_unparsed"],
        "unresolved_count": normalization_counts["unresolved"],
        "evidence_counts": evidence_counts,
        "precision_counts": precision_counts,
        "projects_requiring_manual_review": projects_requiring_manual_review,
        "rows": list(review_rows),
    }
