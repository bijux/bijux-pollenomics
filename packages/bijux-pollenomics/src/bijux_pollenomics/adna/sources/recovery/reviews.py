from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from bijux_pollenomics.adna.workflow.paths import ADNA_SOURCE_LIBRARY_DIR

from bijux_pollenomics.adna.projects.evidence.chronology import (
    build_date_evidence_gap_queue,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
)
from bijux_pollenomics.adna.projects.evidence.localities import (
    build_sample_locality_manual_curation_workflow_rows,
)
from bijux_pollenomics.adna.projects.sample_master import (
    build_sample_identity_ambiguity_ledger,
)
from bijux_pollenomics.adna.projects.registry.sites import (
    build_sample_site_manual_curation_queue,
)
from bijux_pollenomics.adna.sources.library.registries import (
    build_paper_registry,
)

from .assembly import _project_recovery_rows
from .constants import ADNA_INTAKE_STAGE_KEYS
from .metrics import (
    _cache_key,
    _count_rows,
    _dynamic_row,
    _int_value,
    _nonempty_paths,
    _project_species,
    _sample_evidence_depth_counts,
)
from .policy import (
    _missing_source_queue_category,
    _missing_source_queue_reason,
    _paper_yield_recovery_posture,
)


def build_project_recovery_stage_review(output_root: Path) -> dict[str, Any]:
    """Describe the governed intake stage posture for every tracked animal project."""
    rows = _project_recovery_rows(output_root)
    summary = {
        "complete_projects": 0,
        "blocked_projects": 0,
        "in_progress_projects": 0,
        "ready_for_publication_review": 0,
    }
    stage_totals = {
        stage: {"complete": 0, "blocked": 0, "in_progress": 0, "not_required": 0}
        for stage in ADNA_INTAKE_STAGE_KEYS
    }
    for row in rows:
        overall = str(row["overall_recovery_status"])
        if overall in summary:
            summary[overall] += 1
        for stage, status in row["stage_statuses"].items():
            stage_totals[str(stage)][str(status)] += 1
    return {
        "schema_version": "animal-project-recovery-stage-review.v1",
        "row_count": len(rows),
        "summary": summary,
        "stage_totals": stage_totals,
        "rows": rows,
    }


def build_project_expected_sample_yield_review(output_root: Path) -> dict[str, Any]:
    """Publish one per-project sample-yield and under-recovery review."""
    rows = _project_recovery_rows(output_root)
    exact_expected_total = sum(
        _int_value(row["expected_sample_count"])
        for row in rows
        if row["expected_sample_count"] is not None
    )
    recovered_total = sum(_int_value(row["final_sample_count"]) for row in rows)
    minimum_gap_total = sum(_int_value(row["minimum_gap_count"] or 0) for row in rows)
    implausibly_low_rows = [
        row for row in rows if bool(row["implausibly_low_recovery"])
    ]
    return {
        "schema_version": "animal-project-expected-sample-yield-review.v1",
        "row_count": len(rows),
        "counts": {
            "tracked_project_count": len(rows),
            "projects_with_exact_expected_count": sum(
                1 for row in rows if row["expected_sample_count"] is not None
            ),
            "projects_with_minimum_expected_floor": sum(
                1 for row in rows if row["minimum_expected_sample_count"] is not None
            ),
            "projects_with_implausibly_low_recovery": len(implausibly_low_rows),
            "exact_expected_sample_total": exact_expected_total,
            "recovered_final_sample_total": recovered_total,
            "minimum_gap_total": minimum_gap_total,
        },
        "rows": rows,
    }


