"""Project registry construction and intake expectations."""

from __future__ import annotations

import re
from functools import cache
from pathlib import Path

from bijux_pollenomics.adna.sources.archive import (
    AdnaArchiveProject,
    build_archive_project_catalog,
    classify_archive_project_evidence,
)
from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from ..models import (
    AdnaPaperRegistryRow,
    AdnaProjectRegistryRow,
    AdnaSourceBundleManifest,
    _empty_reference_stash_record,
    _ProjectIntakeExpectation,
)
from ..specifications import _derive_ingestion_status, _paper_source_spec
from ..storage import _source_library_cache_key
from .bundles import build_project_source_bundles
from .paper_evidence import (
    _paper_sample_extractability,
    _project_sample_table_extraction_status,
)
from .papers import build_paper_registry


def _accession_range_sample_count(project_accession: str) -> int | None:
    match = re.fullmatch(r"([A-Z]+)(\d+)-([A-Z]+)(\d+)", project_accession)
    if match is None:
        return None
    left_prefix, left_value, right_prefix, right_value = match.groups()
    if left_prefix != right_prefix:
        return None
    return int(right_value) - int(left_value) + 1


def _project_intake_expectation(
    project: AdnaArchiveProject,
) -> _ProjectIntakeExpectation:
    default_artifact_path = f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/archive_metadata.html"
    paper_spec = None
    if project.paper_linkage is not None and project.paper_linkage.doi is not None:
        paper_spec = _paper_source_spec(project.paper_linkage.doi)

    if project.archive_status == "reject_or_out_of_scope":
        return _ProjectIntakeExpectation(
            expected_sample_count=_accession_range_sample_count(
                project.project_accession
            )
            if project.accession_scope == "accession_range"
            else (1 if project.accession_scope == "sample" else None),
            expected_sample_count_status=(
                "known_from_archive_accession_scope"
                if project.accession_scope in {"sample", "accession_range"}
                else "not_yet_curated"
            ),
            expected_sample_count_provenance=(
                "Archive-native accession scope implies the current expected sample count."
                if project.accession_scope in {"sample", "accession_range"}
                else "Rejected or out-of-scope projects stay in the intake inventory but do not yet carry a curated sample-count claim."
            ),
            expected_sample_count_artifact_path=default_artifact_path,
            sample_identifier_status=(
                "archive_native_identifiers_known"
                if project.accession_scope in {"sample", "accession_range"}
                else "not_yet_curated"
            ),
            inventory_disposition="retained_rejected_reference",
            rejection_reason=project.notes,
            extraction_plan=(
                "Retain the project in the tracked inventory with an explicit rejection reason so future readers can see why it does not feed the animal sample database."
            ),
        )

    if project.accession_scope == "sample":
        return _ProjectIntakeExpectation(
            expected_sample_count=1,
            expected_sample_count_status="known_from_archive_accession_scope",
            expected_sample_count_provenance="The tracked accession itself is one sample-scoped archive identifier.",
            expected_sample_count_artifact_path=default_artifact_path,
            sample_identifier_status="archive_native_identifiers_known",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Use the archive-native sample accession as the anchor row, then recover site and chronology support from the linked paper or supplementary material."
            ),
        )

    accession_range_count = _accession_range_sample_count(project.project_accession)
    if accession_range_count is not None:
        return _ProjectIntakeExpectation(
            expected_sample_count=accession_range_count,
            expected_sample_count_status="known_from_archive_accession_scope",
            expected_sample_count_provenance="The tracked accession range implies a finite set of archive-native sample identifiers.",
            expected_sample_count_artifact_path=default_artifact_path,
            sample_identifier_status="archive_native_identifiers_known",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Preserve each archive-native accession in the sample master and reconcile it against paper-native labels once supplementary or article-level sample tables are parsed."
            ),
        )

    if paper_spec is not None and _paper_sample_extractability(
        paper_spec,
        supplementary_download_status="missing",
        supplement_artifacts=(),
        supplement_parse_status="missing",
        stash_record=_empty_reference_stash_record(),
    ) in {
        "article_extractable",
        "supplement_extractable",
    }:
        target_text = "; ".join(
            paper_spec.sample_identifier_targets
            or paper_spec.sample_site_targets
            or paper_spec.chronology_targets
        )
        return _ProjectIntakeExpectation(
            expected_sample_count=None,
            expected_sample_count_status="not_yet_curated",
            expected_sample_count_provenance=(
                "The project is paper-pinned, but the expected sample count still needs to be recovered from the listed article or supplementary targets."
            ),
            expected_sample_count_artifact_path=target_text,
            sample_identifier_status="paper_or_supplement_targets_curated",
            inventory_disposition="tracked_intake_candidate",
            rejection_reason="",
            extraction_plan=(
                "Extract the project sample master from the curated article or supplementary targets and then reconcile sample identifiers against any archive-native labels."
            ),
            blocker_categories=("missing_sample_identifiers",),
        )

    blocker_categories: tuple[str, ...] = ("missing_paper_capture",)
    if paper_spec is not None:
        blocker_categories = ("missing_readable_tables", "missing_sample_identifiers")
    return _ProjectIntakeExpectation(
        expected_sample_count=None,
        expected_sample_count_status="not_yet_curated",
        expected_sample_count_provenance=(
            "No trustworthy expected sample count is published yet because the current archive or paper capture is still too weak."
        ),
        expected_sample_count_artifact_path=default_artifact_path,
        sample_identifier_status=(
            "missing_primary_paper_linkage"
            if project.paper_linkage is None
            else "manual_curation_required"
        ),
        inventory_disposition="tracked_intake_candidate",
        rejection_reason="",
        extraction_plan=(
            "Strengthen the paper and supplementary capture first, then recover sample identifiers from the strongest readable table or appendix surface."
        ),
        blocker_categories=blocker_categories,
    )


