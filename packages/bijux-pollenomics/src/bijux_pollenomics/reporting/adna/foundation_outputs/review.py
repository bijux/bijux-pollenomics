"""Animal foundation review responsibilities."""

from __future__ import annotations
from typing import Any, cast
from pathlib import Path
from ....adna.governance.audit_catalogs import (
    build_cross_species_map_readiness,
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)
from ....adna.sources.library import (
    build_cross_project_source_audit,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
)
from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .repository import (
    _build_comparator_only_rows,
    _build_coordinate_lookup,
    _build_sample_lookup,
    _build_site_lookup,
    _count_rows_by_project,
    _load_all_project_sample_site_rows,
)


def build_animal_scientific_caveat_ledger(data_root: Path) -> dict[str, Any]:
    """Group the current scientific weak points in the animal evidence foundation."""
    source_bundles = build_project_source_bundles(data_root)
    paper_registry = build_paper_registry(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    comparator_rows = _build_comparator_only_rows(data_root)
    ambiguous_sample_site_rows = [
        row
        for row in sample_site_rows
        if str(row.get("locality_resolution_status", ""))
        in {
            "sample_group_site",
            "project_level_site_only",
            "region_only",
            "unresolved",
        }
    ]
    unreadable_rows = [
        {
            "paper_doi": row.paper_doi,
            "title": row.title,
            "project_accessions": list(row.project_accessions),
            "parsing_status": row.parsing_status,
        }
        for row in paper_registry
        if row.parsing_status != "ready_for_project_sample_extraction"
    ]
    missing_supplements = [
        {
            "project_accession": bundle.project_accession,
            "species_latin_name": bundle.species_latin_name,
            "paper_doi": bundle.paper_doi,
            "paper_title": bundle.paper_title,
            "blockers": list(bundle.blockers),
        }
        for bundle in source_bundles
        if bundle.supplement_required
        and bundle.supplement_download_status != "archived"
    ]
    return {
        "schema_version": "animal-scientific-caveat-ledger.v1",
        "summary": {
            "missing_supplement_count": len(missing_supplements),
            "unreadable_table_count": len(unreadable_rows),
            "uncertain_site_assignment_count": len(ambiguous_sample_site_rows),
            "region_only_geography_count": len(overbroad_rows),
            "comparator_only_evidence_count": len(comparator_rows),
        },
        "categories": {
            "missing_supplements": missing_supplements,
            "unreadable_tables": unreadable_rows,
            "uncertain_site_assignment": ambiguous_sample_site_rows,
            "unresolved_sample_rows": list(unresolved_rows),
            "region_only_geography": list(overbroad_rows),
            "comparator_only_evidence": comparator_rows,
        },
    }


def build_animal_point_evidence_review(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    """Explain exactly why each published animal atlas point exists."""
    atlas_rows: list[dict[str, Any]] = [
        cast(dict[str, Any], row.as_dict())
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
    ]
    sample_lookup = _build_sample_lookup(data_root)
    site_lookup = _build_site_lookup(data_root)
    provenance_lookup = _build_coordinate_lookup(data_root)
    project_lookup = {
        row.project_accession: row for row in build_project_registry(data_root)
    }

    packets: list[dict[str, Any]] = []
    for row in atlas_rows:
        sample_ids = [
            str(item) for item in row.get("sample_record_ids", []) if str(item).strip()
        ]
        primary_project = str(row.get("primary_project_accession", "")).strip()
        evidence_identity = (
            primary_project,
            str(row.get("locality", "")).strip(),
            str(row.get("political_entity", "")).strip(),
        )
        packets.append(
            {
                "feature_id": row["feature_id"],
                "species_latin_name": row["species_latin_name"],
                "species_common_name": row["species_common_name"],
                "locality": row["locality"],
                "political_entity": row["political_entity"],
                "coordinate_basis": row["coordinate_basis"],
                "coordinate_confidence": row["coordinate_confidence"],
                "support_class": row["support_class"],
                "project_accession": primary_project,
                "paper_doi": row["paper_doi"],
                "paper_title": row["paper_title"],
                "paper_url": row["paper_url"],
                "supplementary_sources": list(row.get("supplementary_sources", [])),
                "exact_source_text": row["exact_source_text"],
                "source_locator": row["source_locator"],
                "sample_rows": [
                    sample_lookup[item] for item in sample_ids if item in sample_lookup
                ],
                "site_evidence": site_lookup.get(evidence_identity, {}),
                "coordinate_provenance": provenance_lookup.get(evidence_identity, {}),
                "project_registry_row": (
                    project_lookup[primary_project].as_dict()
                    if primary_project in project_lookup
                    else {}
                ),
            }
        )
    packets.sort(key=lambda row: str(row["feature_id"]))
    return {
        "schema_version": "animal-point-evidence-review.v1",
        "row_count": len(packets),
        "rows": packets,
    }


def build_animal_project_publication_gap_review(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    """Explain why tracked animal projects do not appear as published map points."""
    atlas_projects = {
        str(row.primary_project_accession)
        for row in build_tracked_animal_atlas_evidence_rows(data_root)
    }
    unresolved_counts = _count_rows_by_project(build_unresolved_site_ledger(data_root))
    overbroad_counts = _count_rows_by_project(build_overbroad_site_ledger(data_root))
    source_audit = build_cross_project_source_audit(data_root)
    bundles = {
        bundle.project_accession: bundle
        for bundle in build_project_source_bundles(data_root)
    }

    rows: list[dict[str, Any]] = []
    for registry_row in build_project_registry(data_root):
        bundle = bundles[registry_row.project_accession]
        atlas_feature_present = registry_row.project_accession in atlas_projects
        blockers = list(bundle.blockers)
        if unresolved_counts.get(registry_row.project_accession, 0):
            blockers.append("sample_context_blocked")
        if overbroad_counts.get(registry_row.project_accession, 0):
            blockers.append("region_only_geography")
        if (
            registry_row.evidence_strength == "comparator_only"
            or "comparator" in registry_row.evidence_strength
        ):
            blockers.append("comparator_only_context")
        if atlas_feature_present:
            continue
        rows.append(
            {
                "project_accession": registry_row.project_accession,
                "species_latin_name": registry_row.species_latin_name,
                "paper_doi": registry_row.primary_paper_doi,
                "project_url": registry_row.project_url,
                "archive_status": registry_row.archive_status,
                "evidence_strength": registry_row.evidence_strength,
                "ingestion_status": registry_row.ingestion_status,
                "paper_download_status": registry_row.paper_download_status,
                "supplement_download_status": registry_row.supplement_download_status,
                "unresolved_sample_count": unresolved_counts.get(
                    registry_row.project_accession, 0
                ),
                "region_only_site_count": overbroad_counts.get(
                    registry_row.project_accession, 0
                ),
                "blockers": sorted(set(blockers)),
                "absence_stage": _absence_stage_for(blockers),
            }
        )
    rows.sort(
        key=lambda row: (str(row["species_latin_name"]), str(row["project_accession"]))
    )
    return {
        "schema_version": "animal-project-publication-gap-review.v1",
        "source_audit": source_audit,
        "row_count": len(rows),
        "rows": rows,
    }


def build_animal_foundation_review_packet(
    *,
    data_root: Path,
    report_root: Path,
    validation_payload: dict[str, Any],
    drift_payload: dict[str, Any],
    caveat_payload: dict[str, Any],
    point_payload: dict[str, Any],
    absence_payload: dict[str, Any],
) -> dict[str, Any]:
    """Summarize the current public scientific posture of the animal evidence foundation."""
    readiness = build_cross_species_map_readiness(data_root)
    readiness_totals = cast(dict[str, Any], readiness["totals"])
    direct_points = int(readiness_totals["direct_coordinate_backed"])
    geocoded_points = int(readiness_totals["indirectly_geocoded"])
    unresolved = int(readiness_totals["unresolved"])
    refused = int(readiness_totals["refused_from_mapping"])
    reference_grade_claim_allowed = (
        validation_payload["overall_ok"]
        and not drift_payload["drift_detected"]
        and direct_points > 0
        and geocoded_points == 0
        and unresolved == 0
        and refused == 0
    )
    posture = (
        "reference_grade_claim_allowed"
        if reference_grade_claim_allowed
        else "governed_metadata_foundation_not_reference_grade"
    )
    strengths = []
    if point_payload["row_count"]:
        strengths.append(
            "published animal atlas points remain fully traceable to sample, project, paper, and site evidence rows"
        )
    if validation_payload["checks"][0]["passed"]:
        strengths.append(
            "curated sample rows keep stable identifiers without duplication"
        )
    if validation_payload["checks"][-1]["passed"]:
        strengths.append(
            "published atlas rows keep project, paper, and sample traceability"
        )
    blockers = []
    if not validation_payload["overall_ok"]:
        blockers.append("foundation_validation_not_yet_clean")
    if drift_payload["drift_detected"]:
        blockers.append("cross_surface_drift_detected")
    if unresolved:
        blockers.append("unresolved_site_assignment_rows_remain")
    if refused:
        blockers.append("region_only_geography_rows_remain")
    if geocoded_points:
        blockers.append("published_points_still_depend_on_named_site_geocoding")
    return {
        "schema_version": "animal-foundation-review.v1",
        "public_posture": posture,
        "reference_grade_claim_allowed": reference_grade_claim_allowed,
        "strengths": strengths,
        "blockers": blockers,
        "counts": {
            "published_point_count": point_payload["row_count"],
            "direct_coordinate_point_count": direct_points,
            "geocoded_point_count": geocoded_points,
            "unresolved_sample_count": unresolved,
            "region_only_refusal_count": refused,
            "blocked_project_count": absence_payload["row_count"],
        },
        "validation_overall_ok": validation_payload["overall_ok"],
        "drift_detected": drift_payload["drift_detected"],
        "caveat_summary": caveat_payload["summary"],
    }


def _absence_stage_for(blockers: list[str]) -> str:
    blocker_set = set(blockers)
    if (
        "missing_local_paper_evidence" in blocker_set
        or "paper_linkage_not_curated" in blocker_set
    ):
        return "paper_or_metadata_capture"
    if "missing_local_supplementary_material" in blocker_set:
        return "supplement_capture"
    if "sample_context_blocked" in blocker_set:
        return "site_extraction"
    if "region_only_geography" in blocker_set:
        return "coordinate_resolution"
    if "comparator_only_context" in blocker_set:
        return "comparator_context_only"
    return "not_point_publishable"
