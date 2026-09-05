"""Animal foundation release responsibilities."""

from __future__ import annotations
from typing import Any, cast
from pathlib import Path
from ....adna.governance.audit_catalogs import (
    build_overbroad_site_ledger,
    build_unresolved_site_ledger,
)
from ....adna.projects.evidence.localities import (
    build_project_locality_substitution_ledger,
)
from ....adna.projects.registry.sample_truth import build_project_locality_count_drift
from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .repository import (
    _load_all_project_sample_chronology_rows,
    _load_all_project_sample_site_rows,
    _load_all_sample_rows,
    _load_country_payloads,
)
from .validation import _check_row


def build_animal_publication_release_gate(
    *,
    data_root: Path,
    report_root: Path,
    docs_root: Path,
    point_payload: dict[str, Any],
    review_payload: dict[str, Any],
    sample_database_review_payload: dict[str, Any],
    intake_recovery_payload: dict[str, Any],
    temporal_comparison_payload: dict[str, Any],
) -> dict[str, Any]:
    """Fail publication when animal outputs overclaim or lose required traceability."""
    docs_paths = sorted(path for path in docs_root.rglob("*.md") if path.is_file())
    docs_text = "\n".join(
        path.read_text(encoding="utf-8") for path in docs_paths
    ).lower()
    all_species_claim = (
        "all-species animal map readiness" in docs_text
        or "all species animal map readiness" in docs_text
    )
    reference_grade_claim = "reference-grade" in docs_text
    country_payloads = _load_country_payloads(report_root)
    try:
        atlas_rows: list[dict[str, Any]] = [
            cast(dict[str, Any], row.as_dict())
            for row in build_tracked_animal_atlas_evidence_rows(data_root)
        ]
    except FileNotFoundError:
        atlas_rows = []
    unresolved_rows = build_unresolved_site_ledger(data_root)
    overbroad_rows = build_overbroad_site_ledger(data_root)
    project_locality_drift_rows = build_project_locality_count_drift(data_root)
    locality_substitution_rows = build_project_locality_substitution_ledger(data_root)
    sample_site_rows = _load_all_project_sample_site_rows(data_root)
    chronology_rows = _load_all_project_sample_chronology_rows(data_root)
    substitution_blocked_projects = {
        str(row.get("project_accession", "")).strip()
        for row in locality_substitution_rows
        if bool(row.get("publication_blocked"))
    }
    blocked_sample_site_rows = {
        str(row.get("repo_stable_sample_id", "")).strip(): row
        for row in sample_site_rows
        if str(row.get("locality_resolution_status", ""))
        in {
            "project_level_site_only",
            "region_only",
            "unresolved",
        }
        and str(row.get("repo_stable_sample_id", "")).strip()
    }
    blocked_exact_site_rows = [
        str(row.get("identity", {}).get("stable_token", "")).strip()
        for row in _load_all_sample_rows(data_root)
        if str(row.get("identity", {}).get("stable_token", "")).strip()
        in blocked_sample_site_rows
        and ":sample-site:"
        in str(row.get("locality_identity", {}).get("stable_token", ""))
    ]
    blocked_atlas_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            for sample_row in point.get("sample_rows", [])
            if str(sample_row.get("identity", {}).get("stable_token", "")).strip()
            in blocked_sample_site_rows
        }
    )
    chronology_blocked_master_ids = {
        str(row.get("repo_stable_sample_id", "")).strip(): row
        for row in chronology_rows
        if _chronology_row_blocks_publication(row)
    }
    sample_master_ids = {
        str(row.get("identity", {}).get("stable_token", "")).strip(): str(
            row.get("master_id", "")
        ).strip()
        for row in _load_all_sample_rows(data_root)
        if str(row.get("identity", {}).get("stable_token", "")).strip()
    }
    blocked_country_chronology_rows = sorted(
        {
            str(sample_row.get("sample_record_id", "")).strip()
            for payload in country_payloads
            for sample_row in payload.get("sample_rows", [])
            if sample_master_ids.get(
                str(sample_row.get("sample_record_id", "")).strip(), ""
            )
            in chronology_blocked_master_ids
        }
    )
    blocked_atlas_chronology_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            for sample_row in point.get("sample_rows", [])
            if sample_master_ids.get(
                str(sample_row.get("identity", {}).get("stable_token", "")).strip(),
                "",
            )
            in chronology_blocked_master_ids
        }
    )
    substitution_blocked_country_rows = sorted(
        {
            str(sample_row.get("sample_record_id", "")).strip()
            for payload in country_payloads
            for sample_row in payload.get("sample_rows", [])
            if str(sample_row.get("project_accession", "")).strip()
            in substitution_blocked_projects
        }
    )
    substitution_blocked_atlas_rows = sorted(
        {
            str(point.get("feature_id", "")).strip()
            for point in point_payload["rows"]
            if str(point.get("primary_project_accession", "")).strip()
            in substitution_blocked_projects
        }
    )
    imprecise_country_chronology_rows = sorted(
        {
            str(locality.get("feature_id", "")).strip()
            for payload in country_payloads
            for locality in payload.get("localities", [])
            if _public_chronology_window_exposed(locality)
        }
    )
    imprecise_atlas_chronology_rows = sorted(
        {
            str(row.get("feature_id", "")).strip()
            for row in atlas_rows
            if _public_chronology_window_exposed(row.get("chronology", {}))
        }
    )
    point_row_count = int(
        point_payload.get("row_count", len(point_payload.get("rows", [])))
    )
    reference_grade_support_requirements = {
        "sample_database_artifacts_present": bool(
            sample_database_review_payload["sample_database_claim_supported"]
        ),
        "sample_evidence_reviews_present": bool(point_row_count),
        "map_outputs_present": bool(
            sample_database_review_payload["nordic_view_supported_now"]
        ),
    }
    reference_grade_support_ready = bool(
        review_payload["reference_grade_claim_allowed"]
        and all(reference_grade_support_requirements.values())
    )
    temporal_feature_findings = list(
        temporal_comparison_payload.get("published_feature_guard_findings", [])
    )
    checks = [
        _check_row(
            "published_points_keep_required_traceability",
            all(
                bool(row.get("sample_rows"))
                and bool(row.get("site_evidence"))
                and bool(row.get("coordinate_provenance"))
                and bool(str(row.get("paper_url", "")).strip())
                for row in point_payload["rows"]
            ),
            "Every published animal point keeps declared identity, site, coordinate, and citation traceability; provisional project context remains explicitly non-final sample evidence.",
            [
                str(row.get("feature_id", ""))
                for row in point_payload["rows"]
                if not (
                    bool(row.get("sample_rows"))
                    and bool(row.get("site_evidence"))
                    and bool(row.get("coordinate_provenance"))
                    and bool(str(row.get("paper_url", "")).strip())
                )
            ],
        ),
        _check_row(
            "project_recovery_guard_passes",
            bool(intake_recovery_payload["release_guard"]["passing"]),
            "The intake recovery guard confirms that no tracked project remains implausibly under-recovered; separate scientific-review and completeness blockers remain independently enforced.",
            []
            if bool(intake_recovery_payload["release_guard"]["passing"])
            else ["project_recovery_release_guard_still_failing"],
        ),
        _check_row(
            "project_locality_outputs_do_not_flatten_sample_site_disagreement",
            not project_locality_drift_rows,
            "Animal publication does not flatten multi-site sample evidence into one project-level locality claim.",
            [
                str(row.get("project_accession", ""))
                for row in project_locality_drift_rows
            ],
        ),
        _check_row(
            "blocked_sample_site_rows_do_not_publish_as_exact_sites_or_atlas_points",
            not (blocked_exact_site_rows or blocked_atlas_rows),
            "Sample rows without defensible sample-owned site assignment do not leak into exact site rows or atlas points.",
            blocked_exact_site_rows + blocked_atlas_rows,
        ),
        _check_row(
            "unresolved_sample_chronology_does_not_publish_in_country_or_atlas_outputs",
            not (blocked_country_chronology_rows or blocked_atlas_chronology_rows),
            "Published country and atlas outputs do not carry unresolved or conflicting sample chronology rows.",
            blocked_country_chronology_rows + blocked_atlas_chronology_rows,
        ),
        _check_row(
            "project_level_locality_substitution_projects_do_not_publish_country_or_atlas_rows",
            not (substitution_blocked_country_rows or substitution_blocked_atlas_rows),
            "Projects whose locality evidence still collapses all samples into one blocked context do not leak into country or atlas publication.",
            substitution_blocked_country_rows + substitution_blocked_atlas_rows,
        ),
        _check_row(
            "broad_or_contextual_chronology_does_not_publish_numeric_windows",
            not (imprecise_country_chronology_rows or imprecise_atlas_chronology_rows),
            "Public country and atlas outputs do not expose numeric chronology windows when the underlying chronology posture is broad, contextual, or approximate.",
            imprecise_country_chronology_rows + imprecise_atlas_chronology_rows,
        ),
        _check_row(
            "temporal_semantics_keep_contextual_rows_from_looking_numeric",
            not temporal_feature_findings,
            "Published animal and context GeoJSON layers must carry temporal semantics and must not expose contextual-only rows as numeric comparisons.",
            temporal_feature_findings,
        ),
        _check_row(
            "docs_do_not_overclaim_all_species_map_readiness",
            not (all_species_claim and (unresolved_rows or overbroad_rows)),
            "Public docs do not claim all-species animal map readiness while blocking ledgers remain.",
            ["docs_claim_all_species_map_readiness"] if all_species_claim else [],
        ),
        _check_row(
            "docs_do_not_claim_reference_grade_without_support",
            not (reference_grade_claim and not reference_grade_support_ready),
            "Public docs do not claim the strongest posture before the sample database, evidence reviews, and map outputs all support it.",
            ["docs_claim_reference_grade"] if reference_grade_claim else [],
        ),
    ]
    overall_ok = all(bool(check["passed"]) for check in checks)
    return {
        "schema_version": "animal-publication-release-gate.v1",
        "overall_ok": overall_ok,
        "checks": checks,
        "reference_grade_claim_allowed": review_payload[
            "reference_grade_claim_allowed"
        ],
        "reference_grade_support_ready": reference_grade_support_ready,
        "reference_grade_support_requirements": reference_grade_support_requirements,
    }


def _chronology_row_blocks_publication(row: dict[str, Any]) -> bool:
    status = str(row.get("chronology_normalization_status", "")).strip()
    precision_posture = str(row.get("chronology_precision_posture", "")).strip()
    return status == "unresolved" or precision_posture == "unresolved"


def _public_chronology_window_exposed(payload: dict[str, Any]) -> bool:
    precision_posture = str(payload.get("chronology_precision_posture", "")).strip()
    if not precision_posture and isinstance(payload.get("precision_posture"), str):
        precision_posture = str(payload.get("precision_posture", "")).strip()
    if precision_posture in {"sample_precise_point", "sample_precise_interval", ""}:
        return False
    return any(
        payload.get(field) is not None
        for field in ("time_start_bp", "time_end_bp", "time_mean_bp")
    )
