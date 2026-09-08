"""Animal foundation validation responsibilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ....adna.sources.library import (
    build_project_source_bundles,
)
from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .repository import (
    _load_all_coordinate_rows,
    _load_all_sample_rows,
    _load_all_site_evidence_rows,
)


def build_animal_foundation_validation_report(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    """Validate the structural scientific contract behind published animal outputs."""
    sample_rows = _load_all_sample_rows(data_root)
    site_rows = _load_all_site_evidence_rows(data_root)
    provenance_rows = _load_all_coordinate_rows(data_root)
    try:
        atlas_rows = [
            row.as_dict() for row in build_tracked_animal_atlas_evidence_rows(data_root)
        ]
    except FileNotFoundError:
        atlas_rows = []
    source_bundles = build_project_source_bundles(data_root)

    sample_tokens: list[str] = []
    duplicate_sample_tokens: set[str] = set()
    for row in sample_rows:
        token = str(row.get("identity", {}).get("stable_token", "")).strip()
        if not token:
            continue
        if token in sample_tokens:
            duplicate_sample_tokens.add(token)
        sample_tokens.append(token)

    checks = [
        _check_row(
            "unique_sample_stable_ids",
            len(duplicate_sample_tokens) == 0,
            "Stable sample identifiers stay unique across all tracked animal rows.",
            sorted(duplicate_sample_tokens),
        ),
        _check_row(
            "sample_project_linkage_present",
            all(str(row.get("project_accession", "")).strip() for row in sample_rows),
            "Every curated animal sample row keeps a project accession.",
            [
                str(row.get("species_latin_name", ""))
                for row in sample_rows
                if not str(row.get("project_accession", "")).strip()
            ],
        ),
        _check_row(
            "sample_paper_linkage_present",
            all(str(row.get("paper_doi", "")).strip() for row in sample_rows),
            "Every curated animal sample row keeps a paper DOI reference.",
            [
                str(row.get("project_accession", ""))
                for row in sample_rows
                if not str(row.get("paper_doi", "")).strip()
            ],
        ),
        _check_row(
            "supplement_required_projects_archived",
            all(
                (not bundle.supplement_required)
                or bundle.supplement_download_status == "archived"
                for bundle in source_bundles
            ),
            "Projects that require supplementary material keep a local archived supplement.",
            [
                bundle.project_accession
                for bundle in source_bundles
                if bundle.supplement_required
                and bundle.supplement_download_status != "archived"
            ],
        ),
        _check_row(
            "site_evidence_keeps_source_traceability",
            all(
                str(row.get("source_artifact_path", "")).strip()
                and str(row.get("source_locator", "")).strip()
                and str(row.get("source_support_status", "")).strip()
                for row in site_rows
            ),
            "Every site-evidence row keeps source artifact, locator, and support status.",
            [
                str(row.get("project_accession", ""))
                for row in site_rows
                if not (
                    str(row.get("source_artifact_path", "")).strip()
                    and str(row.get("source_locator", "")).strip()
                    and str(row.get("source_support_status", "")).strip()
                )
            ],
        ),
        _check_row(
            "mappable_coordinates_keep_complete_basis",
            all(
                str(row.get("coordinate_basis", "")).strip()
                and str(row.get("coordinate_confidence", "")).strip()
                and str(row.get("confidence_rationale", "")).strip()
                and str(row.get("latitude_text", "")).strip()
                and str(row.get("longitude_text", "")).strip()
                for row in provenance_rows
                if str(row.get("mapping_posture", "")) == "mappable_point"
            ),
            "Every mappable coordinate row keeps basis, confidence, rationale, and text coordinates.",
            [
                str(row.get("project_accession", ""))
                for row in provenance_rows
                if str(row.get("mapping_posture", "")) == "mappable_point"
                and not (
                    str(row.get("coordinate_basis", "")).strip()
                    and str(row.get("coordinate_confidence", "")).strip()
                    and str(row.get("confidence_rationale", "")).strip()
                    and str(row.get("latitude_text", "")).strip()
                    and str(row.get("longitude_text", "")).strip()
                )
            ],
        ),
        _check_row(
            "atlas_rows_keep_traceability",
            all(
                (
                    str(row.get("feature_id", "")).strip()
                    and str(row.get("evidence_row_id", "")).strip()
                    and str(row.get("site_record_id", "")).strip()
                    and str(row.get("primary_project_accession", "")).strip()
                    and str(row.get("paper_doi", "")).strip()
                    and str(row.get("paper_url", "")).strip()
                    and bool(row.get("sample_record_ids", []))
                )
                for row in atlas_rows
            ),
            "Every published animal atlas row keeps feature, project, paper, and sample traceability.",
            [
                str(row.get("feature_id", ""))
                for row in atlas_rows
                if not (
                    str(row.get("feature_id", "")).strip()
                    and str(row.get("evidence_row_id", "")).strip()
                    and str(row.get("site_record_id", "")).strip()
                    and str(row.get("primary_project_accession", "")).strip()
                    and str(row.get("paper_doi", "")).strip()
                    and str(row.get("paper_url", "")).strip()
                    and bool(row.get("sample_record_ids", []))
                )
            ],
        ),
    ]
    overall_ok = all(bool(check["passed"]) for check in checks)
    return {
        "schema_version": "animal-foundation-validation.v1",
        "overall_ok": overall_ok,
        "sample_row_count": len(sample_rows),
        "site_evidence_row_count": len(site_rows),
        "coordinate_row_count": len(provenance_rows),
        "atlas_row_count": len(atlas_rows),
        "checks": checks,
    }


def _check_row(
    check_id: str,
    passed: bool,
    description: str,
    findings: list[str],
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": passed,
        "description": description,
        "finding_count": len(findings),
        "findings": findings[:10],
    }
