from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from ..projects.sample_chronology import (
    build_date_evidence_gap_queue,
    build_project_sample_chronology_review_rows,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
)
from ..projects.sample_locality_evidence import (
    build_project_locality_substitution_ledger,
    build_sample_locality_manual_curation_workflow_rows,
)
from ..projects.sample_master import (
    build_cross_project_sample_master_completeness,
    build_sample_identity_ambiguity_ledger,
)
from ..projects.sample_sites import (
    build_project_sample_site_review_rows,
    build_sample_site_manual_curation_queue,
)
from .ena import build_archive_project_catalog
from .library import (
    ADNA_SOURCE_LIBRARY_DIR,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
)

__all__ = [
    "ADNA_INTAKE_STAGE_KEYS",
    "build_manual_curation_worklist",
    "build_missing_source_queue",
    "build_paper_expected_sample_yield_review",
    "build_project_expected_sample_yield_review",
    "build_project_recovery_dossier",
    "build_project_recovery_stage_review",
    "build_source_recovery_progress",
    "build_source_recovery_release_guard",
    "build_species_project_deficit_ledger",
    "render_manual_curation_worklist_markdown",
    "render_missing_source_queue_markdown",
    "render_paper_expected_sample_yield_review_markdown",
    "render_project_expected_sample_yield_review_markdown",
    "render_project_recovery_dossier_markdown",
    "render_project_recovery_stage_review_markdown",
    "render_source_recovery_progress_markdown",
    "render_source_recovery_release_guard_markdown",
    "render_species_project_deficit_ledger_markdown",
]

ADNA_INTAKE_STAGE_KEYS = (
    "project_admission",
    "paper_capture",
    "supplement_capture",
    "sample_identity_recovery",
    "site_recovery",
    "chronology_recovery",
    "coordinate_derivation",
    "publication_readiness",
)


def build_project_recovery_stage_review(output_root: Path) -> dict[str, object]:
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


def build_project_expected_sample_yield_review(output_root: Path) -> dict[str, object]:
    """Publish one per-project sample-yield and under-recovery review."""
    rows = _project_recovery_rows(output_root)
    exact_expected_total = sum(
        int(row["expected_sample_count"])
        for row in rows
        if row["expected_sample_count"] is not None
    )
    recovered_total = sum(int(row["final_sample_count"]) for row in rows)
    minimum_gap_total = sum(int(row["minimum_gap_count"] or 0) for row in rows)
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


def build_paper_expected_sample_yield_review(output_root: Path) -> dict[str, object]:
    """Aggregate project-level recovery posture into one paper-by-paper sample-yield review."""
    project_rows = build_project_expected_sample_yield_review(output_root)["rows"]
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in project_rows:
        paper_doi = str(row.get("paper_doi") or "").strip()
        if not paper_doi:
            continue
        grouped.setdefault(paper_doi, []).append(row)

    rows: list[dict[str, object]] = []
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
                    int(item["final_sample_count"]) for item in items
                ),
                "exact_expected_sample_count_total": sum(
                    int(item["expected_sample_count"])
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
                if int(row["projects_with_implausibly_low_recovery"]) > 0
            ),
            "paper_rows_with_unknown_expected_totals": sum(
                1
                for row in rows
                if int(row["projects_with_unknown_expected_total"]) > 0
            ),
        },
        "rows": rows,
    }


def build_species_project_deficit_ledger(output_root: Path) -> dict[str, object]:
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
        if int(row["minimum_gap_count"] or 0) > 0:
            counts["projects_with_sample_gap"] += 1
        if int(row["lacking_defensible_site_assignment_count"]) > 0:
            counts["projects_with_site_gap"] += 1
        if int(row["missing_chronology_count"]) > 0:
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


def build_manual_curation_worklist(output_root: Path) -> dict[str, object]:
    """Track real governed curation work units rather than loose narrative blockers."""
    return _build_manual_curation_worklist_cached(_cache_key(output_root))


