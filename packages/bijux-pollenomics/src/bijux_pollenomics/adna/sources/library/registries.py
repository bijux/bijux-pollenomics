"""aDNA project, paper, supplement, and source-bundle registries."""

from __future__ import annotations

from functools import cache
import json
from pathlib import Path
import re
import zipfile
from bijux_pollenomics.adna.workflow.paths import (
    ADNA_SOURCE_LIBRARY_DIR,
)
from bijux_pollenomics.adna.sources.archive import (
    AdnaArchiveProject,
    build_archive_project_catalog,
    classify_archive_project_evidence,
)
from .models import (
    AdnaPaperRegistryRow,
    AdnaProjectRegistryRow,
    AdnaSourceArtifact,
    AdnaSourceBundleManifest,
    AdnaSupplementRegistryRow,
    _PaperSourceSpec,
    _ProjectIntakeExpectation,
    _ReferenceStashRecord,
    _empty_reference_stash_record,
)
from .specifications import (
    _derive_ingestion_status,
    _doi_slug,
    _paper_required,
    _paper_source_spec,
    _supplement_required,
)
from .storage import (
    _iter_materialized_artifacts,
    _local_reference_article_status,
    _local_reference_supplement_status,
    _reference_stash_records,
    _source_library_cache_key,
    build_source_artifact_index,
)


def build_project_source_bundles(
    output_root: Path,
) -> tuple[AdnaSourceBundleManifest, ...]:
    """Return one per-project manifest describing local paper and supplement support."""
    output_root = Path(output_root)
    artifacts_by_project: dict[str, list[AdnaSourceArtifact]] = {}
    for artifact in _iter_materialized_artifacts(output_root):
        for accession in artifact.project_accessions:
            artifacts_by_project.setdefault(accession, []).append(artifact)

    bundles: list[AdnaSourceBundleManifest] = []
    for project in build_archive_project_catalog():
        project_artifacts = tuple(
            sorted(
                artifacts_by_project.get(project.project_accession, ()),
                key=lambda item: item.artifact_id,
            )
        )
        local_project_artifacts = tuple(
            item for item in project_artifacts if item.fetch_status == "archived"
        )
        paper_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind
            in {"article_html", "article_pdf", "paper_metadata_json"}
        )
        supplement_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind.startswith("supplementary_")
        )
        paper_required = _paper_required(project.archive_status)
        supplement_required = _supplement_required(project)
        blockers = []
        if paper_required and not paper_artifacts:
            blockers.append("missing_local_paper_evidence")
        if supplement_required and not supplement_artifacts:
            blockers.append("missing_local_supplementary_material")
        if project.paper_linkage is None:
            blockers.append("paper_linkage_not_curated")
        bundles.append(
            AdnaSourceBundleManifest(
                project_accession=project.project_accession,
                species_latin_name=project.species_latin_name,
                archive_status=project.archive_status,
                evidence_strength=classify_archive_project_evidence(project),
                project_url=project.metadata_url,
                paper_doi=None
                if project.paper_linkage is None
                else project.paper_linkage.doi,
                paper_title=(
                    None
                    if project.paper_linkage is None
                    else project.paper_linkage.paper_title
                ),
                archive_metadata_sufficient=not paper_required,
                paper_required=paper_required,
                supplement_required=supplement_required,
                paper_download_status=_fold_fetch_status(paper_artifacts),
                supplement_download_status=_fold_fetch_status(supplement_artifacts),
                local_artifact_ids=tuple(
                    item.artifact_id for item in local_project_artifacts
                ),
                local_artifact_paths=tuple(
                    item.local_path for item in local_project_artifacts
                ),
                blockers=tuple(blockers),
            )
        )
    return tuple(sorted(bundles, key=lambda item: item.project_accession))


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


