from __future__ import annotations

from datetime import date
from typing import Any, cast


def build_sead_recovery_requirements(
    *,
    access_model_packet: dict[str, object],
    evidence_legibility_review: dict[str, object],
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
    rows = [
        {
            "requirement_key": "unresolved_chronology_boundary",
            "evidence_gap_count": unresolved_count,
            "required_evidence": "Retain sites without captured upstream chronology as an explicit spatial-only population; add dates only when a linked SEAD chronology record supplies defensible bounds.",
            "satisfaction_signal": "Every captured chronology row has normalized BP bounds, the temporal-evidence layer is fully time-filterable, and upstream-undated sites remain visibly unresolved.",
        },
        {
            "requirement_key": "unreferenced_site_boundary",
            "evidence_gap_count": site_page_only_count,
            "required_evidence": "Retain site-page-only access where captured bibliography rows expose no directly followable DOI or URL; add links only from identified SEAD bibliography values.",
            "satisfaction_signal": "All captured bibliography relations preserve their source relation and sites without directly followable upstream links remain explicit instead of receiving inferred URLs.",
        },
        {
            "requirement_key": "context_layer_republication",
            "evidence_gap_count": review_row_count,
            "required_evidence": "Republish the normalized SEAD context layer with explicit temporal semantics, access posture, and context-only caveats on every feature.",
            "satisfaction_signal": "Normalized and published SEAD GeoJSON no longer trigger missing-temporal-semantics findings in report review surfaces.",
        },
        {
            "requirement_key": "published_scope_refresh",
            "evidence_gap_count": review_row_count,
            "required_evidence": "Refresh published world, Europe-plus, and Nordic report bundles so SEAD appears as a bounded archaeology context layer rather than a generic environmental blob.",
            "satisfaction_signal": "Published map and review bundles expose SEAD with stable caveats, access wording, and bounded contextual role labels.",
        },
    ]
    return {
        "schema_version": "sead-recovery-requirements.v1",
        "generated_on": str(date.today()),
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
