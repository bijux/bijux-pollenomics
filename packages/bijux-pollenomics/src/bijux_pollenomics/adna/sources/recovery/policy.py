from __future__ import annotations

from typing import Any

from bijux_pollenomics.adna.sources.library.models import (
    AdnaPaperRegistryRow,
    AdnaProjectRegistryRow,
    AdnaSourceBundleManifest,
)
from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from .constants import ADNA_INTAKE_STAGE_KEYS
from .metrics import _int_value, _nonempty_paths


def _project_stage_statuses(
    *,
    project_row: AdnaProjectRegistryRow,
    bundle: AdnaSourceBundleManifest,
    paper_row: AdnaPaperRegistryRow | None,
    sample_master_row: dict[str, Any],
    site_row: dict[str, Any],
    chronology_row: dict[str, Any],
    coord_counts: dict[str, int],
) -> dict[str, str]:
    stage_statuses: dict[str, str] = {}
    stage_statuses["project_admission"] = "complete"
    if project_row.inventory_disposition == "retained_rejected_reference":
        for stage in ADNA_INTAKE_STAGE_KEYS[1:]:
            stage_statuses[stage] = "not_required"
        return stage_statuses

    if (
        project_row.primary_paper_doi
        and project_row.paper_download_status == "archived"
    ):
        stage_statuses["paper_capture"] = "complete"
    elif project_row.primary_paper_doi:
        stage_statuses["paper_capture"] = "blocked"
    elif project_row.sample_identifier_status == "archive_native_identifiers_known":
        stage_statuses["paper_capture"] = "not_required"
    else:
        stage_statuses["paper_capture"] = "blocked"

    if (
        project_row.supplement_download_status == "archived"
        or (
            paper_row is not None
            and paper_row.supplementary_download_status == "archived"
        )
    ):
        stage_statuses["supplement_capture"] = "complete"
    elif not bundle.supplement_required:
        stage_statuses["supplement_capture"] = "not_required"
    else:
        stage_statuses["supplement_capture"] = "blocked"

    final_sample_count = _int_value(sample_master_row.get("final_sample_count") or 0)
    if final_sample_count > 0:
        stage_statuses["sample_identity_recovery"] = "complete"
    elif str(project_row.sample_table_extraction_status) == "published_empty":
        stage_statuses["sample_identity_recovery"] = "in_progress"
    else:
        stage_statuses["sample_identity_recovery"] = "blocked"

    if stage_statuses["sample_identity_recovery"] != "complete":
        stage_statuses["site_recovery"] = "blocked"
        stage_statuses["chronology_recovery"] = "blocked"
        stage_statuses["coordinate_derivation"] = "blocked"
        stage_statuses["publication_readiness"] = "blocked"
        return stage_statuses

    lacking_site = _int_value(site_row.get("lacking_defensible_site_assignment_count") or 0)
    if final_sample_count > 0 and lacking_site == 0:
        stage_statuses["site_recovery"] = "complete"
    else:
        stage_statuses["site_recovery"] = "in_progress"

    missing_chronology = _int_value(chronology_row.get("unresolved_count") or 0)
    missing_norm = _int_value(chronology_row.get("normalization_unresolved_count") or 0)
    if final_sample_count > 0 and missing_chronology == 0 and missing_norm == 0:
        stage_statuses["chronology_recovery"] = "complete"
    else:
        stage_statuses["chronology_recovery"] = "in_progress"

    if (
        stage_statuses["site_recovery"] == "complete"
        and _int_value(coord_counts.get("mappable_point", 0)) > 0
        and _int_value(coord_counts.get("refused_region_only", 0)) == 0
    ):
        stage_statuses["coordinate_derivation"] = "complete"
    elif (
        stage_statuses["site_recovery"] == "complete"
        or _int_value(coord_counts.get("mappable_point", 0)) > 0
    ):
        stage_statuses["coordinate_derivation"] = "in_progress"
    else:
        stage_statuses["coordinate_derivation"] = "blocked"

    if (
        stage_statuses["site_recovery"] == "complete"
        and stage_statuses["chronology_recovery"] == "complete"
        and stage_statuses["coordinate_derivation"] in {"complete", "in_progress"}
        and "comparator" not in str(project_row.evidence_strength)
    ):
        stage_statuses["publication_readiness"] = "complete"
    elif "comparator" in str(project_row.evidence_strength):
        stage_statuses["publication_readiness"] = "not_required"
    else:
        stage_statuses["publication_readiness"] = "blocked"
    return stage_statuses