def build_paper_expected_sample_yield_review(output_root: Path) -> dict[str, Any]:
    """Aggregate project-level recovery posture into one paper-by-paper sample-yield review."""
    project_rows = build_project_expected_sample_yield_review(output_root)["rows"]
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in project_rows:
        paper_doi = str(row.get("paper_doi") or "").strip()
        if not paper_doi:
            continue
        grouped.setdefault(paper_doi, []).append(row)

    rows: list[dict[str, Any]] = []
    for paper_doi, items in sorted(grouped.items()):
        paper_row = paper_rows.get(paper_doi)
        rows.append(
            {
                "paper_doi": paper_doi,
                "paper_title": "" if paper_row is None else paper_row.title,
                "project_accessions": sorted(
                    str(item["project_accession"]) for item in items
                ),
                "sample_extractability": (
                    "unknown" if paper_row is None else paper_row.sample_extractability
                ),
                "article_download_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.article_download_status
                ),
                "supplementary_download_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.supplementary_download_status
                ),
                "supplement_parse_status": (
                    "unknown"
                    if paper_row is None
                    else paper_row.supplement_parse_status
                ),
                "recovered_final_sample_count": sum(
                    _int_value(item["final_sample_count"]) for item in items
                ),
                "exact_expected_sample_count_total": sum(
                    _int_value(item["expected_sample_count"])
                    for item in items
                    if item["expected_sample_count"] is not None
                ),
                "projects_with_unknown_expected_total": sum(
                    1 for item in items if item["expected_sample_count"] is None
                ),
                "projects_with_implausibly_low_recovery": sum(
                    1 for item in items if bool(item["implausibly_low_recovery"])
                ),
                "yield_recovery_posture": _paper_yield_recovery_posture(items),
                "expected_contribution_surfaces": sorted(
                    {
                        surface
                        for item in items
                        for surface in item["expected_contribution_surfaces"]
                    }
                ),
            }
        )
    return {
        "schema_version": "animal-paper-expected-sample-yield-review.v1",
        "row_count": len(rows),
        "counts": {
            "paper_rows_with_implausibly_low_recovery": sum(
                1
                for row in rows
                if _int_value(row["projects_with_implausibly_low_recovery"]) > 0
            ),
            "paper_rows_with_unknown_expected_totals": sum(
                1
                for row in rows
                if _int_value(row["projects_with_unknown_expected_total"]) > 0
            ),
        },
        "rows": rows,
    }


def build_species_project_deficit_ledger(output_root: Path) -> dict[str, Any]:
    """Quantify sample, site, chronology, and publication deficits project by project within each species."""
    rows = _project_recovery_rows(output_root)
    species_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        species = str(row["species_latin_name"])
        counts = species_counts.setdefault(
            species,
            {
                "project_count": 0,
                "projects_with_sample_gap": 0,
                "projects_with_site_gap": 0,
                "projects_with_chronology_gap": 0,
                "projects_blocked_before_publication": 0,
            },
        )
        counts["project_count"] += 1
        if _int_value(row["minimum_gap_count"] or 0) > 0:
            counts["projects_with_sample_gap"] += 1
        if _int_value(row["lacking_defensible_site_assignment_count"]) > 0:
            counts["projects_with_site_gap"] += 1
        if _int_value(row["missing_chronology_count"]) > 0:
            counts["projects_with_chronology_gap"] += 1
        if str(row["publication_readiness_status"]) != "complete":
            counts["projects_blocked_before_publication"] += 1
    payload_rows = [
        {
            "species_latin_name": str(row["species_latin_name"]),
            "project_accession": str(row["project_accession"]),
            "paper_doi": row["paper_doi"],
            "final_sample_count": row["final_sample_count"],
            "expected_sample_count": row["expected_sample_count"],
            "minimum_expected_sample_count": row["minimum_expected_sample_count"],
            "minimum_gap_count": row["minimum_gap_count"],
            "lacking_defensible_site_assignment_count": row[
                "lacking_defensible_site_assignment_count"
            ],
            "missing_chronology_count": row["missing_chronology_count"],
            "chronology_conflict_count": row["chronology_conflict_count"],
            "chronology_ambiguity_count": row["chronology_ambiguity_count"],
            "coordinate_blocked_count": row["coordinate_blocked_count"],
            "publication_readiness_status": row["publication_readiness_status"],
            "major_deficit_reasons": row["major_deficit_reasons"],
        }
        for row in rows
    ]
    return {
        "schema_version": "animal-species-project-deficit-ledger.v1",
        "row_count": len(payload_rows),
        "species_counts": species_counts,
        "rows": payload_rows,
    }


def build_manual_curation_worklist(output_root: Path) -> dict[str, Any]:
    """Track real governed curation work units rather than loose narrative blockers."""
    return _build_manual_curation_worklist_cached(_cache_key(output_root))