@lru_cache(maxsize=8)
def _build_manual_curation_worklist_cached(output_root_key: str) -> dict[str, object]:
    output_root = Path(output_root_key)
    chronology_gap_rows = {
        str(row["project_accession"]): row
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

    rows: list[dict[str, object]] = []
    for row in build_sample_site_manual_curation_queue(output_root):
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
    for row in build_sample_locality_manual_curation_workflow_rows(output_root):
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
            int(gap_row["missing_date_count"])
            + int(chronology_ambiguity_counts.get(project_accession, 0))
            + int(chronology_conflict_counts.get(project_accession, 0))
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
        if int(ambiguity_count) <= 0:
            continue
        rows.append(
            {
                "project_accession": project_accession,
                "species_latin_name": _project_species(project_accession),
                "work_unit_type": "sample_identity_resolution",
                "work_unit_state": "pending_manual_curation",
                "open_item_count": int(ambiguity_count),
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


def build_source_recovery_progress(output_root: Path) -> dict[str, object]:
    """Measure project completeness and sample evidence depth without using raw row growth as a proxy."""
    rows = _project_recovery_rows(output_root)
    sample_depth_counts = _sample_evidence_depth_counts(output_root)
    return {
        "schema_version": "animal-source-recovery-progress.v1",
        "project_count": len(rows),
        "sample_evidence_depth_counts": sample_depth_counts,
        "project_counts": {
            "projects_with_sample_identity_rows": sum(
                1 for row in rows if int(row["final_sample_count"]) > 0
            ),
            "projects_with_defensible_site_rows": sum(
                1
                for row in rows
                if int(row["final_sample_count"]) > 0
                and int(row["lacking_defensible_site_assignment_count"]) == 0
            ),
            "projects_with_sample_owned_chronology": sum(
                1
                for row in rows
                if int(row["final_sample_count"]) > 0
                and int(row["missing_chronology_count"]) == 0
            ),
            "projects_with_mappable_coordinates": sum(
                1 for row in rows if int(row["mappable_coordinate_count"]) > 0
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


def build_missing_source_queue(output_root: Path) -> dict[str, object]:
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


def build_source_recovery_release_guard(output_root: Path) -> dict[str, object]:
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
) -> dict[str, object]:
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
    if int(row["chronology_conflict_count"]) > 0:
        contradictory_evidence.append(
            f"{row['chronology_conflict_count']} chronology row(s) still disagree between sample-owned and context-level evidence."
        )
    if bool(row["publication_blocked_by_locality_substitution"]):
        contradictory_evidence.append(
            "Locality substitution review still blocks publication because project-level geography would flatten distinct sample evidence."
        )
    inferred_claims = []
    if int(row["named_place_inferred_count"]) > 0:
        inferred_claims.append(
            f"{row['named_place_inferred_count']} site row(s) still depend on named-place inference."
        )
    if int(row["sample_group_site_count"]) > 0:
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


def render_project_recovery_stage_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Project recovery stage review",
        "",
        f"- Tracked projects: `{payload['row_count']}`",
        f"- Ready for publication review: `{payload['summary']['ready_for_publication_review']}`",
        f"- Blocked projects: `{payload['summary']['blocked_projects']}`",
        "",
        "| Project | Species | Recovery status | Next required stage | Blocking stages |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['overall_recovery_status']}` | `{row['next_required_stage'] or 'none'}` | "
            f"`{'; '.join(row['blocking_stages']) or 'none'}` |"
        )
    return "\n".join(lines) + "\n"


def render_project_expected_sample_yield_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Project expected sample yield review",
        "",
        f"- Tracked projects: `{payload['counts']['tracked_project_count']}`",
        f"- Projects with exact expected counts: `{payload['counts']['projects_with_exact_expected_count']}`",
        f"- Projects with a minimum expected floor: `{payload['counts']['projects_with_minimum_expected_floor']}`",
        f"- Implausibly low recovery projects: `{payload['counts']['projects_with_implausibly_low_recovery']}`",
        "",
        "| Project | Species | Exact expected | Minimum expected | Final rows | Gap status | Implausibly low |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"{row['expected_sample_count'] if row['expected_sample_count'] is not None else '-'} | "
            f"{row['minimum_expected_sample_count'] if row['minimum_expected_sample_count'] is not None else '-'} | "
            f"{row['final_sample_count']} | `{row['recovery_gap_status']}` | "
            f"`{str(bool(row['implausibly_low_recovery'])).lower()}` |"
        )
    return "\n".join(lines) + "\n"


def render_paper_expected_sample_yield_review_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Paper expected sample yield review",
        "",
        f"- Paper rows: `{payload['row_count']}`",
        "",
        "| Paper DOI | Projects | Sample extractability | Recovered rows | Unknown expected totals | Implausibly low projects |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['paper_doi']}` | `{'; '.join(row['project_accessions'])}` | "
            f"`{row['sample_extractability']}` | `{row['recovered_final_sample_count']}` | "
            f"`{row['projects_with_unknown_expected_total']}` | "
            f"`{row['projects_with_implausibly_low_recovery']}` |"
        )
    return "\n".join(lines) + "\n"


def render_species_project_deficit_ledger_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Species project deficit ledger",
        "",
        f"- Project rows: `{payload['row_count']}`",
        "",
        "| Species | Project | Minimum sample gap | Site gap | Chronology gap | Publication status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['species_latin_name']}` | `{row['project_accession']}` | "
            f"`{row['minimum_gap_count'] or 0}` | "
            f"`{row['lacking_defensible_site_assignment_count']}` | "
            f"`{row['missing_chronology_count']}` | "
            f"`{row['publication_readiness_status']}` |"
        )
    return "\n".join(lines) + "\n"


def render_manual_curation_worklist_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Manual curation worklist",
        "",
        f"- Work units: `{payload['row_count']}`",
        "",
        "| Project | Species | Work unit | State | Open items | Impact |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['work_unit_type']}` | `{row['work_unit_state']}` | "
            f"`{row['open_item_count']}` | {row['downstream_impact']} |"
        )
    return "\n".join(lines) + "\n"


