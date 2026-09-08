"""Animal foundation recovery responsibilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from ....adna.projects.evidence.chronology import (
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
)
from ....adna.projects.evidence.localities import (
    build_project_locality_completeness_rows,
    build_project_locality_substitution_ledger,
    build_sample_locality_conflict_ledger,
    build_sample_locality_manual_curation_workflow_rows,
    build_site_name_normalization_dictionary_rows,
)
from ....adna.projects.registry.sites import (
    ADNA_LOCALITY_RESOLUTION_STATUSES,
)
from ....adna.sources.library import (
    build_paper_registry,
    build_project_registry,
    build_supplement_registry,
)
from ....adna.sources.recovery import (
    build_manual_curation_worklist,
    build_missing_source_queue,
    build_project_expected_sample_yield_review,
    build_project_recovery_stage_review,
    build_source_recovery_progress,
    build_source_recovery_release_guard,
    build_species_project_deficit_ledger,
)
from .repository import (
    _load_all_coordinate_rows,
    _load_all_project_sample_chronology_rows,
    _load_all_project_sample_site_rows,
    _load_all_sample_rows,
    _load_all_site_evidence_rows,
    _load_country_payloads,
)


def build_animal_intake_recovery_review(
    *,
    data_root: Path,
) -> dict[str, Any]:
    """Publish one outsider-facing review of current intake recovery depth and blockers."""
    stage_review = build_project_recovery_stage_review(data_root)
    project_yield_review = build_project_expected_sample_yield_review(data_root)
    species_deficit_ledger = build_species_project_deficit_ledger(data_root)
    worklist = build_manual_curation_worklist(data_root)
    progress = build_source_recovery_progress(data_root)
    missing_source_queue = build_missing_source_queue(data_root)
    release_guard = build_source_recovery_release_guard(data_root)
    stage_summary = cast(dict[str, Any], stage_review["summary"])
    project_yield_rows = cast(list[dict[str, Any]], project_yield_review["rows"])

    return {
        "schema_version": "animal-intake-recovery-review.v1",
        "public_posture": "sample_recovery_still_partial_and_project_gaps_explicit",
        "stage_review": {
            "tracked_project_count": stage_review["row_count"],
            "ready_for_publication_review": stage_summary[
                "ready_for_publication_review"
            ],
            "blocked_projects": stage_summary["blocked_projects"],
            "in_progress_projects": stage_summary["in_progress_projects"],
        },
        "yield_review": project_yield_review["counts"],
        "species_deficit_counts": species_deficit_ledger["species_counts"],
        "manual_curation_counts": worklist["counts"],
        "missing_source_queue_counts": missing_source_queue["counts"],
        "release_guard": {
            "passing": release_guard["passing"],
            "implausibly_low_recovery_project_count": release_guard[
                "implausibly_low_recovery_project_count"
            ],
        },
        "sample_evidence_depth_counts": progress["sample_evidence_depth_counts"],
        "top_gap_projects": [
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "recovery_gap_status": row["recovery_gap_status"],
                "minimum_gap_count": row["minimum_gap_count"],
                "major_deficit_reasons": row["major_deficit_reasons"],
            }
            for row in project_yield_rows
            if row["major_deficit_reasons"]
        ][:20],
        "direct_links": {
            "project_recovery_stage_review": "data/adna/governance/source_library/project_recovery_stage_review.json",
            "project_expected_sample_yield_review": "data/adna/governance/source_library/project_expected_sample_yield_review.json",
            "paper_expected_sample_yield_review": "data/adna/governance/source_library/paper_expected_sample_yield_review.json",
            "species_project_deficit_ledger": "data/adna/governance/source_library/species_project_deficit_ledger.json",
            "manual_curation_worklist": "data/adna/governance/source_library/manual_curation_worklist.json",
            "source_recovery_progress": "data/adna/governance/source_library/source_recovery_progress.json",
            "missing_source_queue": "data/adna/governance/source_library/missing_source_queue.json",
            "source_recovery_release_guard": "data/adna/governance/source_library/source_recovery_release_guard.json",
        },
    }


def build_animal_sample_database_review(
    *,
    data_root: Path,
    report_root: Path,
    point_payload: dict[str, Any],
    review_payload: dict[str, Any],
    intake_recovery_payload: dict[str, Any],
) -> dict[str, Any]:
    """Prove the current repository posture as a checked-in sample database."""
    project_rows = build_project_registry(data_root)
    paper_rows = build_paper_registry(data_root)
    supplement_rows = build_supplement_registry(data_root)
    sample_rows = _load_all_sample_rows(data_root)
    site_rows = _load_all_site_evidence_rows(data_root)
    chronology_rows = _load_all_project_sample_chronology_rows(data_root)
    coordinate_rows = _load_all_coordinate_rows(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    locality_conflict_rows = build_sample_locality_conflict_ledger(data_root)
    locality_curation_rows = build_sample_locality_manual_curation_workflow_rows(
        data_root
    )
    locality_substitution_rows = build_project_locality_substitution_ledger(data_root)
    locality_dictionary_rows = build_site_name_normalization_dictionary_rows(data_root)
    locality_completeness_rows = cast(
        list[dict[str, Any]], build_project_locality_completeness_rows(data_root)
    )
    country_payloads = _load_country_payloads(report_root)

    locality_status_counts = dict.fromkeys(ADNA_LOCALITY_RESOLUTION_STATUSES, 0)
    for row in sample_site_rows:
        status = str(row.get("locality_resolution_status", "")).strip()
        if status in locality_status_counts:
            locality_status_counts[status] += 1

    chronology_status_counts = dict.fromkeys(ADNA_CHRONOLOGY_NORMALIZATION_STATUSES, 0)
    chronology_precision_counts = dict.fromkeys(ADNA_CHRONOLOGY_PRECISION_POSTURES, 0)
    for row in chronology_rows:
        status = str(row.get("chronology_normalization_status", "")).strip()
        if status in chronology_status_counts:
            chronology_status_counts[status] += 1
        precision_posture = str(row.get("chronology_precision_posture", "")).strip()
        if precision_posture in chronology_precision_counts:
            chronology_precision_counts[precision_posture] += 1
    paper_with_archived_supplement_count = sum(
        1 for row in paper_rows if int(row.supplementary_count) > 0
    )
    normalized_chronology_count = (
        chronology_status_counts["normalized_interval"]
        + chronology_status_counts["normalized_point"]
    )
    point_row_count = int(point_payload["row_count"])
    mapped_sample_count = _mapped_sample_count(point_payload)
    mapped_sample_share = (
        round(mapped_sample_count / len(sample_rows), 4) if sample_rows else 0.0
    )

    direct_links = {
        "project_registry": "data/adna/governance/source_library/project_registry.json",
        "paper_registry": "data/adna/governance/source_library/paper_registry.json",
        "supplement_registry": "data/adna/governance/source_library/supplement_registry.json",
        "sample_foundation_truth": "data/adna/governance/animal_sample_foundation_truth.json",
        "sample_database_contract": "data/adna/governance/animal_sample_product_contract.json",
        "sample_query_example": "docs/report/countries/sweden/sweden_animal_adna_v66_samples.md",
        "site_review": "data/adna/governance/source_library/project_sample_site_review.json",
        "locality_conflicts": "data/adna/governance/source_library/sample_locality_conflict_ledger.json",
        "locality_curation_workflow": "data/adna/governance/source_library/sample_locality_manual_curation_workflow.json",
        "locality_substitution_ledger": "data/adna/governance/source_library/project_locality_substitution_ledger.json",
        "locality_normalization_dictionary": "data/adna/governance/source_library/site_name_normalization_dictionary.json",
        "locality_completeness": "data/adna/governance/source_library/project_locality_completeness.json",
        "chronology_review": "data/adna/governance/source_library/project_sample_chronology_review.json",
        "chronology_conflicts": "data/adna/governance/source_library/sample_chronology_conflict_ledger.json",
        "chronology_precision_audit": "data/adna/governance/source_library/sample_chronology_precision_audit.json",
        "date_evidence_gap_queue": "data/adna/governance/source_library/date_evidence_gap_queue.json",
        "project_recovery_stage_review": "data/adna/governance/source_library/project_recovery_stage_review.json",
        "project_expected_sample_yield_review": "data/adna/governance/source_library/project_expected_sample_yield_review.json",
        "paper_expected_sample_yield_review": "data/adna/governance/source_library/paper_expected_sample_yield_review.json",
        "species_project_deficit_ledger": "data/adna/governance/source_library/species_project_deficit_ledger.json",
        "manual_curation_worklist": "data/adna/governance/source_library/manual_curation_worklist.json",
        "source_recovery_progress": "data/adna/governance/source_library/source_recovery_progress.json",
        "missing_source_queue": "data/adna/governance/source_library/missing_source_queue.json",
        "source_recovery_release_guard": "data/adna/governance/source_library/source_recovery_release_guard.json",
        "animal_intake_recovery_review": "docs/report/animal_intake_recovery_review.json",
        "coordinate_provenance_example": "data/adna/species/ovis_aries/normalized/coordinate_provenance.json",
        "point_evidence_review": "docs/report/animal_point_evidence_review.md",
        "atlas_evidence_rows": "docs/report/world/world_animal_atlas_evidence.json",
        "atlas_map": "docs/report/world/world_map.html",
        "country_output_summary": "docs/report/published_reports_summary.json",
    }
    sample_database_claim_supported = all(
        (
            len(project_rows) > 0,
            len(paper_rows) > 0,
            len(supplement_rows) > 0,
            len(sample_rows) > 0,
            len(site_rows) > 0,
            len(chronology_rows) > 0,
            len(coordinate_rows) > 0,
        )
    )
    nordic_view_supported_now = all(
        (
            point_row_count >= 10,
            paper_with_archived_supplement_count >= 5,
            mapped_sample_share >= 0.05,
            normalized_chronology_count >= 100,
            bool(country_payloads),
        )
    )
    region_agnostic_contract_ready = all(
        (
            sample_database_claim_supported,
            not review_payload["blockers"],
            point_row_count >= 25,
            paper_with_archived_supplement_count == len(paper_rows),
            mapped_sample_share >= 0.2,
        )
    )
    posture_findings = []
    if point_row_count < 10:
        posture_findings.append(
            "published_atlas_point_count_below_minimum_reading_depth"
        )
    if paper_with_archived_supplement_count < 5:
        posture_findings.append("supplement_backed_paper_coverage_still_too_low")
    if mapped_sample_share < 0.05:
        posture_findings.append("mapped_sample_share_still_too_low")
    if normalized_chronology_count < 100:
        posture_findings.append("normalized_chronology_depth_still_too_thin")
    if not bool(intake_recovery_payload["release_guard"]["passing"]):
        posture_findings.append("project_recovery_release_guard_still_failing")
    blockers = list(review_payload["blockers"])
    if not bool(intake_recovery_payload["release_guard"]["passing"]):
        blockers.append("project_recovery_release_guard_still_failing")
    return {
        "schema_version": "animal-sample-database-review.v1",
        "public_posture": "partial_sample_owned_animal_evidence_surface",
        "sample_database_claim_supported": sample_database_claim_supported,
        "nordic_view_supported_now": nordic_view_supported_now,
        "region_agnostic_contract_ready": region_agnostic_contract_ready,
        "world_map_expansion_posture": (
            "not_supported_until_source_capture_site_resolution_and_chronology_depth_are_materially_stronger"
        ),
        "readiness_thresholds": {
            "minimum_published_atlas_points": 10,
            "minimum_supplement_backed_papers": 5,
            "minimum_mapped_sample_share": 0.05,
            "minimum_normalized_chronology_rows": 100,
            "minimum_region_agnostic_point_floor": 25,
            "minimum_region_agnostic_mapped_share": 0.2,
        },
        "counts": {
            "tracked_project_count": len(project_rows),
            "tracked_paper_count": len(paper_rows),
            "tracked_supplement_count": len(supplement_rows),
            "papers_with_archived_supplements": paper_with_archived_supplement_count,
            "sample_row_count": len(sample_rows),
            "site_evidence_row_count": len(site_rows),
            "sample_site_row_count": len(sample_site_rows),
            "chronology_row_count": len(chronology_rows),
            "coordinate_row_count": len(coordinate_rows),
            "published_atlas_point_count": point_payload["row_count"],
            "mapped_sample_count": mapped_sample_count,
            "published_country_bundle_count": len(country_payloads),
            "mapped_sample_share": mapped_sample_share,
            "locality_conflict_row_count": len(locality_conflict_rows),
            "locality_curation_row_count": len(locality_curation_rows),
            "locality_substitution_project_count": len(locality_substitution_rows),
            "locality_dictionary_row_count": len(locality_dictionary_rows),
        },
        "locality_status_counts": locality_status_counts,
        "locality_completeness_counts": {
            "exact_site_evidence_count": sum(
                int(row["exact_site_evidence_count"])
                for row in locality_completeness_rows
            ),
            "broader_locality_evidence_count": sum(
                int(row["broader_locality_evidence_count"])
                for row in locality_completeness_rows
            ),
            "unresolved_geography_count": sum(
                int(row["unresolved_geography_count"])
                for row in locality_completeness_rows
            ),
        },
        "chronology_status_counts": chronology_status_counts,
        "chronology_precision_counts": chronology_precision_counts,
        "intake_recovery_counts": {
            "blocked_projects": intake_recovery_payload["stage_review"][
                "blocked_projects"
            ],
            "ready_for_publication_review": intake_recovery_payload["stage_review"][
                "ready_for_publication_review"
            ],
            "implausibly_low_recovery_project_count": intake_recovery_payload[
                "release_guard"
            ]["implausibly_low_recovery_project_count"],
        },
        "posture_findings": posture_findings,
        "blockers": blockers,
        "direct_links": direct_links,
    }


def _mapped_sample_count(point_payload: dict[str, Any]) -> int:
    sample_ids: set[str] = set()
    rows = point_payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("point payload rows must be a list")
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each point payload row must be an object")
        if "sample_record_ids" in row:
            sample_record_ids = row["sample_record_ids"]
            if not isinstance(sample_record_ids, list):
                raise ValueError("sample_record_ids must be a list")
            for sample_id in sample_record_ids:
                if not isinstance(sample_id, str) or not sample_id.strip():
                    raise ValueError("sample_record_ids must contain non-empty strings")
                sample_ids.add(sample_id.strip())
            continue
        sample_rows = row.get("sample_rows")
        if not isinstance(sample_rows, list):
            raise ValueError("sample_rows must be a list")
        for sample_row in sample_rows:
            if not isinstance(sample_row, dict):
                raise ValueError("each mapped sample row must be an object")
            identity = sample_row.get("identity")
            if not isinstance(identity, dict):
                raise ValueError("mapped sample identity must be an object")
            stable_token = identity.get("stable_token")
            if not isinstance(stable_token, str) or not stable_token.strip():
                raise ValueError("mapped sample identity must contain a stable token")
            sample_ids.add(stable_token.strip())
    return len(sample_ids)
