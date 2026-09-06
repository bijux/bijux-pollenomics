from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessReport,
)


def _is_registry_backed_report(report: LakeEvidenceRichnessReport) -> bool:
    diagnostics = _methodology_mapping(report, "identity_diagnostics")
    if diagnostics is None:
        return False
    methods = diagnostics.get("coordinate_resolution_methods")
    if not isinstance(methods, list):
        return False
    return "svar_polygon_representative_point" in methods


def _lake_ranking_summary_paragraph(registry_backed: bool) -> str:
    if registry_backed:
        return (
            "Coordinates resolve to representative points drawn from official "
            "SMHI SVAR lake polygons, so map checks land on the lake itself "
            "rather than on a synthetic centroid or on one supporting pollen record."
        )
    return (
        "Coordinates resolve to one representative source-backed point per lake "
        "candidate so map checks land on a published source point rather than a "
        "synthetic centroid."
    )


def _render_identity_methodology(report: LakeEvidenceRichnessReport) -> str:
    diagnostics = _methodology_mapping(report, "identity_diagnostics") or {}
    if _is_registry_backed_report(report):
        return (
            "duplicate Sweden lake names stay explicit, and registry names that do not "
            "come from the official register field remain flagged for review"
        )
    name_match_distance = diagnostics.get("name_match_distance_km", "not recorded")
    coordinate_spread = diagnostics.get("coordinate_spread_flag_km", "not recorded")
    return (
        f"cleaned-name matching within {name_match_distance} km, "
        f"coordinate-spread flag at {coordinate_spread} km, "
        "and explicit source-position notes when raw source notes say the lake "
        "position is uncertain"
    )


def _render_coordinate_targeting(report: LakeEvidenceRichnessReport) -> str:
    if _is_registry_backed_report(report):
        return (
            "each lake keeps one representative point derived from the official "
            "lake polygon, with registry identifiers and name status carried into "
            "the CSV, JSON, and map popups"
        )
    return (
        "each lake keeps one representative source-backed point chosen from its "
        "supporting pollen records using the method recorded in the registry CSV "
        "and JSON payload"
    )


def _render_human_weighting(report: LakeEvidenceRichnessReport) -> str:
    score_components = _methodology_mapping(report, "score_components") or {}
    if (
        "human_adna_signal" in score_components
        and "direct_pollen_signal" in score_components
        and "nearby_pollen_signal" in score_components
    ):
        return (
            f"human aDNA contributes {score_components['human_adna_signal']:.2f} of each "
            f"band score, direct pollen contributes {score_components['direct_pollen_signal']:.2f}, "
            f"nearby pollen contributes {score_components['nearby_pollen_signal']:.2f}, "
            f"and archaeology contributes {score_components['archaeology_signal']:.2f}"
        )
    return "human aDNA is balanced with pollen and archaeology rather than acting as the decisive term"


def _render_ranking_decision_rule(report: LakeEvidenceRichnessReport) -> str:
    rule = report.methodology.get("ranking_decision_rule")
    if isinstance(rule, str) and rule:
        return rule
    return (
        "aggregate and band ranks use one blended score without an explicit "
        "decision chain"
    )


def _render_temporal_alignment_rule(report: LakeEvidenceRichnessReport) -> str:
    rule = report.methodology.get("temporal_alignment_rule")
    if isinstance(rule, str) and rule:
        return rule
    return (
        "time-aware chronology remains visible where available, but the ranking does "
        "not currently promote chronology overlap as a separate rule"
    )


def _render_temporal_navigation(report: LakeEvidenceRichnessReport) -> str:
    payload = report.methodology.get("temporal_navigation")
    if not isinstance(payload, dict):
        return "no governed candidate-level navigation summary is available"
    candidates = _methodology_count(payload, "candidate_count")
    contextual = _methodology_count(payload, "candidate_with_numeric_context_count")
    direct = _methodology_count(payload, "candidate_with_direct_numeric_pollen_count")
    summaries = _methodology_count(payload, "context_summary_count")
    radius = _methodology_count(payload, "context_radius_km")
    return (
        f"{contextual}/{candidates} ranked lakes have numeric navigation context; "
        f"{direct}/{candidates} have direct numeric pollen chronology. The map "
        f"publishes {summaries} source-family/window summaries within {radius} km, "
        "with nearby context kept separate from lake-owned chronology"
    )


def _render_optional_methodology_note(
    report: LakeEvidenceRichnessReport,
    key: str,
) -> str:
    value = report.methodology.get(key)
    if isinstance(value, str) and value:
        return value
    if key == "pollen_note":
        return (
            "Direct pollen signal reflects the quality of the lake-linked pollen "
            "records rather than a synthetic lake average."
        )
    return ""


def _render_source_temporal_coverage(report: LakeEvidenceRichnessReport) -> str:
    payload = report.methodology.get("source_temporal_coverage")
    if not isinstance(payload, dict):
        return (
            "checked-in context layers do not publish one explicit source-by-source "
            "temporal coverage summary yet"
        )
    labels = {
        "neotoma_pollen": "Neotoma",
        "landclim_pollen": "LandClim",
        "sead_archaeology": "SEAD",
    }
    rendered = []
    for key in ("neotoma_pollen", "landclim_pollen", "sead_archaeology"):
        item = payload.get(key)
        if not isinstance(item, dict):
            continue
        total = _methodology_count(item, "record_count")
        numeric = _methodology_count(item, "numeric_interval_record_count")
        posture = _render_source_temporal_posture(key=key, item=item)
        rendered.append(
            f"{labels[key]} {numeric}/{total} numeric-interval records ({posture})"
        )
    return ", ".join(rendered) if rendered else "no source temporal coverage summary"


def _render_source_temporal_posture(*, key: str, item: Mapping[str, object]) -> str:
    total = _methodology_count(item, "record_count")
    numeric = _methodology_count(item, "numeric_interval_record_count")
    capture_posture = str(item.get("capture_posture", "")).strip()
    temporal_support_note = str(item.get("temporal_support_note", "")).strip()
    distance_scoring_note = str(item.get("distance_scoring_note", "")).strip()
    if total == 0:
        return "no checked-in records"
    if key == "neotoma_pollen":
        if (
            capture_posture
            == "calendar_comparable_system_context_without_compact_chronology"
        ):
            base = (
                "source BP-system context retained; compact numeric intervals withheld"
            )
            if distance_scoring_note:
                return f"{base}; {distance_scoring_note[0].lower()}{distance_scoring_note[1:]}"
            return base
        if numeric == total:
            return "full numeric chronology coverage"
        if numeric > 0:
            return "partial chronology coverage"
        return "spatial inventory only"
    if key == "landclim_pollen" and temporal_support_note:
        return temporal_support_note
    if key == "sead_archaeology":
        if capture_posture == "site_inventory_only":
            base = "site inventory only in checked-in raw capture"
            if distance_scoring_note:
                return f"{base}; {distance_scoring_note[0].lower()}{distance_scoring_note[1:]}"
            return base
        if numeric == 0:
            return temporal_support_note or "spatial inventory only"
        if numeric == total:
            return "full numeric chronology coverage"
        return "partial chronology coverage"
    if numeric == 0:
        return temporal_support_note or "spatial inventory only"
    if numeric == total:
        return "full numeric chronology coverage"
    return "partial chronology coverage"


def _methodology_mapping(
    report: LakeEvidenceRichnessReport,
    key: str,
) -> Mapping[str, object] | None:
    value = report.methodology.get(key)
    return value if isinstance(value, Mapping) else None


def _methodology_count(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key, 0)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value
