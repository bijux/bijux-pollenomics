from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.domain.models import AdnaSiteEvidenceRecord
from bijux_pollenomics.adna.projects.evidence.sites import resolve_project_site_evidence
from bijux_pollenomics.adna.projects.sample_master import (
    AdnaProjectSampleMasterRow,
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
    rows: list[AdnaProjectSampleChronologyRow] = []

    for master_row in master_rows:
        if master_row.source_native_identity_kind == "sequencing_experiment_accession":
            continue
        site_row = _matching_site_row(master_row, site_rows)
        dating_basis = (
            master_row.chronology_dating_basis or project.dating_basis or "unknown"
        )
        source = _resolve_chronology_source(
            master_row=master_row,
            site_row=site_row,
            dating_basis=dating_basis,
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
                dating_basis=dating_basis,
                chronology_conflict_note=source.chronology_conflict_note,
                review_note=source.review_note,
            )
        )

    rows.sort(key=lambda row: (row.project_accession, row.repo_stable_sample_id))
    return tuple(rows)


def _matching_site_row(
    master_row: AdnaProjectSampleMasterRow,
    site_rows: tuple[AdnaSiteEvidenceRecord, ...],
) -> AdnaSiteEvidenceRecord | None:
    """Resolve exact sample locality evidence and refuse multi-site fallbacks."""
    master_key = _normalized_place_key(
        master_row.locality_text, master_row.political_entity
    )
    if master_key[0]:
        matches = [
            row
            for row in site_rows
            if _normalized_place_key(
                str(getattr(row, "site_label", "")),
                str(getattr(row, "political_entity", "")),
            )
            == master_key
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                "Multiple site-evidence rows match one sample locality: "
                f"{master_row.project_accession} {master_row.repo_stable_sample_id}"
            )
    if len(site_rows) == 1:
        return site_rows[0]
    return None


def _normalized_place_key(locality: str, political_entity: str) -> tuple[str, str]:
    return _normalize_place(locality), _normalize_place(political_entity)


def _normalize_place(value: str) -> str:
    normalized = "".join(
        character for character in value.casefold() if character.isalnum()
    )
    return "" if normalized in {"na", "notavailable", "unknown"} else normalized


def _project_by_accession(project_accession: str) -> AdnaArchiveProject:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)