@lru_cache(maxsize=8)
def _build_manual_curation_worklist_cached(output_root_key: str) -> dict[str, Any]:
    output_root = Path(output_root_key)
    chronology_gap_rows = {
        str(row["project_accession"]): _dynamic_row(row)
        for row in build_date_evidence_gap_queue(output_root)
    }
    chronology_ambiguity_counts = _count_rows(
        build_sample_chronology_ambiguity_ledger(output_root),
        key="project_accession",
    )
    chronology_conflict_counts = _count_rows(
        build_sample_chronology_conflict_ledger(output_root),
        key="project_accession",
    )
    identity_ambiguity_counts = _count_rows(
        build_sample_identity_ambiguity_ledger(output_root),
        key="project_accession",
    )

    rows: list[dict[str, Any]] = []
    for source_row in build_sample_site_manual_curation_queue(output_root):
        row = _dynamic_row(source_row)
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "work_unit_type": "site_resolution",
                "work_unit_state": "pending_manual_curation",
                "open_item_count": row["queued_sample_count"],
                "rationale": "; ".join(row["queue_reasons"]),
                "downstream_impact": "blocks exact site, coordinate, and publication recovery",
                "recommended_source_surfaces": _nonempty_paths(
                    list(row["sample_site_targets"])
                    + list(row["expected_supplementary_artifacts"])
                    + list(row["local_artifact_paths"])
                ),
            }
        )
    for source_row in build_sample_locality_manual_curation_workflow_rows(output_root):
        row = _dynamic_row(source_row)
        rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "work_unit_type": "locality_string_resolution",
                "work_unit_state": row["decision_status"],
                "open_item_count": row["queued_sample_count"],
                "rationale": row["locality_resolution_status"]
                if not str(row["decision_rationale"]).strip()
                else row["decision_rationale"],
                "downstream_impact": "blocks coordinate derivation and exact locality publication",
                "recommended_source_surfaces": _nonempty_paths(
                    list(row["recommended_source_surfaces"])
                ),
            }
        )
    for project_accession, gap_row in chronology_gap_rows.items():
        open_item_count = (
            _int_value(gap_row["missing_date_count"])
            + _int_value(chronology_ambiguity_counts.get(project_accession, 0))
            + _int_value(chronology_conflict_counts.get(project_accession, 0))
        )
        if open_item_count <= 0:
            continue
        rows.append(
            {
                "project_accession": project_accession,
                "species_latin_name": gap_row["species_latin_name"],
                "work_unit_type": "chronology_recovery",
                "work_unit_state": "pending_source_recovery",
                "open_item_count": open_item_count,
                "rationale": "; ".join(gap_row["gap_reasons"]),
                "downstream_impact": "blocks chronology honesty and publication precision",
                "recommended_source_surfaces": [
                    f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/sample_chronology.json",
                    f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/intake_dossier.json",
                ],
            }
        )
    for project_accession, ambiguity_count in identity_ambiguity_counts.items():
        if _int_value(ambiguity_count) <= 0:
            continue
        rows.append(
            {
                "project_accession": project_accession,
                "species_latin_name": _project_species(project_accession),
                "work_unit_type": "sample_identity_resolution",
                "work_unit_state": "pending_manual_curation",
                "open_item_count": _int_value(ambiguity_count),
                "rationale": "Stable sample identity rows still carry unresolved ambiguity.",
                "downstream_impact": "blocks trustworthy project-level sample recovery counts",
                "recommended_source_surfaces": [
                    f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/sample_master.json"
                ],
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["species_latin_name"]),
            str(item["project_accession"]),
            str(item["work_unit_type"]),
        )
    )
    return {
        "schema_version": "animal-manual-curation-worklist.v1",
        "row_count": len(rows),
        "counts": _count_rows(rows, key="work_unit_type"),
        "rows": rows,
    }


def build_source_recovery_progress(output_root: Path) -> dict[str, Any]:
    """Measure project completeness and sample evidence depth without using raw row growth as a proxy."""
    rows = _project_recovery_rows(output_root)
    sample_depth_counts = _sample_evidence_depth_counts(output_root)
    return {
        "schema_version": "animal-source-recovery-progress.v1",
        "project_count": len(rows),
        "sample_evidence_depth_counts": sample_depth_counts,
        "project_counts": {
            "projects_with_sample_identity_rows": sum(
                1 for row in rows if _int_value(row["final_sample_count"]) > 0
            ),
            "projects_with_defensible_site_rows": sum(
                1
                for row in rows
                if _int_value(row["final_sample_count"]) > 0
                and _int_value(row["lacking_defensible_site_assignment_count"]) == 0
            ),
            "projects_with_sample_owned_chronology": sum(
                1
                for row in rows
                if _int_value(row["final_sample_count"]) > 0
                and _int_value(row["missing_chronology_count"]) == 0
            ),
            "projects_with_mappable_coordinates": sum(
                1 for row in rows if _int_value(row["mappable_coordinate_count"]) > 0
            ),
            "projects_ready_for_publication_review": sum(
                1
                for row in rows
                if str(row["publication_readiness_status"]) == "complete"
            ),
        },
        "rows": [
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "completed_stage_count": row["completed_stage_count"],
                "required_stage_count": row["required_stage_count"],
                "recovery_depth_score": row["recovery_depth_score"],
                "final_sample_count": row["final_sample_count"],
                "minimum_gap_count": row["minimum_gap_count"],
                "publication_readiness_status": row["publication_readiness_status"],
            }
            for row in rows
        ],
    }