def _paper_sample_extractability(
    spec: _PaperSourceSpec,
    *,
    supplementary_download_status: str,
    supplement_artifacts: tuple[AdnaSourceArtifact, ...],
    supplement_parse_status: str,
    stash_record: _ReferenceStashRecord,
) -> str:
    if spec.sample_extractability != "manual_curation_required":
        return spec.sample_extractability
    if spec.supplementary_assets or (
        supplementary_download_status == "archived" and supplement_artifacts
    ):
        return "supplement_extractable"
    if supplement_parse_status in {
        "repository_supplement_archived",
        "zip_member_inventory_published",
    }:
        return "supplement_archived_needs_extraction"
    if supplement_parse_status in {
        "local_structured_tables_staged",
        "local_supplement_staged",
    } or stash_record.get("supplementary_assets"):
        return "supplement_known_needs_repo_ingestion"
    if spec.parsing_status == "full_paper_download_blocked":
        return "full_paper_capture_blocked"
    if spec.article_kind == "article_html":
        return "article_extractable"
    return "manual_curation_required"


def _paper_expected_supplementary_artifacts(
    spec: _PaperSourceSpec,
    supplement_artifacts: tuple[AdnaSourceArtifact, ...],
) -> tuple[str, ...]:
    if spec.supplementary_assets:
        return tuple(
            f"{ADNA_SOURCE_LIBRARY_DIR}/{item.relative_path}"
            for item in spec.supplementary_assets
        )
    return tuple(sorted(item.local_path for item in supplement_artifacts))


def _expected_supplementary_file_families(
    spec: _PaperSourceSpec,
    stash_record: _ReferenceStashRecord,
) -> tuple[str, ...]:
    families: set[str] = set()
    for asset in spec.supplementary_assets:
        families.add(_supplementary_file_family_from_name(asset.relative_path))
    for asset_name in stash_record.get("supplementary_assets", ()):
        families.add(_supplementary_file_family_from_name(str(asset_name)))
    return tuple(sorted(family for family in families if family))


def _paper_sample_identifier_targets(
    spec: _PaperSourceSpec,
    expected_supplementary_artifacts: tuple[str, ...],
) -> tuple[str, ...]:
    if spec.sample_identifier_targets:
        return spec.sample_identifier_targets
    if expected_supplementary_artifacts:
        return expected_supplementary_artifacts
    return (spec.article_local_path,)


def _paper_sample_site_targets(
    spec: _PaperSourceSpec,
    expected_supplementary_artifacts: tuple[str, ...],
) -> tuple[str, ...]:
    if spec.sample_site_targets:
        return spec.sample_site_targets
    if expected_supplementary_artifacts:
        return expected_supplementary_artifacts
    return (spec.article_local_path,)


def _paper_chronology_targets(
    spec: _PaperSourceSpec,
    expected_supplementary_artifacts: tuple[str, ...],
) -> tuple[str, ...]:
    if spec.chronology_targets:
        return spec.chronology_targets
    if expected_supplementary_artifacts:
        return expected_supplementary_artifacts
    return (spec.article_local_path,)


def build_supplement_registry(
    output_root: Path,
) -> tuple[AdnaSupplementRegistryRow, ...]:
    """Return the supplementary-material registry."""
    rows: list[AdnaSupplementRegistryRow] = []
    for artifact in build_source_artifact_index(output_root):
        if not artifact.artifact_kind.startswith("supplementary_"):
            continue
        rows.append(
            AdnaSupplementRegistryRow(
                artifact_id=artifact.artifact_id,
                paper_doi=artifact.paper_doi or "",
                source_url=artifact.source_url,
                local_path=artifact.local_path,
                artifact_kind=artifact.artifact_kind,
                fetch_status=artifact.fetch_status,
                project_accessions=artifact.project_accessions,
                purpose="sample_or_site_support",
            )
        )
    return tuple(sorted(rows, key=lambda item: item.artifact_id))


