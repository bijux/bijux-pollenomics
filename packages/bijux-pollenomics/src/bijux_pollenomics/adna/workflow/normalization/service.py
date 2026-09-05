"""Species normalization orchestration."""

from __future__ import annotations
from bijux_pollenomics.adna.governance.curation import build_species_curation_manifest
from bijux_pollenomics.adna.workflow.manifests import (
    build_species_manifest,
)
from ...projects.evidence.coordinates import build_species_coordinate_provenance_rows
from ...projects.evidence.sites import build_species_site_evidence_rows

from .localities import build_species_project_locality_records
from .models import AdnaSpeciesNormalizationBundle
from .projects import (
    _build_lineage_records,
    _build_study_summaries,
    _normalize_project_summaries,
)
from .samples import _build_sample_records


def build_species_normalization_bundle(
    species_name: str,
) -> AdnaSpeciesNormalizationBundle:
    """Build the deterministic non-human normalization bundle for one species."""
    species_manifest = build_species_manifest(species_name)
    if species_manifest.species.latin_name == "Homo sapiens":
        raise ValueError(
            "Homo sapiens normalization is owned by the governed AADR metadata runtime"
        )
    curation_manifest = build_species_curation_manifest(species_name)
    project_summaries, project_refusals = _normalize_project_summaries(
        species_name,
        curation_manifest.curation_class,
    )
    sample_records, sample_refusals = _build_sample_records(
        species_name, project_summaries
    )
    coordinate_provenance_records = build_species_coordinate_provenance_rows(
        tuple(project.project_accession for project in project_summaries)
    )
    site_evidence_records = build_species_site_evidence_rows(
        tuple(project.project_accession for project in project_summaries)
    )
    locality_records, locality_refusals = build_species_project_locality_records(
        species_name,
        project_summaries,
    )
    study_summaries = _build_study_summaries(project_summaries)
    lineage_records = _build_lineage_records(
        species_manifest.species,
        project_summaries,
        study_summaries,
    )
    return AdnaSpeciesNormalizationBundle(
        schema_version="adna-nonhuman-normalization-bundle.v1",
        species_manifest=species_manifest,
        sample_records=sample_records,
        coordinate_provenance_records=coordinate_provenance_records,
        site_evidence_records=site_evidence_records,
        locality_records=locality_records,
        project_summaries=project_summaries,
        study_summaries=study_summaries,
        lineage_records=lineage_records,
        refusals=project_refusals + sample_refusals + locality_refusals,
        normalization_scope=(
            "Non-human normalization admits only recovered, final sample identities, "
            "plus project summaries, study summaries, and curated locality summaries. "
            "Pending and rejected placeholder rows remain source-native accounting and "
            "reasoned refusals; they are not normalized sample evidence."
        ),
    )
