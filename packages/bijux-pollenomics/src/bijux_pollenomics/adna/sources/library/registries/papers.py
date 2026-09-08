"""Paper registry construction."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from bijux_pollenomics.adna.sources.archive import (
    AdnaArchiveProject,
    build_archive_project_catalog,
)
from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from ..models import (
    AdnaPaperRegistryRow,
    AdnaSourceArtifact,
    _empty_reference_stash_record,
)
from ..specifications import _doi_slug, _paper_source_spec
from ..storage import (
    _local_reference_article_status,
    _local_reference_supplement_status,
    _reference_stash_records,
    _source_library_cache_key,
    build_source_artifact_index,
)
from .bundles import _fold_fetch_status
from .paper_evidence import (
    _article_readability_status,
    _expected_supplementary_file_families,
    _paper_chronology_targets,
    _paper_evidence_acquisition_state,
    _paper_expected_supplementary_artifacts,
    _paper_sample_extractability,
    _paper_sample_identifier_targets,
    _paper_sample_site_targets,
    _paper_sample_table_extraction_status,
    _supplement_parse_status,
    _supplementary_verification_status,
)


def build_paper_registry(output_root: Path) -> tuple[AdnaPaperRegistryRow, ...]:
    """Return the master unique-paper registry."""
    return _build_paper_registry_cached(_source_library_cache_key(output_root))


def _build_paper_registry_uncached(
    output_root: Path,
) -> tuple[AdnaPaperRegistryRow, ...]:
    output_root = Path(output_root)
    artifacts = build_source_artifact_index(output_root)
    artifacts_by_doi: dict[str, list[AdnaSourceArtifact]] = {}
    projects_by_doi: dict[str, list[AdnaArchiveProject]] = {}
    for project in build_archive_project_catalog():
        if project.paper_linkage is None or project.paper_linkage.doi is None:
            continue
        projects_by_doi.setdefault(project.paper_linkage.doi, []).append(project)
    for artifact in artifacts:
        if artifact.paper_doi is None:
            continue
        artifacts_by_doi.setdefault(artifact.paper_doi, []).append(artifact)

    rows: list[AdnaPaperRegistryRow] = []
    for doi, projects in sorted(projects_by_doi.items()):
        first = projects[0]
        linkage = first.paper_linkage
        if linkage is None:
            raise ValueError(
                f"Paper registry cannot render DOI {doi} without a curated paper linkage"
            )
        spec = _paper_source_spec(doi)
        stash_record = _reference_stash_records(output_root).get(
            _doi_slug(doi), _empty_reference_stash_record()
        )
        doi_artifacts = tuple(artifacts_by_doi.get(doi, ()))
        article_artifacts = tuple(
            item
            for item in doi_artifacts
            if item.artifact_kind
            in {"article_html", "article_pdf", "paper_metadata_json"}
        )
        supplement_artifacts = tuple(
            item
            for item in doi_artifacts
            if item.artifact_kind.startswith("supplementary_")
        )
        article_download_status = _fold_fetch_status(article_artifacts)
        supplementary_download_status = _fold_fetch_status(supplement_artifacts)
        supplement_parse_status = _supplement_parse_status(
            output_root,
            doi,
            supplementary_download_status=supplementary_download_status,
            stash_record=stash_record,
        )
        expected_supplementary_artifacts = _paper_expected_supplementary_artifacts(
            spec,
            supplement_artifacts,
        )
        sample_table_extraction_status = _paper_sample_table_extraction_status(
            output_root,
            tuple(sorted(project.project_accession for project in projects)),
        )
        rows.append(
            AdnaPaperRegistryRow(
                paper_doi=doi,
                canonical_url=f"https://doi.org/{doi}",
                article_source_url=spec.article_source_url,
                journal=linkage.journal_title,
                publication_year=linkage.publication_year,
                title=linkage.paper_title,
                species_latin_names=tuple(
                    sorted({project.species_latin_name for project in projects})
                ),
                project_accessions=tuple(
                    sorted(project.project_accession for project in projects)
                ),
                article_download_status=article_download_status,
                article_readability_status=_article_readability_status(
                    spec,
                    article_download_status,
                ),
                article_local_path=spec.article_local_path,
                supplementary_download_status=supplementary_download_status,
                supplement_parse_status=supplement_parse_status,
                supplementary_verification_status=_supplementary_verification_status(
                    supplementary_download_status=supplementary_download_status,
                    stash_record=stash_record,
                ),
                local_reference_article_status=_local_reference_article_status(
                    stash_record
                ),
                local_reference_supplement_status=_local_reference_supplement_status(
                    stash_record
                ),
                supplementary_count=len(supplement_artifacts),
                parsing_status=spec.parsing_status,
                sample_extractability=_paper_sample_extractability(
                    spec,
                    supplementary_download_status=supplementary_download_status,
                    supplement_artifacts=supplement_artifacts,
                    supplement_parse_status=supplement_parse_status,
                    stash_record=stash_record,
                ),
                sample_table_extraction_status=sample_table_extraction_status,
                evidence_acquisition_state=_paper_evidence_acquisition_state(
                    article_download_status=article_download_status,
                    supplementary_download_status=supplementary_download_status,
                    supplement_parse_status=supplement_parse_status,
                    local_reference_supplement_status=_local_reference_supplement_status(
                        stash_record
                    ),
                    sample_table_extraction_status=sample_table_extraction_status,
                    parsing_status=spec.parsing_status,
                ),
                expected_supplementary_file_families=_expected_supplementary_file_families(
                    spec,
                    stash_record,
                ),
                expected_supplementary_artifacts=expected_supplementary_artifacts,
                sample_identifier_targets=_paper_sample_identifier_targets(
                    spec,
                    expected_supplementary_artifacts,
                ),
                sample_site_targets=_paper_sample_site_targets(
                    spec,
                    expected_supplementary_artifacts,
                ),
                chronology_targets=_paper_chronology_targets(
                    spec,
                    expected_supplementary_artifacts,
                ),
                supplementary_manifest_path=(
                    f"{ADNA_SOURCE_LIBRARY_DIR}/papers/{_doi_slug(doi)}/supplementary_manifest.json"
                ),
                supplementary_acquisition_checklist_path=(
                    f"{ADNA_SOURCE_LIBRARY_DIR}/supplement_acquisition_checklist.json"
                ),
            )
        )
    return tuple(rows)


@cache
def _build_paper_registry_cached(
    output_root_key: str,
) -> tuple[AdnaPaperRegistryRow, ...]:
    return _build_paper_registry_uncached(Path(output_root_key))
