from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.projects.evidence.sites import resolve_project_site_evidence
from bijux_pollenomics.adna.projects.sample_master import (
    build_project_sample_master_rows,
)
from bijux_pollenomics.adna.sources.archive import (
    AdnaArchiveProject,
    build_archive_project_catalog,
)

from .models import AdnaProjectSampleChronologyRow
from .resolution import _resolve_chronology_source


def build_project_sample_chronology_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleChronologyRow, ...]:
    output_root = Path(output_root)
    project = _project_by_accession(project_accession)
    master_rows = build_project_sample_master_rows(output_root, project_accession)
    site_rows = resolve_project_site_evidence(project_accession)
    site_row = site_rows[0] if site_rows else None
    rows: list[AdnaProjectSampleChronologyRow] = []

    for master_row in master_rows:
        if master_row.source_native_identity_kind == "sequencing_experiment_accession":
            continue
        source = _resolve_chronology_source(
            master_row=master_row,
            site_row=site_row,
            dating_basis=project.dating_basis or "unknown",
        )
        rows.append(
            AdnaProjectSampleChronologyRow(
                species_latin_name=master_row.species_latin_name,
                species_common_name=master_row.species_common_name,
                project_accession=master_row.project_accession,
                repo_stable_sample_id=master_row.repo_stable_sample_id,
                preferred_sample_label=master_row.preferred_sample_label,
                sample_basis=master_row.sample_basis,
                sample_evidence_status=master_row.sample_evidence_status,
                sample_identity_resolution=master_row.sample_identity_resolution,
                sample_ambiguity_note=master_row.sample_ambiguity_note,
                chronology_text=source.chronology_text,
                chronology_strength=source.chronology_strength,
                chronology_evidence_class=source.chronology_evidence_class,
                chronology_precision_posture=source.chronology_precision_posture,
                chronology_provenance_path=source.chronology_provenance_path,
                chronology_provenance_kind=source.chronology_provenance_kind,
                chronology_provenance_locator=source.chronology_provenance_locator,
                chronology_provenance_text=source.chronology_provenance_text,
                chronology_normalization_status=source.chronology_normalization_status,
                time_start_bp=source.time_start_bp,
                time_end_bp=source.time_end_bp,
                time_mean_bp=source.time_mean_bp,
                dating_basis=project.dating_basis or "unknown",
                chronology_conflict_note=source.chronology_conflict_note,
                review_note=source.review_note,
            )
        )

    rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(rows)


def _project_by_accession(project_accession: str) -> AdnaArchiveProject:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)