def render_source_recovery_progress_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Source recovery progress",
        "",
        f"- Tracked projects: `{payload['project_count']}`",
        f"- Sample identity rows present: `{payload['project_counts']['projects_with_sample_identity_rows']}`",
        f"- Defensible site rows present: `{payload['project_counts']['projects_with_defensible_site_rows']}`",
        f"- Sample-owned chronology present: `{payload['project_counts']['projects_with_sample_owned_chronology']}`",
        f"- Mappable coordinate projects: `{payload['project_counts']['projects_with_mappable_coordinates']}`",
        f"- Ready for publication review: `{payload['project_counts']['projects_ready_for_publication_review']}`",
        "",
        "## Sample Evidence Depth",
        "",
    ]
    for key, value in payload["sample_evidence_depth_counts"].items():
        lines.append(f"- {key.replace('_', ' ')}: `{value}`")
    lines.extend(
        [
            "",
            "| Project | Species | Completed stages | Required stages | Recovery depth score |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['completed_stage_count']}` | `{row['required_stage_count']}` | "
            f"`{row['recovery_depth_score']}` |"
        )
    return "\n".join(lines) + "\n"


def render_missing_source_queue_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Missing source queue",
        "",
        f"- Queued rows: `{payload['row_count']}`",
        "",
        "| Project | Species | Queue category | Expected contributions | Reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['queue_category']}` | `{'; '.join(row['expected_contributions'])}` | "
            f"{row['queue_reason']} |"
        )
    return "\n".join(lines) + "\n"


