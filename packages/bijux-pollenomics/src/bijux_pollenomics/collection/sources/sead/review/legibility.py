from __future__ import annotations

from datetime import date
from typing import Any, cast

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.sead.acquisition.access import (
    build_sead_site_access_model,
)

from .inventory import inventory_summary


def build_sead_evidence_legibility_review(
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, object]:
    """Classify SEAD rows by temporal strength, duration weakness, access, and risk."""
    record_lookup = {record.record_id: record for record in records}
    review_rows: list[dict[str, object]] = []
    counts: dict[str, dict[str, int]] = {
        "temporal_strength": {},
        "duration_posture": {},
        "access_visibility": {},
        "normalization_risk": {},
    }
    for row in rows:
        site_id = str(row.get("site_id", "")).strip()
        record = record_lookup.get(site_id)
        semantics = (record.temporal_semantics or {}) if record is not None else {}
        posture = (
            str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        )
        access_model = build_sead_site_access_model(row)
        temporal_strength = temporal_strength_for(posture)
        duration_posture = duration_posture_for(row, semantics)
        access_visibility = str(access_model.get("access_visibility", "")).strip()
        normalization_risk = normalization_risk_for(
            row=row,
            posture=posture,
            access_visibility=access_visibility,
        )
        for key, value in (
            ("temporal_strength", temporal_strength),
            ("duration_posture", duration_posture),
            ("access_visibility", access_visibility),
            ("normalization_risk", normalization_risk),
        ):
            counts[key][value] = counts[key].get(value, 0) + 1
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("site_name", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "temporal_strength": temporal_strength,
                "duration_posture": duration_posture,
                "access_visibility": access_visibility,
                "normalization_risk": normalization_risk,
                "publication_posture": "context_layer_with_explicit_caveat",
                "site_page_url": str(access_model.get("site_page_url", "")).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "review_note": review_note_for(
                    temporal_strength=temporal_strength,
                    duration_posture=duration_posture,
                    access_visibility=access_visibility,
                    normalization_risk=normalization_risk,
                ),
            }
        )
    review_rows.sort(
        key=lambda row: (
            str(row["normalization_risk"]),
            str(row["temporal_strength"]),
            str(row["site_name"]).casefold(),
        )
    )
    return {
        "schema_version": "sead-evidence-legibility-review.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "inventory_summary": inventory_summary(rows),
        "temporal_strength_counts": counts["temporal_strength"],
        "duration_posture_counts": counts["duration_posture"],
        "access_visibility_counts": counts["access_visibility"],
        "normalization_risk_counts": counts["normalization_risk"],
        "rows": review_rows,
    }


def temporal_strength_for(posture: str) -> str:
    if posture == "numeric_interval":
        return "numeric_site_span"
    if posture in {"numeric_interval_with_caveat", "mixed_interval_and_context"}:
        return "numeric_span_with_contextual_caveat"
    if posture == "contextual_label_only":
        return "period_label_only"
    return "inventory_only_or_unresolved"


def duration_posture_for(row: dict[str, object], semantics: dict[str, object]) -> str:
    time_start_bp = semantics.get("time_start_bp")
    time_end_bp = semantics.get("time_end_bp")
    if isinstance(time_start_bp, int) and isinstance(time_end_bp, int):
        if time_start_bp == time_end_bp:
            return "point_like_or_single_year"
        return "duration_span_visible"
    contextual_start = row.get("contextual_time_start_bp")
    contextual_end = row.get("contextual_time_end_bp")
    if isinstance(contextual_start, int) and isinstance(contextual_end, int):
        return "broad_context_duration"
    return "duration_not_available"


def normalization_risk_for(
    *, row: dict[str, object], posture: str, access_visibility: str
) -> str:
    if posture == "unresolved" and not isinstance(row.get("dating_range_rows"), list):
        return "high_thin_site_inventory"
    if posture == "contextual_label_only":
        return "medium_period_label_interpretation"
    if posture in {"numeric_interval_with_caveat", "mixed_interval_and_context"}:
        return "medium_contextual_numeric_mix"
    if access_visibility == "site_page_only":
        return "medium_access_constrained"
    return "low_contextually_bounded"


def review_note_for(
    *,
    temporal_strength: str,
    duration_posture: str,
    access_visibility: str,
    normalization_risk: str,
) -> str:
    if normalization_risk == "high_thin_site_inventory":
        return "Current checked-in SEAD capture is too thin to support stronger temporal interpretation."
    if access_visibility == "site_page_only":
        return "Readers may need to inspect the upstream SEAD site page because the repository does not currently expose stronger reference links."
    if temporal_strength == "period_label_only":
        return "This row should stay a contextual period label, not a direct date."
    if duration_posture == "duration_span_visible":
        return "This row carries a visible site span, but the span still belongs to archaeology context rather than a sample-owned event."
    return "This row is publishable only as contextual archaeology support with its stated caveats."


def render_sead_evidence_legibility_review_markdown(payload: dict[str, object]) -> str:
    review_rows = cast(list[dict[str, Any]], payload["rows"])
    lines = [
        "# SEAD evidence legibility review",
        "",
        "This review classifies SEAD rows by temporal strength, duration posture, access visibility, and normalization risk so the contextual layer can be published honestly.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
        "",
        "## Risk Counts",
        "",
    ]
    counts = payload.get("normalization_risk_counts", {})
    if isinstance(counts, dict):
        for key in sorted(counts):
            lines.append(f"- {key.replace('_', ' ')}: `{counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Temporal strength | Duration posture | Access visibility | Normalization risk | Review note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in review_rows:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['temporal_strength']} | "
            f"{row['duration_posture']} | {row['access_visibility']} | "
            f"{row['normalization_risk']} | {row['review_note']} |"
        )
    lines.append("")
    return "\n".join(lines)
