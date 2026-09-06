"""Project, study, and lineage normalization."""

from __future__ import annotations

import re
from collections import defaultdict

from bijux_pollenomics.adna.workflow.paths import ADNA_SPECIES_DIR

from ...projects.registry.context import AdnaProjectContext, resolve_project_context
from ...sources.archive import (
    AdnaArchiveProject,
    build_species_archive_projects,
    classify_archive_project_evidence,
)
from ...species.definitions import AdnaSpeciesDefinition, resolve_species_definition
from .models import (
    AdnaNormalizationLineage,
    AdnaNormalizationRefusal,
    AdnaProjectSummary,
    AdnaStudySummary,
)
from .primitives import normalize_breed_label, normalize_species_anchor


def _build_project_summary(
    project: AdnaArchiveProject,
    curation_class: str,
) -> AdnaProjectSummary:
    species = normalize_species_anchor(project.species_latin_name)
    project_context = resolve_project_context(project)
    paper_doi = None if project.paper_linkage is None else project.paper_linkage.doi
    paper_title = (
        None if project.paper_linkage is None else project.paper_linkage.paper_title
    )
    support_class = _support_class_for(project, curation_class)
    return AdnaProjectSummary(
        schema_version="adna-project-summary.v1",
        summary_token=f"{species.slug}:project:{project.project_accession}",
        species_latin_name=species.latin_name,
        species_common_name=species.common_name,
        project_accession=project.project_accession,
        study_token=_study_token_for(project.project_accession, paper_doi),
        source_family=project.source_family,
        source_release=project.project_accession,
        result_kind=project.result_kind,
        archive_status=project.archive_status,
        evidence_strength=classify_archive_project_evidence(project),
        review_strength=_review_strength_for(
            project.archive_status, curation_class, paper_doi
        ),
        support_class=support_class,
        record_modality=_record_modality_for(project),
        domestication_status=_domestication_status_for(curation_class),
        domestication_scope=project.domestication_scope,
        comparator_status=curation_class == "comparator_only"
        or project.archive_status == "comparator_only",
        normalized_breed_label=normalize_breed_label(
            _breed_label_from_notes(project.notes)
        ),
        sequencing_target=project.sequencing_target,
        material_basis=project.material_basis,
        chronology_basis=project.dating_basis,
        dating_basis=project.dating_basis,
        geographic_basis=project.geographic_basis,
        coordinate_policy=_coordinate_policy_for(project.geographic_basis),
        chronology_policy=_chronology_policy_for(project.dating_basis),
        paper_title=paper_title,
        paper_doi=paper_doi,
        paper_url=_paper_url_for(project),
        nordic_relevance=project_context.nordic_relevance,
        nordic_relevance_reason=project_context.nordic_relevance_reason,
        interpretation_caveat=_interpretation_caveat_for(
            project=project,
            support_class=support_class,
            project_context=project_context,
        ),
        notes=project.notes,
    )


def _normalize_project_summaries(
    species_name: str,
    curation_class: str,
) -> tuple[tuple[AdnaProjectSummary, ...], tuple[AdnaNormalizationRefusal, ...]]:
    project_summaries: list[AdnaProjectSummary] = []
    refusals: list[AdnaNormalizationRefusal] = []
    for project in build_species_archive_projects(species_name):
        try:
            project_summaries.append(_build_project_summary(project, curation_class))
        except ValueError as exc:
            refusals.append(
                AdnaNormalizationRefusal(
                    schema_version="adna-normalization-refusal.v1",
                    species_latin_name=resolve_species_definition(
                        species_name
                    ).latin_name,
                    source_token=project.project_accession,
                    record_kind="project_summary",
                    reason="defensible_species_anchor_missing",
                    detail=str(exc),
                )
            )
    normalized = _deduplicate_project_summaries(
        tuple(sorted(project_summaries, key=lambda item: item.summary_token))
    )
    return normalized, tuple(refusals)


