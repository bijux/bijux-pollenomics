"""aDNA source-library records, specifications, and capture states."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import TypedDict


class _ReferenceStashRecord(TypedDict):
    stash_slug: str
    article_formats: tuple[str, ...]
    supplementary_assets: tuple[str, ...]
    structured_table_count: int
    archive_bundle_count: int


class _ReferenceStashDraft(TypedDict):
    stash_slug: str
    article_formats: set[str]
    supplementary_assets: list[str]
    structured_table_count: int
    archive_bundle_count: int


def _empty_reference_stash_record() -> _ReferenceStashRecord:
    return {
        "stash_slug": "",
        "article_formats": (),
        "supplementary_assets": (),
        "structured_table_count": 0,
        "archive_bundle_count": 0,
    }


@dataclass(frozen=True)
class AdnaSourceArtifact:
    """One tracked source artifact backing a paper, supplement, or metadata claim."""

    artifact_id: str
    artifact_kind: str
    label: str
    source_url: str
    local_path: str
    fetch_status: str
    remote_note: str
    project_accessions: tuple[str, ...]
    paper_doi: str | None = None
    content_type: str | None = None
    byte_size: int | None = None
    storage_path: str | None = None
    storage_byte_size: int | None = None
    content_encoding: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
            "label": self.label,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "fetch_status": self.fetch_status,
            "remote_note": self.remote_note,
            "project_accessions": list(self.project_accessions),
            "paper_doi": self.paper_doi,
            "content_type": self.content_type,
            "byte_size": self.byte_size,
            "storage_path": self.storage_path,
            "storage_byte_size": self.storage_byte_size,
            "content_encoding": self.content_encoding,
        }


@dataclass(frozen=True)
class AdnaProjectRegistryRow:
    """Cross-species registry row for one tracked animal aDNA project or accession."""

    species_latin_name: str
    project_accession: str
    source_family: str
    archive_status: str
    evidence_strength: str
    accession_scope: str
    project_url: str
    primary_paper_doi: str | None
    primary_paper_url: str | None
    source_bundle_path: str
    paper_download_status: str
    article_readability_status: str
    supplement_download_status: str
    supplement_parse_status: str
    local_reference_article_status: str
    local_reference_supplement_status: str
    sample_table_extraction_status: str
    evidence_acquisition_state: str
    ingestion_status: str
    expected_sample_count: int | None
    expected_sample_count_status: str
    expected_sample_count_provenance: str
    expected_sample_count_artifact_path: str
    sample_identifier_status: str
    inventory_disposition: str
    rejection_reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "source_family": self.source_family,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "accession_scope": self.accession_scope,
            "project_url": self.project_url,
            "primary_paper_doi": self.primary_paper_doi,
            "primary_paper_url": self.primary_paper_url,
            "source_bundle_path": self.source_bundle_path,
            "paper_download_status": self.paper_download_status,
            "article_readability_status": self.article_readability_status,
            "supplement_download_status": self.supplement_download_status,
            "supplement_parse_status": self.supplement_parse_status,
            "local_reference_article_status": self.local_reference_article_status,
            "local_reference_supplement_status": self.local_reference_supplement_status,
            "sample_table_extraction_status": self.sample_table_extraction_status,
            "evidence_acquisition_state": self.evidence_acquisition_state,
            "ingestion_status": self.ingestion_status,
            "expected_sample_count": self.expected_sample_count,
            "expected_sample_count_status": self.expected_sample_count_status,
            "expected_sample_count_provenance": self.expected_sample_count_provenance,
            "expected_sample_count_artifact_path": self.expected_sample_count_artifact_path,
            "sample_identifier_status": self.sample_identifier_status,
            "inventory_disposition": self.inventory_disposition,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True)
class AdnaPaperRegistryRow:
    """Unique paper registry row across the tracked animal aDNA program."""

    paper_doi: str
    canonical_url: str
    article_source_url: str
    journal: str | None
    publication_year: int | None
    title: str
    species_latin_names: tuple[str, ...]
    project_accessions: tuple[str, ...]
    article_download_status: str
    article_readability_status: str
    article_local_path: str
    supplementary_download_status: str
    supplement_parse_status: str
    supplementary_verification_status: str
    local_reference_article_status: str
    local_reference_supplement_status: str
    supplementary_count: int
    parsing_status: str
    sample_extractability: str
    sample_table_extraction_status: str
    evidence_acquisition_state: str
    expected_supplementary_file_families: tuple[str, ...]
    expected_supplementary_artifacts: tuple[str, ...]
    sample_identifier_targets: tuple[str, ...]
    sample_site_targets: tuple[str, ...]
    chronology_targets: tuple[str, ...]
    supplementary_manifest_path: str
    supplementary_acquisition_checklist_path: str

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_doi": self.paper_doi,
            "canonical_url": self.canonical_url,
            "article_source_url": self.article_source_url,
            "journal": self.journal,
            "publication_year": self.publication_year,
            "title": self.title,
            "species_latin_names": list(self.species_latin_names),
            "project_accessions": list(self.project_accessions),
            "article_download_status": self.article_download_status,
            "article_readability_status": self.article_readability_status,
            "article_local_path": self.article_local_path,
            "supplementary_download_status": self.supplementary_download_status,
            "supplement_parse_status": self.supplement_parse_status,
            "supplementary_verification_status": self.supplementary_verification_status,
            "local_reference_article_status": self.local_reference_article_status,
            "local_reference_supplement_status": self.local_reference_supplement_status,
            "supplementary_count": self.supplementary_count,
            "parsing_status": self.parsing_status,
            "sample_extractability": self.sample_extractability,
            "sample_table_extraction_status": self.sample_table_extraction_status,
            "evidence_acquisition_state": self.evidence_acquisition_state,
            "expected_supplementary_file_families": list(
                self.expected_supplementary_file_families
            ),
            "expected_supplementary_artifacts": list(
                self.expected_supplementary_artifacts
            ),
            "sample_identifier_targets": list(self.sample_identifier_targets),
            "sample_site_targets": list(self.sample_site_targets),
            "chronology_targets": list(self.chronology_targets),
            "supplementary_manifest_path": self.supplementary_manifest_path,
            "supplementary_acquisition_checklist_path": self.supplementary_acquisition_checklist_path,
        }


@dataclass(frozen=True)
class AdnaSupplementRegistryRow:
    """Tracked supplementary-material registry row for one supporting artifact."""

    artifact_id: str
    paper_doi: str
    source_url: str
    local_path: str
    artifact_kind: str
    fetch_status: str
    project_accessions: tuple[str, ...]
    purpose: str

    def as_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "paper_doi": self.paper_doi,
            "source_url": self.source_url,
            "local_path": self.local_path,
            "artifact_kind": self.artifact_kind,
            "fetch_status": self.fetch_status,
            "project_accessions": list(self.project_accessions),
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class AdnaSourceBundleManifest:
    """Per-project manifest tying archive, paper, and supplementary assets together."""

    project_accession: str
    species_latin_name: str
    archive_status: str
    evidence_strength: str
    project_url: str
    paper_doi: str | None
    paper_title: str | None
    archive_metadata_sufficient: bool
    paper_required: bool
    supplement_required: bool
    paper_download_status: str
    supplement_download_status: str
    local_artifact_ids: tuple[str, ...]
    local_artifact_paths: tuple[str, ...]
    blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "species_latin_name": self.species_latin_name,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "project_url": self.project_url,
            "paper_doi": self.paper_doi,
            "paper_title": self.paper_title,
            "archive_metadata_sufficient": self.archive_metadata_sufficient,
            "paper_required": self.paper_required,
            "supplement_required": self.supplement_required,
            "paper_download_status": self.paper_download_status,
            "supplement_download_status": self.supplement_download_status,
            "local_artifact_ids": list(self.local_artifact_ids),
            "local_artifact_paths": list(self.local_artifact_paths),
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class _RemoteArtifactSpec:
    artifact_kind: str
    label: str
    source_url: str
    relative_path: str
    remote_note: str


@dataclass(frozen=True)
class _PaperSourceSpec:
    doi: str
    article_source_url: str
    article_local_path: str
    article_kind: str
    article_note: str
    supplementary_assets: tuple[_RemoteArtifactSpec, ...] = ()
    parsing_status: str = "ready_for_project_sample_extraction"
    sample_extractability: str = "manual_curation_required"
    sample_identifier_targets: tuple[str, ...] = ()
    sample_site_targets: tuple[str, ...] = ()
    chronology_targets: tuple[str, ...] = ()
    registry_note: str = ""


@dataclass(frozen=True)
class _ProjectIntakeExpectation:
    expected_sample_count: int | None
    expected_sample_count_status: str
    expected_sample_count_provenance: str
    expected_sample_count_artifact_path: str
    sample_identifier_status: str
    inventory_disposition: str
    rejection_reason: str
    extraction_plan: str
    blocker_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class _PendingSourceCapture:
    logical_path: Path
    payload: bytes
    metadata: dict[str, object]


class _SourceCaptureDisposition(Enum):
    NEW_CAPTURE = "new_capture"
    IDENTICAL_EXISTING = "identical_existing"
    REFUSED = "refused"


@dataclass(frozen=True)
class _SourceCaptureAssessment:
    disposition: _SourceCaptureDisposition
    refusal_path: Path | None = None


SOURCE_LIBRARY_SCHEMA_VERSION = "adna-source-library.v1"


_CAPTURE_REFUSAL_SCHEMA_VERSION = "adna-source-capture-refusal.v1"


_USER_AGENT = "Mozilla/5.0 (compatible; bijux-pollenomics/1.0)"


_NATURE_DOI_RE = re.compile(
    r"https?://www\.nature\.com/articles/(?P<slug>[A-Za-z0-9_.-]+)"
)