def build_missing_source_queue(output_root: Path) -> dict[str, Any]:
    """Make missing paper, supplement, and sub-study capture gaps explicit and actionable."""
    rows = _project_recovery_rows(output_root)
    queued_rows = []
    for row in rows:
        category = _missing_source_queue_category(row)
        if category == "not_queued":
            continue
        queued_rows.append(
            {
                "project_accession": row["project_accession"],
                "species_latin_name": row["species_latin_name"],
                "paper_doi": row["paper_doi"],
                "queue_category": category,
                "expected_contributions": row["expected_contributions"],
                "expected_contribution_surfaces": row["expected_contribution_surfaces"],
                "current_capture_state": row["evidence_acquisition_state"],
                "queue_reason": _missing_source_queue_reason(category, row),
            }
        )
    return {
        "schema_version": "animal-missing-source-queue.v1",
        "row_count": len(queued_rows),
        "counts": _count_rows(queued_rows, key="queue_category"),
        "rows": queued_rows,
    }


def build_source_recovery_release_guard(output_root: Path) -> dict[str, Any]:
    """Fail when project recovery posture is too weak to support intake credibility claims."""
    rows = build_project_expected_sample_yield_review(output_root)["rows"]
    failing_projects = [
        {
            "project_accession": row["project_accession"],
            "species_latin_name": row["species_latin_name"],
            "recovery_gap_status": row["recovery_gap_status"],
            "implausibly_low_recovery_reason": row["implausibly_low_recovery_reason"],
        }
        for row in rows
        if bool(row["implausibly_low_recovery"])
    ]
    return {
        "schema_version": "animal-source-recovery-release-guard.v1",
        "passing": len(failing_projects) == 0,
        "implausibly_low_recovery_project_count": len(failing_projects),
        "failing_projects": failing_projects,
    }


def build_project_recovery_dossier(
    output_root: Path,
    project_accession: str,
) -> dict[str, Any]:
    """Build one authoritative per-project recovery dossier."""
    rows = {
        str(row["project_accession"]): row
        for row in _project_recovery_rows(output_root)
    }
    row = rows[project_accession]
    manual_rows = [
        item
        for item in build_manual_curation_worklist(output_root)["rows"]
        if str(item["project_accession"]) == project_accession
    ]
    contradictory_evidence = []
    if _int_value(row["chronology_conflict_count"]) > 0:
        contradictory_evidence.append(
            f"{row['chronology_conflict_count']} chronology row(s) still disagree between sample-owned and context-level evidence."
        )
    if bool(row["publication_blocked_by_locality_substitution"]):
        contradictory_evidence.append(
            "Locality substitution review still blocks publication because project-level geography would flatten distinct sample evidence."
        )
    inferred_claims = []
    if _int_value(row["named_place_inferred_count"]) > 0:
        inferred_claims.append(
            f"{row['named_place_inferred_count']} site row(s) still depend on named-place inference."
        )
    if _int_value(row["sample_group_site_count"]) > 0:
        inferred_claims.append(
            f"{row['sample_group_site_count']} site row(s) still resolve only at a sample-group level."
        )
    return {
        "schema_version": "animal-project-recovery-dossier.v1",
        "project_accession": row["project_accession"],
        "species_latin_name": row["species_latin_name"],
        "paper_doi": row["paper_doi"],
        "archive_status": row["archive_status"],
        "evidence_strength": row["evidence_strength"],
        "inventory_disposition": row["inventory_disposition"],
        "stage_statuses": row["stage_statuses"],
        "blocking_stages": row["blocking_stages"],
        "next_required_stage": row["next_required_stage"],
        "publication_readiness_status": row["publication_readiness_status"],
        "expected_sample_count": row["expected_sample_count"],
        "expected_sample_count_status": row["expected_sample_count_status"],
        "expected_sample_count_provenance": row["expected_sample_count_provenance"],
        "expected_sample_count_artifact_path": row[
            "expected_sample_count_artifact_path"
        ],
        "minimum_expected_sample_count": row["minimum_expected_sample_count"],
        "recovered_sample_count": row["recovered_sample_count"],
        "final_sample_count": row["final_sample_count"],
        "unresolved_sample_count": row["unresolved_sample_count"],
        "minimum_gap_count": row["minimum_gap_count"],
        "recovery_gap_status": row["recovery_gap_status"],
        "implausibly_low_recovery": row["implausibly_low_recovery"],
        "implausibly_low_recovery_reason": row["implausibly_low_recovery_reason"],
        "known_assets": row["known_assets"],
        "missing_assets": row["missing_assets"],
        "expected_contributions": row["expected_contributions"],
        "expected_contribution_surfaces": row["expected_contribution_surfaces"],
        "contradictory_evidence": contradictory_evidence,
        "inferred_claims": inferred_claims,
        "manual_curation_work_units": manual_rows,
        "major_deficit_reasons": row["major_deficit_reasons"],
    }
