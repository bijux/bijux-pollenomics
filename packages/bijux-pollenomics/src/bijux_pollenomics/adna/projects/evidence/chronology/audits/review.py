"""Sample ambiguity, conflict, and review-row audit surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import AdnaProjectSampleChronologyRow


def _build_sample_chronology_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import (
        _row_requires_attention,
        build_archive_project_catalog,
        build_project_sample_chronology_rows,
    )

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if not _row_requires_attention(row):
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "chronology_text": row.chronology_text,
                    "chronology_conflict_note": row.chronology_conflict_note,
                    "chronology_provenance_path": row.chronology_provenance_path,
                    "chronology_provenance_locator": row.chronology_provenance_locator,
                    "review_note": row.review_note,
                }
            )
    return tuple(rows)


def _build_sample_chronology_review_rows(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import build_archive_project_catalog, build_project_sample_chronology_rows

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            rows.append(row.as_dict())
    rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            str(row["project_accession"]),
            str(row["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)


def _build_sample_chronology_conflict_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    from . import build_archive_project_catalog, build_project_sample_chronology_rows

    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_chronology_rows(
            output_root, project.project_accession
        ):
            if not row.chronology_conflict_note.strip():
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "chronology_strength": row.chronology_strength,
                    "chronology_evidence_class": row.chronology_evidence_class,
                    "chronology_precision_posture": row.chronology_precision_posture,
                    "chronology_normalization_status": row.chronology_normalization_status,
                    "chronology_text": row.chronology_text,
                    "time_start_bp": row.time_start_bp,
                    "time_end_bp": row.time_end_bp,
                    "dating_basis": row.dating_basis,
                    "chronology_provenance_path": row.chronology_provenance_path,
                    "chronology_provenance_locator": row.chronology_provenance_locator,
                    "chronology_provenance_text": row.chronology_provenance_text,
                    "chronology_conflict_note": row.chronology_conflict_note,
                }
            )
    return tuple(rows)


def _row_requires_attention_impl(row: AdnaProjectSampleChronologyRow) -> bool:
    return (
        row.chronology_strength != "sample_owned_interval"
        or row.chronology_precision_posture
        not in {"sample_precise_interval", "sample_precise_point"}
        or bool(row.chronology_conflict_note.strip())
    )
