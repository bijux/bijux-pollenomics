"""Per-sample chronology provenance packets and temporal semantics."""

from __future__ import annotations

from pathlib import Path


def _build_sample_chronology_provenance_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        _normalization_rule_for,
        _temporal_semantics_for_chronology_row,
        _uncertainty_note_for,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            temporal_semantics = _temporal_semantics_for_chronology_row(row)
            rows.append(
                {
                    "species_latin_name": row.species_latin_name,
                    "species_common_name": row.species_common_name,
                    "project_accession": row.project_accession,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "published_wording": row.chronology_text,
                    "source_wording_excerpt": row.chronology_provenance_text,
                    "provenance_surface": row.chronology_provenance_path,
                    "provenance_kind": row.chronology_provenance_kind,
                    "provenance_locator": row.chronology_provenance_locator,
                    "dating_basis": row.dating_basis,
                    "evidence_class": row.chronology_evidence_class,
                    "precision_posture": row.chronology_precision_posture,
                    "normalization_status": row.chronology_normalization_status,
                    "normalization_rule": _normalization_rule_for(row),
                    "uncertainty_note": _uncertainty_note_for(row),
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "time_mean_bp": row.time_mean_bp,
                    "temporal_semantics": temporal_semantics,
                }
            )
    rows.sort(
        key=lambda row: (
            str(row["project_accession"]),
            str(row["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)