def _minimum_expected_sample_count(
    project_row: AdnaProjectRegistryRow,
    sample_master_row: dict[str, Any],
) -> int | None:
    if project_row.expected_sample_count is not None:
        return _int_value(project_row.expected_sample_count)
    if project_row.inventory_disposition == "retained_rejected_reference":
        return None
    if project_row.sample_identifier_status in {
        "paper_or_supplement_targets_curated",
        "manual_curation_required",
        "archive_native_identifiers_known",
    }:
        return 1
    if (
        str(project_row.sample_table_extraction_status)
        == "project_sample_master_published"
        and _int_value(sample_master_row.get("recovered_sample_count") or 0) > 0
    ):
        return _int_value(sample_master_row.get("recovered_sample_count") or 0)
    return None


def _implausibly_low_recovery(
    *,
    project_row: AdnaProjectRegistryRow,
    sample_master_row: dict[str, Any],
    minimum_gap_count: int | None,
) -> tuple[bool, str]:
    if project_row.inventory_disposition == "retained_rejected_reference":
        return (False, "")
    final_sample_count = _int_value(sample_master_row.get("final_sample_count") or 0)
    if (
        project_row.expected_sample_count is not None
        and minimum_gap_count
        and minimum_gap_count > 0
    ):
        return (
            True,
            "Exact expected sample count is curated, but the governed sample master still recovers fewer final rows than that exact count.",
        )
    if (
        str(project_row.sample_table_extraction_status) == "published_empty"
        and project_row.paper_download_status == "archived"
        and project_row.sample_identifier_status
        in {"paper_or_supplement_targets_curated", "manual_curation_required"}
    ):
        return (
            True,
            "Readable paper or supplementary capture exists, but the governed sample master still publishes zero recovered rows.",
        )
    if (
        final_sample_count == 0
        and project_row.sample_identifier_status == "archive_native_identifiers_known"
    ):
        return (
            True,
            "Archive-native sample identifiers are already known, but no governed final sample row was published.",
        )
    return (False, "")


def _expected_contributions(
    *,
    project_row: AdnaProjectRegistryRow,
    paper_row: AdnaPaperRegistryRow | None,
    site_row: dict[str, Any],
    chronology_row: dict[str, Any],
) -> list[str]:
    contributions: list[str] = []
    if project_row.inventory_disposition == "retained_rejected_reference":
        return contributions
    if project_row.sample_identifier_status != "missing_primary_paper_linkage":
        contributions.append("sample_identities")
    if paper_row is not None:
        contributions.append("taxonomic_context")
    if (
        _int_value(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0
        or not site_row
    ):
        contributions.append("site_evidence")
        contributions.append("coordinate_candidates")
    if _int_value(chronology_row.get("unresolved_count") or 0) > 0 or not chronology_row:
        contributions.append("sample_chronology")
    return list(dict.fromkeys(contributions))


def _expected_contribution_surfaces(
    *,
    project_row: AdnaProjectRegistryRow,
    paper_row: AdnaPaperRegistryRow | None,
) -> list[str]:
    surfaces = [
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_row.project_accession}/archive_metadata.html"
    ]
    if paper_row is not None:
        surfaces.append(paper_row.article_local_path)
        surfaces.extend(
            str(item) for item in paper_row.expected_supplementary_artifacts
        )
        surfaces.extend(str(item) for item in paper_row.sample_identifier_targets)
        surfaces.extend(str(item) for item in paper_row.sample_site_targets)
        surfaces.extend(str(item) for item in paper_row.chronology_targets)
    return _nonempty_paths(surfaces)


def _next_required_stage(stage_statuses: dict[str, str]) -> str | None:
    for stage in ADNA_INTAKE_STAGE_KEYS:
        if stage_statuses[stage] in {"blocked", "in_progress"}:
            return stage
    return None


def _overall_recovery_status(stage_statuses: dict[str, str]) -> str:
    if stage_statuses["publication_readiness"] == "complete":
        return "ready_for_publication_review"
    if any(status == "blocked" for status in stage_statuses.values()):
        return "blocked_projects"
    if any(status == "in_progress" for status in stage_statuses.values()):
        return "in_progress_projects"
    return "complete_projects"


def _recovery_depth_score(stage_statuses: dict[str, str]) -> float:
    complete = sum(1 for status in stage_statuses.values() if status == "complete")
    required = sum(1 for status in stage_statuses.values() if status != "not_required")
    if required == 0:
        return 0.0
    return round(complete / required, 4)


def _recovery_gap_status(
    *,
    project_row: AdnaProjectRegistryRow,
    sample_master_row: dict[str, Any],
    minimum_gap_count: int | None,
) -> str:
    if project_row.inventory_disposition == "retained_rejected_reference":
        return "out_of_scope_reference"
    final_sample_count = _int_value(sample_master_row.get("final_sample_count") or 0)
    if (
        project_row.expected_sample_count is not None
        and _int_value(minimum_gap_count or 0) == 0
    ):
        return "recovered_to_exact_expected_count"
    if (
        project_row.expected_sample_count is not None
        and _int_value(minimum_gap_count or 0) > 0
    ):
        return "exact_expected_count_still_unrecovered"
    if (
        final_sample_count == 0
        and str(project_row.sample_table_extraction_status) == "published_empty"
    ):
        return "extractable_sources_but_no_governed_samples"
    if final_sample_count > 0 and minimum_gap_count is None:
        return "partial_recovery_expected_total_unknown"
    if final_sample_count > 0 and _int_value(minimum_gap_count or 0) == 0:
        return "minimum_expected_floor_met"
    return "paper_or_capture_gap_blocks_estimate"