def _deduplicate_project_summaries(
    summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[AdnaProjectSummary, ...]:
    deduplicated: dict[str, AdnaProjectSummary] = {}
    for summary in summaries:
        previous = deduplicated.get(summary.summary_token)
        if previous is None:
            deduplicated[summary.summary_token] = summary
            continue
        if previous.as_dict() != summary.as_dict():
            raise ValueError(
                f"Conflicting non-human project normalization for {summary.summary_token}"
            )
    return tuple(deduplicated[token] for token in sorted(deduplicated))


def _build_study_summaries(
    project_summaries: tuple[AdnaProjectSummary, ...],
) -> tuple[AdnaStudySummary, ...]:
    grouped: dict[str, list[AdnaProjectSummary]] = defaultdict(list)
    for summary in project_summaries:
        grouped[summary.study_token].append(summary)

    study_summaries: list[AdnaStudySummary] = []
    for study_token, group in grouped.items():
        ordered = tuple(sorted(group, key=lambda item: item.project_accession))
        lead = ordered[0]
        study_summaries.append(
            AdnaStudySummary(
                schema_version="adna-study-summary.v1",
                summary_token=study_token,
                species_latin_name=lead.species_latin_name,
                species_common_name=lead.species_common_name,
                project_accessions=tuple(item.project_accession for item in ordered),
                source_families=tuple(sorted({item.source_family for item in ordered})),
                archive_statuses=tuple(
                    sorted({item.archive_status for item in ordered})
                ),
                evidence_strengths=tuple(
                    sorted({item.evidence_strength for item in ordered})
                ),
                domestication_status=lead.domestication_status,
                paper_title=lead.paper_title,
                paper_doi=lead.paper_doi,
                sequencing_targets=tuple(
                    sorted(
                        {
                            item.sequencing_target
                            for item in ordered
                            if item.sequencing_target is not None
                        }
                    )
                ),
                material_bases=tuple(
                    sorted(
                        {
                            item.material_basis
                            for item in ordered
                            if item.material_basis is not None
                        }
                    )
                ),
                dating_bases=tuple(
                    sorted(
                        {
                            item.dating_basis
                            for item in ordered
                            if item.dating_basis is not None
                        }
                    )
                ),
                geographic_bases=tuple(
                    sorted(
                        {
                            item.geographic_basis
                            for item in ordered
                            if item.geographic_basis is not None
                        }
                    )
                ),
            )
        )
    return tuple(sorted(study_summaries, key=lambda item: item.summary_token))


def _build_lineage_records(
    species: AdnaSpeciesDefinition,
    project_summaries: tuple[AdnaProjectSummary, ...],
    study_summaries: tuple[AdnaStudySummary, ...],
) -> tuple[AdnaNormalizationLineage, ...]:
    lineages: list[AdnaNormalizationLineage] = []
    project_by_token = {project.summary_token: project for project in project_summaries}
    for project in project_summaries:
        lineages.append(
            AdnaNormalizationLineage(
                schema_version="adna-normalization-lineage.v1",
                output_record_kind="project_summary",
                output_record_token=project.summary_token,
                source_artifact_path=_source_artifact_path(species, project),
                source_accessions=(project.project_accession,),
                lineage_tokens=(
                    f"species:{species.latin_name}",
                    f"source_family:{project.source_family}",
                    f"project_accession:{project.project_accession}",
                    f"archive_status:{project.archive_status}",
                ),
            )
        )
    for study in study_summaries:
        first_project = project_by_token.get(
            f"{species.slug}:project:{study.project_accessions[0]}"
        )
        if first_project is None:
            raise ValueError(
                "Study summary references a project token missing from the normalization bundle"
            )
        lineages.append(
            AdnaNormalizationLineage(
                schema_version="adna-normalization-lineage.v1",
                output_record_kind="study_summary",
                output_record_token=study.summary_token,
                source_artifact_path=_source_artifact_path(species, first_project),
                source_accessions=study.project_accessions,
                lineage_tokens=(
                    f"species:{species.latin_name}",
                    f"study_token:{study.summary_token}",
                    *(
                        f"project_accession:{accession}"
                        for accession in study.project_accessions
                    ),
                ),
            )
        )
    return tuple(
        sorted(
            lineages,
            key=lambda item: (item.output_record_kind, item.output_record_token),
        )
    )


def _study_token_for(project_accession: str, paper_doi: str | None) -> str:
    if paper_doi:
        return "study:" + re.sub(r"[^a-z0-9]+", "-", paper_doi.casefold()).strip("-")
    return f"study:project:{project_accession.casefold()}"


def _review_strength_for(
    archive_status: str,
    curation_class: str,
    paper_doi: str | None,
) -> str:
    if curation_class == "comparator_only" or archive_status == "comparator_only":
        return "comparator_only"
    if paper_doi:
        return "primary_paper_pinned"
    return "archive_verified_needs_paper_pinning"


def _record_modality_for(project: AdnaArchiveProject) -> str:
    sequencing_target = (project.sequencing_target or "").casefold()
    if "mitogenome" in sequencing_target:
        return "mitogenome_only"
    if project.source_family == "GenBank":
        return "paper_only"
    return "archive_reads"


def _domestication_status_for(curation_class: str) -> str:
    if curation_class == "paper_pinned_core":
        return "domesticated_core"
    if curation_class == "comparator_only":
        return "comparator_only"
    if curation_class in {
        "genbank_only_or_non_project_archive",
        "weak_or_precuration",
    }:
        return "thin_evidence"
    return "unsupported"


def _support_class_for(project: AdnaArchiveProject, curation_class: str) -> str:
    if project.archive_status == "reject_or_out_of_scope":
        return "rejected_or_out_of_scope"
    if (
        curation_class == "comparator_only"
        or project.archive_status == "comparator_only"
    ):
        return "comparator_only"
    if project.domestication_scope == "wild_or_progenitor_context":
        return "wild_or_progenitor_context"
    if project.archive_status == "paper_pinned_core":
        return "domesticated_core_curated"
    return "archive_pending_paper_linkage"


def _paper_url_for(project: AdnaArchiveProject) -> str | None:
    if project.paper_linkage is None:
        return None
    if project.paper_linkage.doi:
        return f"https://doi.org/{project.paper_linkage.doi}"
    if project.paper_linkage.pmc_id:
        return f"https://pmc.ncbi.nlm.nih.gov/articles/{project.paper_linkage.pmc_id}/"
    if project.paper_linkage.pubmed_id:
        return f"https://pubmed.ncbi.nlm.nih.gov/{project.paper_linkage.pubmed_id}/"
    return None


def _interpretation_caveat_for(
    *,
    project: AdnaArchiveProject,
    support_class: str,
    project_context: AdnaProjectContext,
) -> str:
    caveats = [project.notes.strip()]

    if support_class == "archive_pending_paper_linkage":
        caveats.append(
            "Keep this project out of strong pollenomics interpretation until the primary paper linkage is encoded explicitly."
        )
    if support_class == "wild_or_progenitor_context":
        caveats.append(
            "Treat this as wild or progenitor context, not as direct domesticated-animal support."
        )
    if support_class == "comparator_only":
        caveats.append(
            "Use this only as comparator context and do not count it toward domesticated-core support."
        )
    if support_class == "rejected_or_out_of_scope":
        caveats.append(
            "Keep this row visible as a reject so archive presence does not masquerade as curated support."
        )

    if project_context.nordic_relevance == "nordic_relevant_unmapped":
        caveats.append(
            "Nordic-relevant lead remains unmapped in the shipped public atlas."
        )
    elif project_context.nordic_relevance == "nordic_adjacent":
        caveats.append(
            "Nordic-adjacent context does not justify a Nordic-localized project claim."
        )
    elif project_context.nordic_relevance == "non_nordic":
        caveats.append(
            "This project stays in the evidence base for comparative context, not as shipped Nordic evidence."
        )

    return " ".join(dict.fromkeys(part for part in caveats if part))


def _coordinate_policy_for(geographic_basis: str | None) -> str:
    basis = (geographic_basis or "").casefold()
    if "site_level" in basis:
        return "site_level_coordinates_expected"
    if "locality_text" in basis:
        return "locality_text_without_coordinates_allowed"
    if "country_only" in basis:
        return "country_only_withheld_coordinates_allowed"
    return "manual_coordinate_review_required"


def _chronology_policy_for(dating_basis: str | None) -> str:
    basis = (dating_basis or "").casefold()
    if "radiocarbon" in basis:
        return "bp_interval_expected"
    if "historical" in basis:
        return "historical_interval_or_label_allowed"
    if "archaeological" in basis:
        return "archaeological_period_label_allowed"
    if "mixed" in basis:
        return "mixed_chronology_review_required"
    return "manual_chronology_review_required"


def _breed_label_from_notes(notes: str) -> str | None:
    lowered = notes.casefold()
    if "przewalski" in lowered:
        return "przewalski-associated"
    if "dromedary" in lowered:
        return "dromedary-associated"
    return None


def _source_artifact_path(
    species: AdnaSpeciesDefinition,
    project: AdnaProjectSummary,
) -> str:
    root = f"{ADNA_SPECIES_DIR}/{species.slug}/raw"
    family = project.source_family.casefold()
    suffix = "filereport.tsv"
    if family == "genbank":
        suffix = "summary.tsv"
    if family == "manual_curation":
        suffix = "review.md"
    return f"{root}/{family}/{project.project_accession}.{suffix}"
