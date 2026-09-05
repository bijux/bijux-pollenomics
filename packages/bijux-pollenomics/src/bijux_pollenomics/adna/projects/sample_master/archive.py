"""Archive-native aDNA sample identity recovery."""

from __future__ import annotations

from pathlib import Path
import re
from bijux_pollenomics.adna.workflow.source_artifacts import (
    read_source_artifact_text,
)
from bijux_pollenomics.adna.sources.ena import (
    AdnaArchiveProject,
    build_archive_project_catalog,
)
from bijux_pollenomics.adna.species.definitions import AdnaSpeciesDefinition
from bijux_pollenomics.adna.sources.library import ADNA_SOURCE_LIBRARY_DIR
from bijux_pollenomics.adna.projects.registry.archive_samples import (
    read_archive_project_samples,
)
from bijux_pollenomics.adna.projects.evidence.article_samples import (
    resolve_article_sample_evidence,
)
from .identity import (
    _normalize_sample_label,
    _resolve_data_relative_path,
    _taxon_alignment_status,
)
from .models import AdnaProjectSampleMaster, AdnaProjectSampleMasterRow


def _empty_sample_master_row(master: AdnaProjectSampleMaster) -> dict[str, object]:
    return {
        "species_latin_name": master.species_latin_name,
        "species_common_name": master.species_common_name,
        "project_accession": master.project_accession,
        "repo_stable_sample_id": "",
        "archive_native_sample_id": "",
        "paper_native_sample_label": "",
        "supplementary_table_sample_label": "",
        "preferred_sample_label": "",
        "sample_basis": "",
        "sample_evidence_status": "not_yet_recoverable",
        "sample_lineage_path": "",
        "sample_lineage_locator": "",
        "sample_lineage_excerpt": "",
        "sample_identity_resolution": "provisional",
        "sample_ambiguity_note": "No recoverable sample-level row has been extracted yet for this project.",
        "locality_text": "",
        "political_entity": "",
        "latitude_text": "",
        "longitude_text": "",
        "chronology_text": "",
        "source_native_tax_id": "",
        "source_native_scientific_name": "",
        "taxon_alignment_status": "not_reported",
    }


def _project_by_accession(project_accession: str) -> AdnaArchiveProject:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project
    raise KeyError(project_accession)