def _known_assets(
    project_row: AdnaProjectRegistryRow,
    bundle: AdnaSourceBundleManifest,
) -> list[str]:
    assets = list(bundle.local_artifact_paths)
    project_root = f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_row.project_accession}"
    for suffix in (
        "sample_master.json",
        "sample_sites.json",
        "sample_chronology.json",
        "sample_locality_evidence.json",
    ):
        assets.append(f"{project_root}/{suffix}")
    return _nonempty_paths(assets)


def _missing_assets(
    *,
    project_row: AdnaProjectRegistryRow,
    bundle: AdnaSourceBundleManifest,
    sample_master_row: dict[str, Any],
    site_row: dict[str, Any],
    gap_row: dict[str, Any],
) -> list[str]:
    missing: list[str] = []
    if "missing_local_paper_evidence" in bundle.blockers:
        missing.append("Readable repository paper capture is still missing.")
    if "missing_local_supplementary_material" in bundle.blockers:
        missing.append("Governed repository supplementary capture is still missing.")
    if _int_value(sample_master_row.get("final_sample_count") or 0) == 0:
        missing.append("No final governed sample rows are published yet.")
    if _int_value(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0:
        missing.append(
            "Some recovered sample rows still lack a defensible site assignment."
        )
    if _int_value(gap_row.get("missing_date_count") or 0) > 0:
        missing.append("Some recovered sample rows still lack sample-level chronology.")
    if project_row.sample_identifier_status == "missing_primary_paper_linkage":
        missing.append(
            "The tracked project still lacks a pinned primary paper linkage."
        )
    return missing


def _major_deficit_reasons(
    *,
    project_row: AdnaProjectRegistryRow,
    minimum_gap_count: int | None,
    site_row: dict[str, Any],
    gap_row: dict[str, Any],
    coord_counts: dict[str, int],
    implausibly_low: bool,
) -> list[str]:
    reasons: list[str] = []
    if implausibly_low:
        reasons.append("implausibly_low_sample_recovery")
    if _int_value(minimum_gap_count or 0) > 0:
        reasons.append("sample_recovery_gap")
    if _int_value(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0:
        reasons.append("site_assignment_gap")
    if _int_value(gap_row.get("missing_date_count") or 0) > 0:
        reasons.append("chronology_gap")
    if _int_value(coord_counts.get("refused_region_only", 0)) > 0:
        reasons.append("coordinate_precision_gap")
    if project_row.sample_identifier_status == "missing_primary_paper_linkage":
        reasons.append("missing_primary_paper_linkage")
    return reasons


def _paper_yield_recovery_posture(items: list[dict[str, Any]]) -> str:
    if any(bool(item["implausibly_low_recovery"]) for item in items):
        return "implausibly_low_project_recovery_present"
    if any(item["expected_sample_count"] is None for item in items):
        return "expected_total_still_partially_unbounded"
    return "exact_expected_counts_curated"


def _missing_source_queue_category(row: dict[str, Any]) -> str:
    if row["inventory_disposition"] == "retained_rejected_reference":
        return "not_queued"
    if "missing_primary_paper_linkage" in row["major_deficit_reasons"]:
        return "missing_primary_paper_linkage"
    if str(row["paper_download_status"]) != "archived" and row["paper_doi"]:
        return "missing_repository_paper_capture"
    if (
        str(row["supplement_download_status"]) != "archived"
        and "sample_identities" in row["expected_contributions"]
        and any(
            "supplementary" in surface
            for surface in row["expected_contribution_surfaces"]
        )
    ):
        return "missing_repository_supplement_capture"
    if bool(row["implausibly_low_recovery"]):
        return "sample_recovery_still_thin"
    return "not_queued"


def _missing_source_queue_reason(category: str, row: dict[str, Any]) -> str:
    if category == "missing_primary_paper_linkage":
        return "The project is tracked, but the repository still lacks a pinned primary paper anchor for downstream extraction."
    if category == "missing_repository_paper_capture":
        return "The project has a paper anchor, but the repository still lacks a governed readable article surface."
    if category == "missing_repository_supplement_capture":
        return "The tracked paper points to supplementary evidence that still is not archived under the governed source library."
    if category == "sample_recovery_still_thin":
        return str(row["implausibly_low_recovery_reason"])
    return ""