def render_source_recovery_release_guard_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Source recovery release guard",
        "",
        f"- Passing: `{str(payload['passing']).lower()}`",
        f"- Implausibly low recovery projects: `{payload['implausibly_low_recovery_project_count']}`",
        "",
    ]
    if payload["failing_projects"]:
        lines.extend(
            [
                "| Project | Species | Gap status | Reason |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in payload["failing_projects"]:
            lines.append(
                f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
                f"`{row['recovery_gap_status']}` | {row['implausibly_low_recovery_reason']} |"
            )
    return "\n".join(lines) + "\n"


def render_project_recovery_dossier_markdown(payload: dict[str, object]) -> str:
    lines = [
        f"# {payload['project_accession']} recovery dossier",
        "",
        f"- Species: `{payload['species_latin_name']}`",
        f"- Archive status: `{payload['archive_status']}`",
        f"- Inventory disposition: `{payload['inventory_disposition']}`",
        f"- Paper DOI: `{payload['paper_doi'] or 'none'}`",
        f"- Publication readiness: `{payload['publication_readiness_status']}`",
        f"- Next required stage: `{payload['next_required_stage'] or 'none'}`",
        f"- Exact expected sample count: `{payload['expected_sample_count'] if payload['expected_sample_count'] is not None else 'unknown'}`",
        f"- Minimum expected sample count: `{payload['minimum_expected_sample_count'] if payload['minimum_expected_sample_count'] is not None else 'unknown'}`",
        f"- Final recovered sample rows: `{payload['final_sample_count']}`",
        f"- Minimum recovery gap: `{payload['minimum_gap_count'] or 0}`",
        f"- Implausibly low recovery: `{str(bool(payload['implausibly_low_recovery'])).lower()}`",
        "",
        "## Stage Statuses",
        "",
    ]
    for stage in ADNA_INTAKE_STAGE_KEYS:
        lines.append(f"- `{stage}`: `{payload['stage_statuses'][stage]}`")
    lines.extend(
        [
            "",
            "## Expected Contributions",
            "",
        ]
    )
    for item in payload["expected_contributions"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Known Assets",
            "",
        ]
    )
    for item in payload["known_assets"] or ["none"]:
        lines.append(f"- `{item}`" if item != "none" else "- none")
    lines.extend(
        [
            "",
            "## Missing Assets",
            "",
        ]
    )
    for item in payload["missing_assets"] or ["none"]:
        lines.append(f"- {item}" if item != "none" else "- none")
    if payload["contradictory_evidence"]:
        lines.extend(["", "## Contradictory Evidence", ""])
        for item in payload["contradictory_evidence"]:
            lines.append(f"- {item}")
    if payload["inferred_claims"]:
        lines.extend(["", "## Inferred Claims", ""])
        for item in payload["inferred_claims"]:
            lines.append(f"- {item}")
    if payload["manual_curation_work_units"]:
        lines.extend(["", "## Manual Curation Work Units", ""])
        for item in payload["manual_curation_work_units"]:
            lines.append(
                f"- `{item['work_unit_type']}`: {item['open_item_count']} item(s), {item['downstream_impact']}"
            )
    return "\n".join(lines) + "\n"


def _project_recovery_rows(output_root: Path) -> list[dict[str, object]]:
    return list(_project_recovery_rows_cached(_cache_key(output_root)))


@lru_cache(maxsize=8)
def _project_recovery_rows_cached(
    output_root_key: str,
) -> tuple[dict[str, object], ...]:
    output_root = Path(output_root_key)
    project_rows = list(build_project_registry(output_root))
    bundles = {
        bundle.project_accession: bundle
        for bundle in build_project_source_bundles(output_root)
    }
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    sample_master_rows = {
        row["project_accession"]: row
        for row in build_cross_project_sample_master_completeness(output_root)
    }
    site_review_rows = {
        row["project_accession"]: row
        for row in build_project_sample_site_review_rows(output_root)
    }
    chronology_review_rows = {
        row["project_accession"]: row
        for row in build_project_sample_chronology_review_rows(output_root)
    }
    chronology_gap_rows = {
        row["project_accession"]: row
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
    locality_substitution_rows = {
        row["project_accession"]: row
        for row in build_project_locality_substitution_ledger(output_root)
    }
    coordinate_counts = _coordinate_counts_by_project(output_root)

    rows: list[dict[str, object]] = []
    for project_row in project_rows:
        bundle = bundles[project_row.project_accession]
        paper_row = (
            None
            if project_row.primary_paper_doi is None
            else paper_rows.get(project_row.primary_paper_doi)
        )
        sample_master_row = sample_master_rows.get(project_row.project_accession, {})
        site_row = site_review_rows.get(project_row.project_accession, {})
        chronology_row = chronology_review_rows.get(project_row.project_accession, {})
        gap_row = chronology_gap_rows.get(project_row.project_accession, {})
        substitution_row = locality_substitution_rows.get(
            project_row.project_accession, {}
        )
        coord_counts = coordinate_counts.get(project_row.project_accession, {})
        stage_statuses = _project_stage_statuses(
            project_row=project_row,
            bundle=bundle,
            paper_row=paper_row,
            sample_master_row=sample_master_row,
            site_row=site_row,
            chronology_row=chronology_row,
            coord_counts=coord_counts,
        )
        minimum_expected = _minimum_expected_sample_count(
            project_row, sample_master_row
        )
        final_sample_count = int(sample_master_row.get("final_sample_count") or 0)
        minimum_gap_count = (
            None
            if minimum_expected is None
            else max(int(minimum_expected) - final_sample_count, 0)
        )
        implausibly_low, implausibly_low_reason = _implausibly_low_recovery(
            project_row=project_row,
            sample_master_row=sample_master_row,
            minimum_gap_count=minimum_gap_count,
        )
        rows.append(
            {
                "project_accession": project_row.project_accession,
                "species_latin_name": project_row.species_latin_name,
                "paper_doi": project_row.primary_paper_doi or "",
                "archive_status": project_row.archive_status,
                "evidence_strength": project_row.evidence_strength,
                "inventory_disposition": project_row.inventory_disposition,
                "evidence_acquisition_state": project_row.evidence_acquisition_state,
                "expected_sample_count": project_row.expected_sample_count,
                "expected_sample_count_status": project_row.expected_sample_count_status,
                "expected_sample_count_provenance": project_row.expected_sample_count_provenance,
                "expected_sample_count_artifact_path": project_row.expected_sample_count_artifact_path,
                "minimum_expected_sample_count": minimum_expected,
                "recovered_sample_count": int(
                    sample_master_row.get("recovered_sample_count") or 0
                ),
                "final_sample_count": final_sample_count,
                "unresolved_sample_count": sample_master_row.get(
                    "unresolved_sample_count"
                ),
                "minimum_gap_count": minimum_gap_count,
                "sample_identifier_status": project_row.sample_identifier_status,
                "sample_table_extraction_status": project_row.sample_table_extraction_status,
                "paper_download_status": project_row.paper_download_status,
                "supplement_download_status": project_row.supplement_download_status,
                "lacking_defensible_site_assignment_count": int(
                    site_row.get("lacking_defensible_site_assignment_count") or 0
                ),
                "named_place_inferred_count": int(
                    site_row.get("named_place_inferred_count") or 0
                ),
                "sample_group_site_count": int(
                    site_row.get("sample_group_site_count") or 0
                ),
                "missing_chronology_count": int(gap_row.get("missing_date_count") or 0),
                "chronology_conflict_count": int(
                    chronology_conflict_counts.get(project_row.project_accession, 0)
                ),
                "chronology_ambiguity_count": int(
                    chronology_ambiguity_counts.get(project_row.project_accession, 0)
                ),
                "mappable_coordinate_count": int(coord_counts.get("mappable_point", 0)),
                "coordinate_blocked_count": int(
                    coord_counts.get("refused_region_only", 0)
                )
                + int(site_row.get("region_only_count") or 0)
                + int(site_row.get("project_level_site_only_count") or 0),
                "publication_blocked_by_locality_substitution": bool(
                    substitution_row.get("publication_blocked")
                ),
                "expected_contributions": _expected_contributions(
                    project_row=project_row,
                    paper_row=paper_row,
                    site_row=site_row,
                    chronology_row=chronology_row,
                ),
                "expected_contribution_surfaces": _expected_contribution_surfaces(
                    project_row=project_row,
                    paper_row=paper_row,
                ),
                "stage_statuses": stage_statuses,
                "blocking_stages": [
                    stage
                    for stage, status in stage_statuses.items()
                    if status == "blocked"
                ],
                "next_required_stage": _next_required_stage(stage_statuses),
                "publication_readiness_status": stage_statuses["publication_readiness"],
                "overall_recovery_status": _overall_recovery_status(stage_statuses),
                "completed_stage_count": sum(
                    1 for status in stage_statuses.values() if status == "complete"
                ),
                "required_stage_count": sum(
                    1 for status in stage_statuses.values() if status != "not_required"
                ),
                "recovery_depth_score": _recovery_depth_score(stage_statuses),
                "recovery_gap_status": _recovery_gap_status(
                    project_row=project_row,
                    sample_master_row=sample_master_row,
                    minimum_gap_count=minimum_gap_count,
                ),
                "implausibly_low_recovery": implausibly_low,
                "implausibly_low_recovery_reason": implausibly_low_reason,
                "known_assets": _known_assets(project_row, bundle),
                "missing_assets": _missing_assets(
                    project_row=project_row,
                    bundle=bundle,
                    sample_master_row=sample_master_row,
                    site_row=site_row,
                    gap_row=gap_row,
                ),
                "major_deficit_reasons": _major_deficit_reasons(
                    project_row=project_row,
                    minimum_gap_count=minimum_gap_count,
                    site_row=site_row,
                    gap_row=gap_row,
                    coord_counts=coord_counts,
                    implausibly_low=implausibly_low,
                ),
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["species_latin_name"]),
            str(item["project_accession"]),
        )
    )
    return tuple(rows)


def _project_stage_statuses(
    *,
    project_row: object,
    bundle: object,
    paper_row: object | None,
    sample_master_row: dict[str, object],
    site_row: dict[str, object],
    chronology_row: dict[str, object],
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

    if not bundle.supplement_required:
        stage_statuses["supplement_capture"] = "not_required"
    elif project_row.supplement_download_status == "archived":
        stage_statuses["supplement_capture"] = "complete"
    else:
        stage_statuses["supplement_capture"] = "blocked"

    final_sample_count = int(sample_master_row.get("final_sample_count") or 0)
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

    lacking_site = int(site_row.get("lacking_defensible_site_assignment_count") or 0)
    if final_sample_count > 0 and lacking_site == 0:
        stage_statuses["site_recovery"] = "complete"
    else:
        stage_statuses["site_recovery"] = "in_progress"

    missing_chronology = int(chronology_row.get("unresolved_count") or 0)
    missing_norm = int(chronology_row.get("normalization_unresolved_count") or 0)
    if final_sample_count > 0 and missing_chronology == 0 and missing_norm == 0:
        stage_statuses["chronology_recovery"] = "complete"
    else:
        stage_statuses["chronology_recovery"] = "in_progress"

    if (
        int(coord_counts.get("mappable_point", 0)) > 0
        and int(coord_counts.get("refused_region_only", 0)) == 0
    ):
        stage_statuses["coordinate_derivation"] = "complete"
    elif stage_statuses["site_recovery"] == "complete":
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
    project_row: object,
    sample_master_row: dict[str, object],
) -> int | None:
    if project_row.expected_sample_count is not None:
        return int(project_row.expected_sample_count)
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
        and int(sample_master_row.get("recovered_sample_count") or 0) > 0
    ):
        return int(sample_master_row.get("recovered_sample_count") or 0)
    return None


