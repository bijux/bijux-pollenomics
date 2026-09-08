"""Sample-level evidence normalization and refusal accounting."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re

from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)

from ....core.repository import repository_data_root
from ...projects.evidence.chronology import build_project_sample_chronology_rows
from ...projects.registry.samples import (
    AdnaCuratedSampleRow,
    build_species_curated_sample_rows,
)
from ...species.definitions import AdnaSpeciesDefinition, resolve_species_definition
from .chronology import (
    _apply_chronology_semantics,
    _fallback_chronology_evidence_class,
    _fallback_chronology_precision_posture,
    normalize_chronology_text,
    normalize_explicit_bp_window,
)
from .models import AdnaNormalizationRefusal, AdnaProjectSummary
from .primitives import normalize_coordinate_resolution


def _build_sample_records(
    species_name: str,
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[tuple[AdnaSampleRecord, ...], tuple[AdnaNormalizationRefusal, ...]]:
    species = resolve_species_definition(species_name)
    project_index = {
        project.project_accession: project for project in project_summaries
    }
    chronology_index = {
        project_accession: {
            chronology_row.repo_stable_sample_id: chronology_row
            for chronology_row in build_project_sample_chronology_rows(
                _default_data_root(),
                project_accession,
            )
        }
        for project_accession in project_index
    }
    sample_records: list[AdnaSampleRecord] = []
    refusals: list[AdnaNormalizationRefusal] = []

    for row in build_species_curated_sample_rows(species_name):
        if not _sample_record_is_admissible(row):
            experiment_only = row.sample_evidence_status == "experiment_level_only"
            refusals.append(
                AdnaNormalizationRefusal(
                    schema_version="adna-normalization-refusal.v1",
                    species_latin_name=species.latin_name,
                    source_token=(f"{row.project_accession}:{row.stable_sample_id}"),
                    record_kind="sample_record",
                    reason=(
                        "experiment_to_biological_sample_mapping_unavailable"
                        if experiment_only
                        else "sample_evidence_not_yet_recoverable"
                    ),
                    detail=(
                        "Source-native identity evidence remains available, but this "
                        f"{'sequencing experiment' if experiment_only else 'placeholder'} "
                        "is refused from normalized biological-sample artifacts: "
                        f"inclusion_status={row.inclusion_status}; "
                        f"sample_evidence_status={row.sample_evidence_status}; "
                        f"sample_identity_resolution={row.sample_identity_resolution}."
                    ),
                )
            )
            continue
        project = project_index[row.project_accession]
        chronology_row = chronology_index.get(row.project_accession, {}).get(
            row.stable_sample_id
        )
        coordinate_resolution = normalize_coordinate_resolution(
            latitude_text=row.latitude_text,
            longitude_text=row.longitude_text,
            geographic_basis=row.coordinate_basis,
        )
        normalized_chronology = (
            normalize_explicit_bp_window(
                chronology_row.time_start_bp
                if chronology_row is not None
                else row.time_start_bp,
                chronology_row.time_end_bp
                if chronology_row is not None
                else row.time_end_bp,
                original_text=(
                    chronology_row.chronology_text
                    if chronology_row is not None
                    else row.chronology_text
                ),
                dating_basis=chronology_row.dating_basis
                if chronology_row is not None
                else row.dating_basis,
            )
            if (
                chronology_row is not None
                and chronology_row.time_start_bp is not None
                and chronology_row.time_end_bp is not None
            )
            or (
                chronology_row is None
                and row.time_start_bp is not None
                and row.time_end_bp is not None
            )
            else normalize_chronology_text(
                chronology_row.chronology_text
                if chronology_row is not None
                else row.chronology_text,
                dating_basis=chronology_row.dating_basis
                if chronology_row is not None
                else row.dating_basis,
            )
        )
        chronology = _apply_chronology_semantics(
            _chronology_with_source_mean(
                normalized_chronology,
                None if chronology_row is None else chronology_row.time_mean_bp,
            ),
            evidence_class=(
                chronology_row.chronology_evidence_class
                if chronology_row is not None
                else _fallback_chronology_evidence_class(
                    chronology=normalized_chronology,
                    dating_basis=row.dating_basis,
                )
            ),
            precision_posture=(
                chronology_row.chronology_precision_posture
                if chronology_row is not None
                else _fallback_chronology_precision_posture(normalized_chronology)
            ),
        )
        locality_text = row.site_label
        sample_records.append(
            AdnaSampleRecord(
                identity=AdnaSampleIdentity(
                    namespace=f"{species.slug}:curated_sample",
                    stable_token=(
                        f"{species.slug}:sample:{row.stable_sample_id.casefold()}"
                    ),
                    accession_lineage=(
                        f"species:{species.latin_name}",
                        f"source:{row.source_family}",
                        f"project:{row.project_accession}",
                        f"sample:{row.stable_sample_id}",
                    ),
                ),
                locality_identity=AdnaLocalityIdentity(
                    namespace=f"{species.slug}:sample_locality",
                    stable_token=_locality_identity_token(
                        species=species,
                        project_accession=row.project_accession,
                        locality_text=locality_text,
                        political_entity=row.political_entity or "",
                    ),
                    locality_text=locality_text,
                    political_entity=row.political_entity,
                    source_anchor_tokens=(row.project_accession, row.sample_basis),
                ),
                species_latin_name=row.species_latin_name,
                species_common_name=row.species_common_name,
                source_family=row.source_family,
                source_release=row.source_release,
                record_modality=row.record_modality,
                review_strength=project.review_strength,
                provenance_quality=row.provenance_quality,
                master_id=row.stable_sample_id,
                group_id=row.project_accession,
                locality=(
                    None
                    if row.political_entity is None
                    and "not yet extracted" in locality_text
                    else locality_text
                ),
                political_entity=row.political_entity,
                coordinates=AdnaCoordinate(
                    latitude=coordinate_resolution.coordinate.latitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    longitude=coordinate_resolution.coordinate.longitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    latitude_text=row.latitude_text,
                    longitude_text=row.longitude_text,
                    confidence=coordinate_resolution.confidence,
                ),
                publication=row.publication,
                year_first_published=row.publication_year,
                full_date=row.chronology_text,
                chronology=chronology,
                data_type=row.data_type,
                molecular_sex="",
                datasets=(project.summary_token,),
                project_accession=row.project_accession,
                paper_doi=row.paper_doi,
                paper_url=row.paper_url,
                supplementary_source=row.supplementary_source,
                inclusion_status=row.inclusion_status,
                inclusion_note=row.inclusion_note,
                chronology_strength=(
                    chronology_row.chronology_strength
                    if chronology_row is not None
                    else "project_context_interval"
                    if normalized_chronology.time_start_bp is not None
                    and normalized_chronology.time_end_bp is not None
                    else "project_context_text_only"
                    if normalized_chronology.original_text
                    else "unresolved"
                ),
                chronology_normalization_status=(
                    chronology_row.chronology_normalization_status
                    if chronology_row is not None
                    else "normalized_point"
                    if normalized_chronology.time_start_bp is not None
                    and normalized_chronology.time_end_bp is not None
                    and normalized_chronology.time_start_bp
                    == normalized_chronology.time_end_bp
                    else "normalized_interval"
                    if normalized_chronology.time_start_bp is not None
                    and normalized_chronology.time_end_bp is not None
                    else "text_only_unparsed"
                    if normalized_chronology.original_text
                    else "unresolved"
                ),
                chronology_provenance_path=(
                    chronology_row.chronology_provenance_path
                    if chronology_row is not None
                    else ""
                ),
                chronology_provenance_kind=(
                    chronology_row.chronology_provenance_kind
                    if chronology_row is not None
                    else ""
                ),
                chronology_provenance_locator=(
                    chronology_row.chronology_provenance_locator
                    if chronology_row is not None
                    else ""
                ),
                chronology_provenance_text=(
                    chronology_row.chronology_provenance_text
                    if chronology_row is not None
                    else ""
                ),
                chronology_conflict_note=(
                    chronology_row.chronology_conflict_note
                    if chronology_row is not None
                    else ""
                ),
                sample_basis=row.sample_basis,
                archive_native_sample_id=row.archive_native_sample_id,
                paper_native_sample_label=row.paper_native_sample_label,
                supplementary_table_sample_label=row.supplementary_table_sample_label,
                sample_evidence_status=row.sample_evidence_status,
                sample_lineage_path=row.sample_lineage_path,
                sample_lineage_locator=row.sample_lineage_locator,
                sample_lineage_excerpt=row.sample_lineage_excerpt,
                sample_identity_resolution=row.sample_identity_resolution,
                sample_ambiguity_note=row.sample_ambiguity_note,
                source_native_tax_id=row.source_native_tax_id,
                source_native_scientific_name=row.source_native_scientific_name,
                taxon_alignment_status=row.taxon_alignment_status,
                archive_native_experiment_id=row.archive_native_experiment_id,
                source_native_identity_kind=row.source_native_identity_kind,
            )
        )

    sample_records.sort(key=lambda item: (item.project_accession, item.genetic_id))
    refusals.sort(key=lambda item: item.source_token)
    return tuple(sample_records), tuple(refusals)


def _chronology_with_source_mean(
    chronology: AdnaChronology,
    source_mean_bp: int | None,
) -> AdnaChronology:
    if source_mean_bp is None:
        return chronology
    if (
        isinstance(source_mean_bp, bool)
        or not isinstance(source_mean_bp, int)
        or source_mean_bp < 0
    ):
        raise ValueError(
            "sample-owned chronology mean must be a nonnegative integer BP"
        )
    younger_bp = chronology.time_start_bp
    older_bp = chronology.time_end_bp
    if (
        younger_bp is None
        or older_bp is None
        or not younger_bp <= source_mean_bp <= older_bp
    ):
        raise ValueError("sample-owned chronology mean must lie inside its BP interval")
    return replace(chronology, time_mean_bp=source_mean_bp)


RECOVERED_SAMPLE_EVIDENCE_STATUSES = frozenset(
    {"archive_native", "article_text_extracted", "direct_table_extracted"}
)


def _sample_record_is_admissible(row: AdnaCuratedSampleRow) -> bool:
    """Admit recovered identities without requiring resolved site context."""
    return (
        row.sample_evidence_status in RECOVERED_SAMPLE_EVIDENCE_STATUSES
        and row.sample_identity_resolution == "final"
    )


def _default_data_root() -> Path:
    return repository_data_root(__file__)


def _locality_identity_token(
    *,
    species: AdnaSpeciesDefinition,
    project_accession: str,
    locality_text: str,
    political_entity: str | None,
) -> str:
    locality_fragment = _normalize_sample_label(locality_text) or "unresolved"
    entity_fragment = _normalize_sample_label(political_entity or "")
    if entity_fragment:
        return (
            f"{species.slug}:locality:{project_accession.casefold()}:"
            f"{locality_fragment}:{entity_fragment}"
        )
    return f"{species.slug}:locality:{project_accession.casefold()}:{locality_fragment}"


def _normalize_sample_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())
