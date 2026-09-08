from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from typing import Any, cast


def build_sead_recovery_requirements(
    *,
    access_model_packet: dict[str, object],
    evidence_legibility_review: dict[str, object],
    generated_on: date | None = None,
) -> dict[str, object]:
    """Turn current SEAD legibility gaps into governed evidence requirements."""
    inventory = _mapping_value(evidence_legibility_review, "inventory_summary")
    temporal_counts = _mapping_value(
        evidence_legibility_review, "temporal_strength_counts"
    )
    access_counts = _mapping_value(access_model_packet, "access_visibility_counts")
    unresolved_count = _integer_value(
        inventory.get(
            "unresolved_site_count",
            temporal_counts.get("inventory_only_or_unresolved", 0),
        )
    )
    site_page_only_count = _integer_value(access_counts.get("site_page_only", 0))
    review_row_count = _integer_value(evidence_legibility_review.get("row_count", 0))
    evidence_rows = _object_rows(evidence_legibility_review, "rows")
    access_rows = _object_rows(access_model_packet, "rows")
    unresolved_site_uuids = _affected_site_uuids(
        row
        for row in evidence_rows
        if row.get("temporal_strength")
        in {"inventory_only_or_unresolved", "period_label_only"}
    )
    site_page_only_uuids = _affected_site_uuids(
        row for row in access_rows if row.get("access_visibility") == "site_page_only"
    )
    all_site_uuids = _affected_site_uuids(evidence_rows)
    _require_matching_gap_count(
        "unresolved_chronology_boundary", unresolved_count, unresolved_site_uuids
    )
    _require_matching_gap_count(
        "unreferenced_site_boundary", site_page_only_count, site_page_only_uuids
    )
    _require_matching_gap_count(
        "context_layer_republication", review_row_count, all_site_uuids
    )
    _require_matching_gap_count(
        "published_scope_refresh", review_row_count, all_site_uuids
    )
    rows = [
        {
            "requirement_key": "unresolved_chronology_boundary",
            "evidence_gap_count": unresolved_count,
            "affected_site_uuids": unresolved_site_uuids,
            "required_evidence": "Retain sites without captured upstream chronology as an explicit spatial-only population; add dates only when a linked SEAD chronology record supplies defensible bounds.",
            "satisfaction_signal": "Every captured chronology row has normalized BP bounds, the temporal-evidence layer is fully time-filterable, and upstream-undated sites remain visibly unresolved.",
        },
        {
            "requirement_key": "unreferenced_site_boundary",
            "evidence_gap_count": site_page_only_count,
            "affected_site_uuids": site_page_only_uuids,
            "required_evidence": "Retain site-page-only access where captured bibliography rows expose no directly followable DOI or URL; add links only from identified SEAD bibliography values.",
            "satisfaction_signal": "All captured bibliography relations preserve their source relation and sites without directly followable upstream links remain explicit instead of receiving inferred URLs.",
        },
        {
            "requirement_key": "context_layer_republication",
            "evidence_gap_count": review_row_count,
            "affected_site_uuids": all_site_uuids,
            "required_evidence": "Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature.",
            "satisfaction_signal": "Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces.",
        },
        {
            "requirement_key": "published_scope_refresh",
            "evidence_gap_count": review_row_count,
            "affected_site_uuids": all_site_uuids,
            "required_evidence": "Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob.",
            "satisfaction_signal": "Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels.",
        },
    ]
    return {
        "schema_version": "sead-recovery-requirements.v1",
        "generated_on": str(generated_on or datetime.now(UTC).date()),
        "row_count": len(rows),
        "rows": rows,
    }


def render_sead_recovery_requirements_markdown(payload: dict[str, object]) -> str:
    review_rows = cast(list[dict[str, Any]], payload["rows"])
    lines = [
        "# SEAD recovery requirements",
        "",
        "These requirements identify the evidence needed to make SEAD a scientifically legible and operationally trustworthy context program.",
        "",
        "| Requirement | Evidence gap count | Required evidence | Satisfaction signal |",
        "| --- | ---: | --- | --- |",
    ]
    for row in review_rows:
        lines.append(
            f"| {row['requirement_key']} | {row['evidence_gap_count']} | "
            f"{row['required_evidence']} | {row['satisfaction_signal']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _mapping_value(payload: dict[str, object], key: str) -> dict[str, object]:
    return dict(cast(Any, payload.get(key, {})))


def _integer_value(value: object) -> int:
    return int(cast(Any, value))


def _object_rows(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"SEAD review {key} must be object rows")
    return cast(list[dict[str, object]], value)


def _affected_site_uuids(rows: Iterable[Mapping[str, object]]) -> list[str]:
    site_uuids: list[str] = []
    for row in rows:
        site_uuid = row.get("site_uuid")
        if not isinstance(site_uuid, str) or not site_uuid.strip():
            raise ValueError("SEAD recovery requirement row site_uuid is missing")
        site_uuids.append(site_uuid.strip())
    if len(site_uuids) != len(set(site_uuids)):
        raise ValueError("SEAD recovery requirement site_uuid is duplicated")
    return sorted(site_uuids)


def _require_matching_gap_count(
    requirement_key: str, gap_count: int, site_uuids: list[str]
) -> None:
    if gap_count != len(site_uuids):
        raise ValueError(
            f"SEAD {requirement_key} gap count does not match affected sites"
        )
