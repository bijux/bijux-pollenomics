"""Project locality aggregation and Nordic context posture."""

from __future__ import annotations
from collections import defaultdict
from bijux_pollenomics.adna.domain.models import (
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from ...projects.registry.context import AdnaProjectContext, resolve_project_context
from ...projects.registry.localities import build_species_project_locality_leads
from ...projects.evidence.chronology import build_project_sample_chronology_rows
from ...projects.registry.samples import (
    AdnaCuratedSampleRow,
    build_species_curated_sample_rows,
)
from ...sources.ena import (
    build_species_archive_projects,
)
from ...species.definitions import resolve_species_definition

from .chronology import _aggregate_locality_chronology
from .models import AdnaNormalizationRefusal, AdnaProjectSummary
from .primitives import normalize_coordinate_resolution
from .samples import (
    _default_data_root,
    _locality_identity_token,
    _normalize_sample_label,
)


def _is_nordic_locality(
    *,
    political_entity: str | None,
    locality_text: str,
    project_context: AdnaProjectContext,
) -> bool:
    entity = (political_entity or "").strip()
    if entity in {"Sweden", "Norway", "Finland", "Denmark", "Iceland"}:
        return True
    if entity == "Baltic Sea Region":
        return True
    locality = locality_text.casefold()
    if "svalbard" in locality:
        return True
    return (
        getattr(project_context, "nordic_relevance", "") == "nordic_relevant_unmapped"
    )


def _nordic_locality_reason(
    *,
    political_entity: str | None,
    locality_text: str,
    project_context: AdnaProjectContext,
) -> str:
    if _is_nordic_locality(
        political_entity=political_entity,
        locality_text=locality_text,
        project_context=project_context,
    ):
        entity = (political_entity or "").strip()
        if entity in {"Sweden", "Norway", "Finland", "Denmark", "Iceland"}:
            return f"This locality falls inside the Nordic publication footprint through direct {entity} sample evidence."
        if entity == "Baltic Sea Region":
            return "This locality is retained for Nordic publication because the Baltic Sea Region bundle is explicitly assigned into Nordic country outputs."
        if "svalbard" in locality_text.casefold():
            return "This locality falls inside the Nordic publication footprint through direct Svalbard evidence."
    return project_context.nordic_relevance_reason


def build_species_project_locality_records(
    species_name: str,
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[tuple[AdnaLocalitySummary, ...], tuple[AdnaNormalizationRefusal, ...]]:
    """Build curated non-human project locality rows and explicit locality refusals."""
    species = resolve_species_definition(species_name)
    project_index = {
        summary.project_accession: summary for summary in project_summaries
    }
    archive_index = {
        project.project_accession: project
        for project in build_species_archive_projects(species_name)
    }
    curated_sample_rows = build_species_curated_sample_rows(species_name)
    sample_rows_by_project: dict[str, list[AdnaCuratedSampleRow]] = defaultdict(list)
    for row in curated_sample_rows:
        sample_rows_by_project[row.project_accession].append(row)
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
    locality_records: list[AdnaLocalitySummary] = []
    refusals: list[AdnaNormalizationRefusal] = []

    leads = build_species_project_locality_leads(tuple(project_index))
    covered_accessions = {lead.project_accession for lead in leads}

    for lead in leads:
        project = project_index.get(lead.project_accession)
        if project is None:
            continue
        project_context = resolve_project_context(archive_index[lead.project_accession])
        matched_sample_rows = [
            row
            for row in sample_rows_by_project.get(lead.project_accession, [])
            if _normalize_sample_label(row.site_label)
            == _normalize_sample_label(lead.locality_text)
        ]
        if not matched_sample_rows:
            matched_sample_rows = list(
                sample_rows_by_project.get(lead.project_accession, [])
            )
        coordinate_resolution = normalize_coordinate_resolution(
            latitude_text=lead.latitude_text,
            longitude_text=lead.longitude_text,
            geographic_basis=lead.coordinate_basis,
        )
        chronology = _aggregate_locality_chronology(
            sample_rows=tuple(matched_sample_rows),
            chronology_lookup=chronology_index.get(lead.project_accession, {}),
            fallback_text=lead.chronology_text,
            fallback_start_bp=lead.time_start_bp,
            fallback_end_bp=lead.time_end_bp,
            dating_basis=project.chronology_basis or project.dating_basis or "unknown",
        )
        identity = AdnaLocalityIdentity(
            namespace=f"{species.slug}:project_locality",
            stable_token=_locality_identity_token(
                species=species,
                project_accession=lead.project_accession,
                locality_text=lead.locality_text,
                political_entity=lead.political_entity,
            ),
            locality_text=lead.locality_text,
            political_entity=lead.political_entity,
            source_anchor_tokens=(
                lead.project_accession,
                lead.latitude_text,
                lead.longitude_text,
            ),
        )
        locality_records.append(
            AdnaLocalitySummary(
                identity=identity,
                species_latin_name=project.species_latin_name,
                species_common_name=project.species_common_name,
                source_family=project.source_family,
                source_releases=(project.source_release,),
                record_modalities=(project.record_modality,),
                review_strengths=(project.review_strength,),
                provenance_qualities=(project.evidence_strength,),
                locality=lead.locality_text,
                coordinates=AdnaCoordinate(
                    latitude=coordinate_resolution.coordinate.latitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    longitude=coordinate_resolution.coordinate.longitude
                    if coordinate_resolution.coordinate is not None
                    else None,
                    latitude_text=lead.latitude_text,
                    longitude_text=lead.longitude_text,
                    confidence=coordinate_resolution.confidence,
                ),
                sample_count=max(len(matched_sample_rows), 1),
                sample_ids=tuple(row.stable_sample_id for row in matched_sample_rows)
                or (lead.project_accession,),
                datasets=(project.summary_token,),
                chronology=chronology,
                sample_namespace=f"{species.slug}:sample_locality",
                project_accessions=(lead.project_accession,),
                original_location_text=lead.locality_text,
                nordic_inclusion=_is_nordic_locality(
                    political_entity=lead.political_entity,
                    locality_text=lead.locality_text,
                    project_context=project_context,
                ),
                nordic_inclusion_reason=_nordic_locality_reason(
                    political_entity=lead.political_entity,
                    locality_text=lead.locality_text,
                    project_context=project_context,
                ),
                interpretation_note=lead.interpretation_note,
            )
        )

    for project in project_summaries:
        if project.project_accession in covered_accessions:
            continue
        refusals.append(
            AdnaNormalizationRefusal(
                schema_version="adna-normalization-refusal.v1",
                species_latin_name=species.latin_name,
                source_token=project.project_accession,
                record_kind="locality_records",
                reason="locality_lead_not_yet_curated",
                detail=(
                    "This project already ships project-level interpretation, but a defensible locality lead "
                    "has not yet been curated into the species-owned locality artifact."
                ),
            )
        )

    locality_records.sort(
        key=lambda item: (
            item.project_accessions[0]
            if item.project_accessions
            else item.locality_token,
            item.locality_token,
        )
    )
    refusals.sort(key=lambda item: item.source_token)
    return tuple(locality_records), tuple(refusals)
