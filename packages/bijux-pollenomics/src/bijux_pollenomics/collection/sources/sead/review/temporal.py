from __future__ import annotations

from datetime import date
from typing import Any, cast

from bijux_pollenomics.collection.contracts.models import ContextPointRecord

from .inventory import inventory_summary, sead_row_capture_posture, site_uuid_for


def build_sead_temporal_review(
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, object]:
    """Build one governed SEAD review of temporal semantics and uncertainty."""
    record_lookup = {record.record_id: record for record in records}
    review_rows: list[dict[str, object]] = []
    posture_counts: dict[str, int] = {}
    for row in rows:
        site_id = str(row.get("site_id", "")).strip()
        record = record_lookup.get(site_id)
        semantics = (record.temporal_semantics or {}) if record is not None else {}
        posture = (
            str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        )
        posture_counts[posture] = posture_counts.get(posture, 0) + 1
        review_rows.append(
            {
                "site_id": site_id,
                "site_uuid": site_uuid_for(row),
                "site_name": str(row.get("site_name", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "comparability_posture": posture,
                "raw_capture_posture": sead_row_capture_posture(row),
                "temporal_window_label": str(
                    semantics.get("temporal_window_label", "")
                ).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "normalized_period_labels": _list_value(semantics, "normalized_labels"),
                "original_period_labels": _list_value(semantics, "original_labels"),
                "uncertainty_notes": _list_value(semantics, "uncertainty_notes"),
                "dating_range_count": _row_count(row, "dating_range_rows"),
                "relative_period_count": _row_count(row, "relative_period_rows"),
                "analysis_entity_age_count": _row_count(
                    row, "analysis_entity_age_rows"
                ),
                "geochronology_count": _row_count(row, "geochronology_rows"),
                "dendro_date_count": _row_count(row, "dendro_date_rows"),
                "bibliography_count": _row_count(row, "bibliography_rows"),
                "comparison_note": str(semantics.get("comparison_note", "")).strip(),
            }
        )
    review_rows.sort(
        key=lambda row: (
            str(row["comparability_posture"]),
            str(row["site_name"]).casefold(),
            str(row["site_id"]),
        )
    )
    return {
        "schema_version": "sead-temporal-review.v2",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "comparability_posture_counts": posture_counts,
        "inventory_summary": inventory_summary(rows),
        "rows": review_rows,
    }


def _list_value(values: dict[str, object], key: str) -> list[Any]:
    value = values.get(key)
    return list(value) if isinstance(value, list) else []


def _row_count(row: dict[str, object], key: str) -> int:
    value = row.get(key)
    return len(value) if isinstance(value, list) else 0


def render_sead_temporal_review_markdown(payload: dict[str, object]) -> str:
    rows = cast(list[dict[str, Any]], payload["rows"])
    inventory = payload.get("inventory_summary", {})
    if not isinstance(inventory, dict):
        inventory = {}
    lines = [
        "# SEAD temporal review",
        "",
        "This review keeps SEAD honest about site-level time semantics. It distinguishes numeric site spans, mixed site spans plus cultural labels, and unresolved rows that should not be read like sample-owned dates. Record-level chronology is published separately so one broad site envelope does not replace its linked intervals.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
    ]
    posture_counts = payload.get("comparability_posture_counts", {})
    if isinstance(posture_counts, dict):
        for key in sorted(posture_counts):
            lines.append(f"- {key.replace('_', ' ')}: `{posture_counts[key]}`")
    if inventory:
        lines.extend(_inventory_markdown_lines(inventory))
    lines.extend(
        [
            "",
            "| Site | Site UUID | Country | Comparability posture | Raw capture posture | Time summary | Normalized period labels | Uncertainty notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | `{row['site_uuid']}` | "
            f"{row['country']} | "
            f"{row['comparability_posture']} | {row['raw_capture_posture']} | "
            f"{row['summary_label']} | "
            f"{', '.join(row['normalized_period_labels']) or 'None'} | "
            f"{' | '.join(row['uncertainty_notes']) or 'None'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _inventory_markdown_lines(inventory: dict[str, object]) -> list[str]:
    return [
        f"- Raw capture posture: `{inventory.get('temporal_capture_posture', 'unknown')}`",
        f"- Sites with numeric intervals: `{inventory.get('numeric_interval_row_count', 0)}`",
        f"- Captured chronology records: `{inventory.get('chronology_record_count', 0)}`",
        f"- Dating-range records: `{inventory.get('dating_range_row_count', 0)}`",
        f"- Relative-period records: `{inventory.get('relative_period_row_count', 0)}`",
        f"- Modelled analysis-entity ages: `{inventory.get('analysis_entity_age_row_count', 0)}`",
        f"- Geochronology records: `{inventory.get('geochronology_row_count', 0)}`",
        f"- Dendrochronology records: `{inventory.get('dendro_date_row_count', 0)}`",
        f"- Bibliography relations: `{inventory.get('bibliography_row_count', 0)}`",
        f"- Sites without numeric chronology: `{inventory.get('unresolved_site_count', 0)}`",
    ]