def build_supplement_zip_member_registry(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    """Return the tracked member inventory for archived supplementary zip bundles."""
    return _build_supplement_zip_member_registry_cached(
        _source_library_cache_key(output_root)
    )


def _build_supplement_zip_member_registry_uncached(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    output_root = Path(output_root)
    rows: list[dict[str, object]] = []
    for artifact in build_source_artifact_index(output_root):
        if artifact.artifact_kind != "supplementary_zip":
            continue
        local_path = output_root / artifact.local_path
        if not local_path.is_file():
            continue
        try:
            with zipfile.ZipFile(local_path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    rows.append(
                        {
                            "paper_doi": artifact.paper_doi,
                            "parent_artifact_id": artifact.artifact_id,
                            "zip_local_path": artifact.local_path,
                            "member_name": member.filename,
                            "member_local_path": f"{artifact.local_path}#{member.filename}",
                            "member_byte_size": member.file_size,
                            "inferred_purpose": _infer_zip_member_purpose(
                                member.filename
                            ),
                        }
                    )
        except zipfile.BadZipFile:
            rows.append(
                {
                    "paper_doi": artifact.paper_doi,
                    "parent_artifact_id": artifact.artifact_id,
                    "zip_local_path": artifact.local_path,
                    "member_name": "",
                    "member_local_path": artifact.local_path,
                    "member_byte_size": None,
                    "inferred_purpose": "invalid_zip_bundle",
                }
            )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item.get("paper_doi", "")),
                str(item.get("zip_local_path", "")),
                str(item.get("member_name", "")),
            ),
        )
    )


@cache
def _build_supplement_zip_member_registry_cached(
    output_root_key: str,
) -> tuple[dict[str, object], ...]:
    return _build_supplement_zip_member_registry_uncached(Path(output_root_key))


def _infer_zip_member_purpose(member_name: str) -> str:
    lowered = member_name.lower()
    if lowered.endswith((".xlsx", ".xls", ".csv", ".tsv")):
        return "structured_table_candidate"
    if lowered.endswith(".pdf"):
        return "supplementary_pdf_note"
    if lowered.endswith((".txt", ".md")):
        return "readme_or_plaintext_note"
    if lowered.endswith((".fasta", ".fa", ".fq", ".fastq", ".bam")):
        return "sequence_or_alignment_payload"
    return "unclassified_bundle_member"


def _paper_manifest_rows(
    output_root: Path,
    doi: str,
) -> tuple[dict[str, object], ...]:
    output_root = Path(output_root)
    artifact_rows = [
        artifact
        for artifact in build_source_artifact_index(output_root)
        if artifact.paper_doi == doi
    ]
    member_rows = [
        row
        for row in build_supplement_zip_member_registry(output_root)
        if row["paper_doi"] == doi
    ]
    rows: list[dict[str, object]] = []
    for artifact in artifact_rows:
        rows.append(
            {
                "row_kind": "archived_asset",
                "paper_doi": doi,
                "artifact_id": artifact.artifact_id,
                "artifact_kind": artifact.artifact_kind,
                "label": artifact.label,
                "source_url": artifact.source_url,
                "local_path": artifact.local_path,
                "fetch_status": artifact.fetch_status,
                "content_type": artifact.content_type,
                "byte_size": artifact.byte_size,
                "member_name": "",
                "member_local_path": "",
                "inferred_purpose": artifact.remote_note,
            }
        )
    rows.extend(
        {
            "row_kind": "zip_member",
            "paper_doi": doi,
            "artifact_id": row["parent_artifact_id"],
            "artifact_kind": "supplementary_zip_member",
            "label": row["member_name"],
            "source_url": "",
            "local_path": row["zip_local_path"],
            "fetch_status": "archived",
            "content_type": "",
            "byte_size": row["member_byte_size"],
            "member_name": row["member_name"],
            "member_local_path": row["member_local_path"],
            "inferred_purpose": row["inferred_purpose"],
        }
        for row in member_rows
    )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item["row_kind"]),
                str(item["local_path"]),
                str(item["member_name"]),
            ),
        )
    )


def _article_readability_status(
    spec: _PaperSourceSpec, article_download_status: str
) -> str:
    if article_download_status == "missing":
        return "missing"
    if article_download_status == "partial":
        return "partial_capture"
    if spec.parsing_status == "full_paper_download_blocked":
        return "blocked_landing_page_only"
    if spec.article_kind == "article_pdf":
        return "readable_pdf"
    if spec.article_kind == "article_html":
        return "readable_html"
    return "readable_article"