def _archive_native_sample_rows(
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    if project.accession_scope == "sample":
        return (
            _archive_native_row(
                species=species,
                project=project,
                accession=project.project_accession,
            ),
        )
    if project.accession_scope != "accession_range":
        return ()
    expanded = _expand_accession_range(project.project_accession)
    return tuple(
        _archive_native_row(species=species, project=project, accession=accession)
        for accession in expanded
    )


def _archive_native_row(
    *,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
    accession: str,
) -> AdnaProjectSampleMasterRow:
    article_evidence = resolve_article_sample_evidence(accession)
    if article_evidence is not None:
        return AdnaProjectSampleMasterRow(
            species_latin_name=species.latin_name,
            species_common_name=species.common_name,
            project_accession=project.project_accession,
            repo_stable_sample_id=f"{project.project_accession}:{accession}".casefold(),
            archive_native_sample_id=accession,
            paper_native_sample_label=article_evidence.sample_label,
            supplementary_table_sample_label="",
            preferred_sample_label=article_evidence.sample_label,
            sample_basis="primary_article_accession_mapping",
            sample_evidence_status="article_text_extracted",
            sample_lineage_path=article_evidence.source_path,
            sample_lineage_locator=article_evidence.source_locator,
            sample_lineage_excerpt=article_evidence.source_excerpt,
            sample_identity_resolution="final",
            sample_ambiguity_note="",
            locality_text=article_evidence.locality_text,
            political_entity=article_evidence.political_entity,
            latitude_text="",
            longitude_text="",
            chronology_text=article_evidence.chronology_text,
        )
    return AdnaProjectSampleMasterRow(
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        repo_stable_sample_id=f"{project.project_accession}:{accession}".casefold(),
        archive_native_sample_id=accession,
        paper_native_sample_label="",
        supplementary_table_sample_label="",
        preferred_sample_label=accession,
        sample_basis=(
            "sample_accession_anchor"
            if project.accession_scope == "sample"
            else "accession_range_anchor"
        ),
        sample_evidence_status="archive_native",
        sample_lineage_path=f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/archive_metadata.html",
        sample_lineage_locator=f"accession:{accession}",
        sample_lineage_excerpt=f"Archive-native accession {accession} is tracked directly in the curated intake catalog.",
        sample_identity_resolution="final",
        sample_ambiguity_note="",
        locality_text="",
        political_entity="",
        latitude_text="",
        longitude_text="",
        chronology_text="",
    )


def _expand_accession_range(accession_range: str) -> tuple[str, ...]:
    match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", accession_range)
    if match is None:
        return (accession_range,)
    left_prefix, left_value, right_prefix, right_value = match.groups()
    if left_prefix != right_prefix:
        return (accession_range,)
    width = len(left_value)
    start = int(left_value)
    end = int(right_value)
    return tuple(f"{left_prefix}{value:0{width}d}" for value in range(start, end + 1))


def _project_scope_archive_sample_rows(
    output_root: Path,
    species: AdnaSpeciesDefinition,
    project: AdnaArchiveProject,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    archive_path = _resolve_data_relative_path(
        Path(output_root),
        f"adna/governance/source_library/projects/{project.project_accession}/archive_metadata.html",
    )
    if not archive_path.is_file():
        return ()
    archive_samples = read_archive_project_samples(archive_path)
    rows = []
    for sample in archive_samples:
        experiment_only = (
            sample.source_native_identity_kind == "sequencing_experiment_accession"
        )
        source_identity = (
            sample.archive_native_experiment_id
            if experiment_only
            else sample.archive_native_sample_id
        )
        rows.append(
            AdnaProjectSampleMasterRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                project_accession=project.project_accession,
                repo_stable_sample_id=(
                    f"{project.project_accession}:"
                    f"{'experiment:' if experiment_only else ''}{source_identity}"
                ).casefold(),
                archive_native_sample_id=sample.archive_native_sample_id,
                paper_native_sample_label=sample.source_native_sample_label,
                supplementary_table_sample_label="",
                preferred_sample_label=(
                    sample.source_native_sample_label or source_identity
                ),
                sample_basis=(
                    "archive_project_experiment_anchor"
                    if experiment_only
                    else "archive_project_sample_accession_anchor"
                ),
                sample_evidence_status=(
                    "experiment_level_only" if experiment_only else "archive_native"
                ),
                sample_lineage_path=f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/archive_metadata.html",
                sample_lineage_locator=sample.source_locator,
                sample_lineage_excerpt=sample.source_excerpt,
                sample_identity_resolution="provisional"
                if experiment_only
                else "final",
                sample_ambiguity_note=(
                    "The cached NCBI result identifies a sequencing experiment, not a "
                    "biological sample; no authoritative experiment-to-BioSample mapping "
                    "is present in the admitted capture."
                    if experiment_only
                    else ""
                ),
                locality_text="",
                political_entity="",
                latitude_text="",
                longitude_text="",
                chronology_text="",
                source_native_tax_id=" | ".join(sample.source_native_tax_ids),
                source_native_scientific_name=" | ".join(
                    sample.source_native_scientific_names
                ),
                taxon_alignment_status=_taxon_alignment_status(
                    configured_species=species.latin_name,
                    source_native_scientific_names=sample.source_native_scientific_names,
                ),
                archive_native_experiment_id=sample.archive_native_experiment_id,
                source_native_identity_kind=sample.source_native_identity_kind,
            )
        )
    return tuple(rows)


def _project_scope_archive_sample_accessions(
    output_root: Path,
    project_accession: str,
) -> tuple[str, ...]:
    archive_path = _resolve_data_relative_path(
        Path(output_root),
        f"adna/governance/source_library/projects/{project_accession}/archive_metadata.html",
    )
    if not archive_path.is_file():
        return ()
    return tuple(
        row.archive_native_sample_id
        for row in read_archive_project_samples(archive_path)
    )


def _build_archive_sample_accession_lookup(
    output_root: Path,
    project_accession: str,
) -> dict[str, str]:
    archive_path = _resolve_data_relative_path(
        Path(output_root),
        f"adna/governance/source_library/projects/{project_accession}/archive_metadata.html",
    )
    if not archive_path.is_file():
        return {}
    rows = read_source_artifact_text(
        archive_path,
        encoding="utf-8",
        errors="ignore",
    ).splitlines()
    if not rows:
        return {}
    header = rows[0].split("\t")
    try:
        sample_index = header.index("sample_accession")
        submitted_index = header.index("submitted_ftp")
    except ValueError:
        return {}
    lookup: dict[str, str] = {}
    for row in rows[1:]:
        fields = row.split("\t")
        if len(fields) <= max(sample_index, submitted_index):
            continue
        sample_accession = fields[sample_index].strip()
        for submitted_path in fields[submitted_index].split(";"):
            basename = Path(submitted_path.strip()).name
            if not basename:
                continue
            sample_label = re.sub(r"\.fastq\.gz$", "", basename, flags=re.IGNORECASE)
            sample_label = re.sub(r"_(?:E\d+|i\d+).*?$", "", sample_label)
            normalized = _normalize_sample_label(sample_label)
            if normalized and normalized not in lookup:
                lookup[normalized] = sample_accession
    return lookup