def _implausibly_low_recovery(
    *,
    project_row: object,
    sample_master_row: dict[str, object],
    minimum_gap_count: int | None,
) -> tuple[bool, str]:
    if project_row.inventory_disposition == "retained_rejected_reference":
        return (False, "")
    final_sample_count = int(sample_master_row.get("final_sample_count") or 0)
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
    project_row: object,
    paper_row: object | None,
    site_row: dict[str, object],
    chronology_row: dict[str, object],
) -> list[str]:
    contributions: list[str] = []
    if project_row.inventory_disposition == "retained_rejected_reference":
        return contributions
    if project_row.sample_identifier_status != "missing_primary_paper_linkage":
        contributions.append("sample_identities")
    if paper_row is not None:
        contributions.append("taxonomic_context")
    if (
        int(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0
        or not site_row
    ):
        contributions.append("site_evidence")
        contributions.append("coordinate_candidates")
    if int(chronology_row.get("unresolved_count") or 0) > 0 or not chronology_row:
        contributions.append("sample_chronology")
    return list(dict.fromkeys(contributions))


def _expected_contribution_surfaces(
    *,
    project_row: object,
    paper_row: object | None,
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
    project_row: object,
    sample_master_row: dict[str, object],
    minimum_gap_count: int | None,
) -> str:
    if project_row.inventory_disposition == "retained_rejected_reference":
        return "out_of_scope_reference"
    final_sample_count = int(sample_master_row.get("final_sample_count") or 0)
    if (
        project_row.expected_sample_count is not None
        and int(minimum_gap_count or 0) == 0
    ):
        return "recovered_to_exact_expected_count"
    if (
        project_row.expected_sample_count is not None
        and int(minimum_gap_count or 0) > 0
    ):
        return "exact_expected_count_still_unrecovered"
    if (
        final_sample_count == 0
        and str(project_row.sample_table_extraction_status) == "published_empty"
    ):
        return "extractable_sources_but_no_governed_samples"
    if final_sample_count > 0 and minimum_gap_count is None:
        return "partial_recovery_expected_total_unknown"
    if final_sample_count > 0 and int(minimum_gap_count or 0) == 0:
        return "minimum_expected_floor_met"
    return "paper_or_capture_gap_blocks_estimate"


def _known_assets(project_row: object, bundle: object) -> list[str]:
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
    project_row: object,
    bundle: object,
    sample_master_row: dict[str, object],
    site_row: dict[str, object],
    gap_row: dict[str, object],
) -> list[str]:
    missing: list[str] = []
    if "missing_local_paper_evidence" in bundle.blockers:
        missing.append("Readable repository paper capture is still missing.")
    if "missing_local_supplementary_material" in bundle.blockers:
        missing.append("Governed repository supplementary capture is still missing.")
    if int(sample_master_row.get("final_sample_count") or 0) == 0:
        missing.append("No final governed sample rows are published yet.")
    if int(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0:
        missing.append(
            "Some recovered sample rows still lack a defensible site assignment."
        )
    if int(gap_row.get("missing_date_count") or 0) > 0:
        missing.append("Some recovered sample rows still lack sample-level chronology.")
    if project_row.sample_identifier_status == "missing_primary_paper_linkage":
        missing.append(
            "The tracked project still lacks a pinned primary paper linkage."
        )
    return missing


def _major_deficit_reasons(
    *,
    project_row: object,
    minimum_gap_count: int | None,
    site_row: dict[str, object],
    gap_row: dict[str, object],
    coord_counts: dict[str, int],
    implausibly_low: bool,
) -> list[str]:
    reasons: list[str] = []
    if implausibly_low:
        reasons.append("implausibly_low_sample_recovery")
    if int(minimum_gap_count or 0) > 0:
        reasons.append("sample_recovery_gap")
    if int(site_row.get("lacking_defensible_site_assignment_count") or 0) > 0:
        reasons.append("site_assignment_gap")
    if int(gap_row.get("missing_date_count") or 0) > 0:
        reasons.append("chronology_gap")
    if int(coord_counts.get("refused_region_only", 0)) > 0:
        reasons.append("coordinate_precision_gap")
    if project_row.sample_identifier_status == "missing_primary_paper_linkage":
        reasons.append("missing_primary_paper_linkage")
    return reasons


def _paper_yield_recovery_posture(items: list[dict[str, object]]) -> str:
    if any(bool(item["implausibly_low_recovery"]) for item in items):
        return "implausibly_low_project_recovery_present"
    if any(item["expected_sample_count"] is None for item in items):
        return "expected_total_still_partially_unbounded"
    return "exact_expected_counts_curated"


def _missing_source_queue_category(row: dict[str, object]) -> str:
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


def _missing_source_queue_reason(category: str, row: dict[str, object]) -> str:
    if category == "missing_primary_paper_linkage":
        return "The project is tracked, but the repository still lacks a pinned primary paper anchor for downstream extraction."
    if category == "missing_repository_paper_capture":
        return "The project has a paper anchor, but the repository still lacks a governed readable article surface."
    if category == "missing_repository_supplement_capture":
        return "The tracked paper points to supplementary evidence that still is not archived under the governed source library."
    if category == "sample_recovery_still_thin":
        return str(row["implausibly_low_recovery_reason"])
    return ""


def _sample_evidence_depth_counts(output_root: Path) -> dict[str, int]:
    output_root = Path(output_root)
    counts = {
        "sample_identity_only": 0,
        "sample_with_site": 0,
        "sample_with_site_and_chronology": 0,
        "sample_with_site_chronology_and_coordinates": 0,
    }
    species_root = output_root / "adna" / "species"
    if not species_root.is_dir():
        return counts
    for root in species_root.iterdir():
        sample_path = root / "normalized" / "sample_records.json"
        if not sample_path.is_file():
            continue
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        for row in payload.get("samples", []):
            has_site = bool(
                str(row.get("locality", "") or row.get("site_label", "")).strip()
            ) or bool(row.get("locality_identity"))
            has_chronology = str(
                row.get("chronology_normalization_status", "")
            ).strip() in {
                "normalized_interval",
                "normalized_point",
            }
            coords = row.get("coordinates", {})
            has_coordinates = bool(
                str(coords.get("latitude_text", "")).strip()
                and str(coords.get("longitude_text", "")).strip()
            )
            if not has_site:
                counts["sample_identity_only"] += 1
            elif has_site and not has_chronology:
                counts["sample_with_site"] += 1
            elif has_site and has_chronology and not has_coordinates:
                counts["sample_with_site_and_chronology"] += 1
            else:
                counts["sample_with_site_chronology_and_coordinates"] += 1
    return counts


def _coordinate_counts_by_project(output_root: Path) -> dict[str, dict[str, int]]:
    output_root = Path(output_root)
    species_root = output_root / "adna" / "species"
    counts: dict[str, dict[str, int]] = {}
    if not species_root.is_dir():
        return counts
    for root in species_root.iterdir():
        payload_path = root / "normalized" / "coordinate_provenance.json"
        if not payload_path.is_file():
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        for row in payload.get("coordinate_provenance", []):
            project_accession = str(row.get("project_accession", "")).strip()
            if not project_accession:
                continue
            project_counts = counts.setdefault(project_accession, {})
            posture = str(row.get("mapping_posture", "")).strip()
            project_counts[posture] = project_counts.get(posture, 0) + 1
    return counts


def _count_rows(
    rows: list[dict[str, object]] | tuple[dict[str, object], ...], *, key: str
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "")).strip()
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    return counts


def _project_species(project_accession: str) -> str:
    for project in build_archive_project_catalog():
        if project.project_accession == project_accession:
            return project.species_latin_name
    return ""


def _nonempty_paths(paths: list[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for path in paths:
        candidate = str(path).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        rows.append(candidate)
    return rows


def _cache_key(output_root: Path) -> str:
    return str(Path(output_root).resolve())