def build_project_registry(output_root: Path) -> tuple[AdnaProjectRegistryRow, ...]:
    """Return the master cross-species project registry."""
    return _build_project_registry_cached(_source_library_cache_key(output_root))


def _build_project_registry_uncached(
    output_root: Path,
) -> tuple[AdnaProjectRegistryRow, ...]:
    output_root = Path(output_root)
    bundles = {
        bundle.project_accession: bundle
        for bundle in build_project_source_bundles(output_root)
    }
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    rows: list[AdnaProjectRegistryRow] = []
    for project in build_archive_project_catalog():
        bundle = bundles[project.project_accession]
        expectation = _project_intake_expectation(project)
        paper_url = None
        paper_row = None
        if project.paper_linkage is not None and project.paper_linkage.doi is not None:
            paper_url = f"https://doi.org/{project.paper_linkage.doi}"
            paper_row = paper_rows.get(project.paper_linkage.doi)
        rows.append(
            AdnaProjectRegistryRow(
                species_latin_name=project.species_latin_name,
                project_accession=project.project_accession,
                source_family=project.source_family,
                archive_status=project.archive_status,
                evidence_strength=classify_archive_project_evidence(project),
                accession_scope=project.accession_scope,
                project_url=project.metadata_url,
                primary_paper_doi=None
                if project.paper_linkage is None
                else project.paper_linkage.doi,
                primary_paper_url=paper_url,
                source_bundle_path=(
                    f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project.project_accession}/bundle_manifest.json"
                ),
                paper_download_status=bundle.paper_download_status,
                article_readability_status=(
                    "no_linked_paper"
                    if paper_row is None
                    else paper_row.article_readability_status
                ),
                supplement_download_status=bundle.supplement_download_status,
                supplement_parse_status=(
                    "not_applicable"
                    if paper_row is None
                    else paper_row.supplement_parse_status
                ),
                local_reference_article_status=(
                    "missing"
                    if paper_row is None
                    else paper_row.local_reference_article_status
                ),
                local_reference_supplement_status=(
                    "missing"
                    if paper_row is None
                    else paper_row.local_reference_supplement_status
                ),
                sample_table_extraction_status=_project_sample_table_extraction_status(
                    output_root,
                    project.project_accession,
                ),
                evidence_acquisition_state=_project_evidence_acquisition_state(
                    bundle=bundle,
                    project_accession=project.project_accession,
                    paper_row=paper_row,
                    inventory_disposition=expectation.inventory_disposition,
                    output_root=output_root,
                ),
                ingestion_status=_derive_ingestion_status(bundle),
                expected_sample_count=expectation.expected_sample_count,
                expected_sample_count_status=expectation.expected_sample_count_status,
                expected_sample_count_provenance=expectation.expected_sample_count_provenance,
                expected_sample_count_artifact_path=expectation.expected_sample_count_artifact_path,
                sample_identifier_status=expectation.sample_identifier_status,
                inventory_disposition=expectation.inventory_disposition,
                rejection_reason=expectation.rejection_reason,
            )
        )
    return tuple(
        sorted(rows, key=lambda item: (item.species_latin_name, item.project_accession))
    )


@cache
def _build_project_registry_cached(
    output_root_key: str,
) -> tuple[AdnaProjectRegistryRow, ...]:
    return _build_project_registry_uncached(Path(output_root_key))


def _project_evidence_acquisition_state(
    *,
    bundle: AdnaSourceBundleManifest,
    project_accession: str,
    paper_row: AdnaPaperRegistryRow | None,
    inventory_disposition: str,
    output_root: Path,
) -> str:
    if inventory_disposition == "retained_rejected_reference":
        return "scope_rejected"
    if paper_row is None:
        return "paper_linkage_not_curated"
    sample_table_status = _project_sample_table_extraction_status(
        output_root, project_accession
    )
    if sample_table_status == "project_sample_master_published":
        return "sample_tables_published"
    if bundle.supplement_download_status == "archived":
        return "repository_supplement_captured_needs_extraction"
    if paper_row.local_reference_supplement_status == "local_reference_staged":
        return "local_supplement_staged_needs_repo_ingestion"
    if bundle.paper_download_status == "archived":
        return "paper_captured_needs_supplement_or_extraction"
    if bundle.paper_download_status == "partial":
        return "paper_capture_partial"
    return "missing_capture"
