"""Cross-project aDNA source intake and release audits."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict
from bijux_pollenomics.adna.workflow.source_artifacts import (
    resolve_source_artifact_path,
)
from bijux_pollenomics.adna.sources.ena import build_archive_project_catalog
from .models import (
    AdnaProjectRegistryRow,
    AdnaSourceBundleManifest,
    SOURCE_LIBRARY_SCHEMA_VERSION,
)
from .registries import (
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
    build_supplement_zip_member_registry,
)


class _CrossProjectAudit(TypedDict):
    schema_version: str
    archive_sufficient_count: int
    paper_dependent_count: int
    supplement_dependent_count: int
    blocked_count: int
    rows: list[dict[str, object]]


def build_cross_project_source_audit(output_root: Path) -> dict[str, object]:
    """Summarize how much of the tracked program is archive-sufficient versus paper-dependent."""
    bundles = build_project_source_bundles(output_root)
    summary: _CrossProjectAudit = {
        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
        "archive_sufficient_count": 0,
        "paper_dependent_count": 0,
        "supplement_dependent_count": 0,
        "blocked_count": 0,
        "rows": [],
    }
    for bundle in bundles:
        if bundle.archive_metadata_sufficient:
            summary["archive_sufficient_count"] += 1
        else:
            summary["paper_dependent_count"] += 1
        if bundle.supplement_required:
            summary["supplement_dependent_count"] += 1
        if bundle.blockers:
            summary["blocked_count"] += 1
        summary["rows"].append(
            {
                "project_accession": bundle.project_accession,
                "species_latin_name": bundle.species_latin_name,
                "archive_status": bundle.archive_status,
                "archive_metadata_sufficient": bundle.archive_metadata_sufficient,
                "paper_required": bundle.paper_required,
                "supplement_required": bundle.supplement_required,
                "paper_download_status": bundle.paper_download_status,
                "supplement_download_status": bundle.supplement_download_status,
                "blockers": list(bundle.blockers),
            }
        )
    return dict(summary)


def build_missing_source_blockers(output_root: Path) -> dict[str, object]:
    """Return the explicit blocker ledger for paper and supplementary archive gaps."""
    project_rows = {
        row.project_accession: row for row in build_project_registry(output_root)
    }
    rows = []
    for bundle in build_project_source_bundles(output_root):
        if not bundle.blockers:
            continue
        project_row = project_rows[bundle.project_accession]
        blocker_categories = list(_derive_blocker_categories(bundle, project_row))
        rows.append(
            {
                "project_accession": bundle.project_accession,
                "species_latin_name": bundle.species_latin_name,
                "paper_doi": bundle.paper_doi,
                "paper_title": bundle.paper_title,
                "archive_status": bundle.archive_status,
                "paper_download_status": bundle.paper_download_status,
                "supplement_download_status": bundle.supplement_download_status,
                "blockers": list(bundle.blockers),
                "blocker_categories": blocker_categories,
            }
        )
    return {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": rows}


def _derive_blocker_categories(
    bundle: AdnaSourceBundleManifest,
    project_row: AdnaProjectRegistryRow,
) -> tuple[str, ...]:
    categories: list[str] = []
    if "missing_local_paper_evidence" in bundle.blockers:
        categories.append("missing_paper_capture")
    if "missing_local_supplementary_material" in bundle.blockers:
        categories.append("missing_supplementary_capture")
    if (
        project_row.sample_identifier_status
        in {
            "missing_primary_paper_linkage",
            "manual_curation_required",
            "paper_or_supplement_targets_curated",
        }
        and project_row.expected_sample_count is None
    ):
        categories.append("missing_sample_identifiers")
    if bundle.paper_download_status != "archived" and bundle.paper_required:
        categories.append("missing_readable_tables")
    return tuple(dict.fromkeys(categories))


def build_source_intake_audit(output_root: Path) -> dict[str, object]:
    """Return the richer intake audit behind project and paper capture."""
    output_root = Path(output_root)
    project_rows = build_project_registry(output_root)
    paper_rows = build_paper_registry(output_root)
    bundles = {
        bundle.project_accession: bundle
        for bundle in build_project_source_bundles(output_root)
    }
    member_rows = build_supplement_zip_member_registry(output_root)

    zip_member_rows_by_doi: dict[str, list[dict[str, object]]] = {}
    for row in member_rows:
        doi = str(row.get("paper_doi") or "")
        zip_member_rows_by_doi.setdefault(doi, []).append(row)

    blocker_counts = {
        "missing_paper_capture_count": 0,
        "missing_supplementary_capture_count": 0,
        "missing_readable_tables_count": 0,
        "missing_sample_identifier_count": 0,
    }
    project_rows_payload: list[dict[str, object]] = []
    for project_row in project_rows:
        bundle = bundles[project_row.project_accession]
        categories = _derive_blocker_categories(bundle, project_row)
        if "missing_paper_capture" in categories:
            blocker_counts["missing_paper_capture_count"] += 1
        if "missing_supplementary_capture" in categories:
            blocker_counts["missing_supplementary_capture_count"] += 1
        if "missing_readable_tables" in categories:
            blocker_counts["missing_readable_tables_count"] += 1
        if "missing_sample_identifiers" in categories:
            blocker_counts["missing_sample_identifier_count"] += 1
        project_rows_payload.append(
            {
                "project_accession": project_row.project_accession,
                "species_latin_name": project_row.species_latin_name,
                "inventory_disposition": project_row.inventory_disposition,
                "expected_sample_count": project_row.expected_sample_count,
                "expected_sample_count_status": project_row.expected_sample_count_status,
                "sample_identifier_status": project_row.sample_identifier_status,
                "blocker_categories": list(categories),
            }
        )

    sample_extractable_violations: list[dict[str, object]] = []
    for paper_row in paper_rows:
        if paper_row.sample_extractability not in {
            "article_extractable",
            "supplement_extractable",
        }:
            continue
        member_inventory_ok = True
        if any(
            path.endswith(".zip") for path in paper_row.expected_supplementary_artifacts
        ):
            member_inventory_ok = any(
                str(row.get("member_name", "")).strip()
                and str(row.get("inferred_purpose", "")) != "invalid_zip_bundle"
                for row in zip_member_rows_by_doi.get(paper_row.paper_doi, [])
            )
        required_assets_ok = all(
            _resolve_data_relative_path(output_root, path).is_file()
            for path in paper_row.expected_supplementary_artifacts
        )
        if paper_row.sample_extractability == "supplement_extractable" and (
            paper_row.supplementary_download_status != "archived"
            or not required_assets_ok
            or not member_inventory_ok
        ):
            sample_extractable_violations.append(
                {
                    "paper_doi": paper_row.paper_doi,
                    "title": paper_row.title,
                    "supplementary_download_status": paper_row.supplementary_download_status,
                    "required_assets_ok": required_assets_ok,
                    "member_inventory_ok": member_inventory_ok,
                }
            )

    return {
        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
        "sample_extractable_paper_count": sum(
            1
            for row in paper_rows
            if row.sample_extractability
            in {"article_extractable", "supplement_extractable"}
        ),
        "supplementary_manifested_paper_count": sum(
            1 for row in paper_rows if row.expected_supplementary_artifacts
        ),
        "supplement_zip_member_count": len(member_rows),
        "blocker_counts": blocker_counts,
        "sample_extractable_violations": sample_extractable_violations,
        "rows": project_rows_payload,
    }


def _resolve_data_relative_path(output_root: Path, path: str) -> Path:
    if path.startswith("data/"):
        return resolve_source_artifact_path(output_root / path.removeprefix("data/"))
    return resolve_source_artifact_path(output_root / path)


def build_source_intake_release_guard(output_root: Path) -> dict[str, object]:
    """Return the tracked-project guard for the intake inventory."""
    catalog = build_archive_project_catalog()
    project_rows = build_project_registry(output_root)
    catalog_accessions = {project.project_accession for project in catalog}
    published_accessions = {row.project_accession for row in project_rows}
    missing_accessions = tuple(sorted(catalog_accessions - published_accessions))
    rejected_without_reason = tuple(
        sorted(
            row.project_accession
            for row in project_rows
            if row.inventory_disposition == "retained_rejected_reference"
            and not row.rejection_reason.strip()
        )
    )
    passing = not missing_accessions and not rejected_without_reason
    return {
        "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
        "passing": passing,
        "tracked_project_count": len(catalog_accessions),
        "published_project_registry_count": len(published_accessions),
        "missing_project_accessions": list(missing_accessions),
        "rejected_without_reason": list(rejected_without_reason),
    }
