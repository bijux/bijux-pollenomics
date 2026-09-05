"""Paper and supplement evidence-status derivation."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from ..models import AdnaSourceArtifact, _PaperSourceSpec, _ReferenceStashRecord
from .supplements import build_supplement_zip_member_registry


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