def _supplement_parse_status(
    output_root: Path,
    doi: str,
    *,
    supplementary_download_status: str,
    stash_record: _ReferenceStashRecord,
) -> str:
    if supplementary_download_status == "archived":
        member_rows = [
            row
            for row in build_supplement_zip_member_registry(output_root)
            if row["paper_doi"] == doi
        ]
        if any(
            str(row.get("inferred_purpose", "")) == "structured_table_candidate"
            for row in member_rows
        ):
            return "zip_member_inventory_published"
        return "repository_supplement_archived"
    if supplementary_download_status == "partial":
        return "repository_supplement_partial"
    if int(stash_record.get("structured_table_count", 0)) > 0:
        return "local_structured_tables_staged"
    if stash_record.get("supplementary_assets"):
        return "local_supplement_staged"
    return "missing"


def _supplementary_verification_status(
    *,
    supplementary_download_status: str,
    stash_record: _ReferenceStashRecord,
) -> str:
    if supplementary_download_status == "archived":
        return "supplement_archived_in_repo"
    if stash_record.get("supplementary_assets"):
        return "supplement_verified_in_local_reference_stash"
    return "supplement_not_verified_yet"


def _project_sample_table_extraction_status(
    output_root: Path, project_accession: str
) -> str:
    path = (
        Path(output_root)
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / project_accession
        / "sample_master.json"
    )
    if not path.is_file():
        return "not_published"
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
    if rows:
        return "project_sample_master_published"
    return "published_empty"


def _paper_sample_table_extraction_status(
    output_root: Path,
    project_accessions: tuple[str, ...],
) -> str:
    statuses = {
        _project_sample_table_extraction_status(output_root, accession)
        for accession in project_accessions
    }
    if "project_sample_master_published" in statuses:
        return "project_sample_master_published"
    if "published_empty" in statuses:
        return "published_empty"
    return "not_published"


def _paper_evidence_acquisition_state(
    *,
    article_download_status: str,
    supplementary_download_status: str,
    supplement_parse_status: str,
    local_reference_supplement_status: str,
    sample_table_extraction_status: str,
    parsing_status: str,
) -> str:
    if sample_table_extraction_status == "project_sample_master_published":
        return "sample_tables_published"
    if supplementary_download_status == "archived":
        return "repository_supplement_captured_needs_extraction"
    if local_reference_supplement_status == "local_reference_staged":
        return "local_supplement_staged_needs_repo_ingestion"
    if article_download_status == "archived":
        return "article_captured_needs_supplement_or_extraction"
    if article_download_status == "partial":
        return "article_capture_partial"
    if parsing_status == "full_paper_download_blocked":
        return "full_paper_capture_blocked"
    if supplement_parse_status == "missing":
        return "missing_capture"
    return "manual_curation_required"


def _supplementary_file_family_from_name(name: str) -> str:
    lowered = name.lower()
    if lowered.endswith(".zip"):
        return "zip_bundle"
    if lowered.endswith((".xlsx", ".xls")):
        return "xlsx_table"
    if lowered.endswith(".csv"):
        return "csv_table"
    if lowered.endswith(".tsv"):
        return "tsv_table"
    if lowered.endswith(".pdf"):
        return "pdf_appendix"
    if lowered.endswith(".docx"):
        return "docx_appendix"
    if lowered.endswith((".jpg", ".jpeg", ".png")):
        return "image_appendix"
    if lowered.endswith(".xml"):
        return "xml_payload"
    if lowered.endswith(".nwk"):
        return "tree_payload"
    return "other_payload"


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


def _fold_fetch_status(artifacts: tuple[AdnaSourceArtifact, ...]) -> str:
    if not artifacts:
        return "missing"
    statuses = {item.fetch_status for item in artifacts}
    if statuses == {"archived"}:
        return "archived"
    if "archived" in statuses:
        return "partial"
    return "missing"
