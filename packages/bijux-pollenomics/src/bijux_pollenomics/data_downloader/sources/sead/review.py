from __future__ import annotations

from datetime import date
import json
from pathlib import Path

from ....core.files import write_json
from ...models import ContextPointRecord

__all__ = [
    "build_sead_temporal_review",
    "render_sead_temporal_review_markdown",
    "write_sead_review_outputs",
]


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
        semantics = record.temporal_semantics if record is not None else {}
        posture = str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        posture_counts[posture] = posture_counts.get(posture, 0) + 1
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("site_name", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "comparability_posture": posture,
                "temporal_window_label": str(
                    semantics.get("temporal_window_label", "")
                ).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "normalized_period_labels": list(
                    semantics.get("normalized_labels", [])
                    if isinstance(semantics.get("normalized_labels"), list)
                    else []
                ),
                "original_period_labels": list(
                    semantics.get("original_labels", [])
                    if isinstance(semantics.get("original_labels"), list)
                    else []
                ),
                "uncertainty_notes": list(
                    semantics.get("uncertainty_notes", [])
                    if isinstance(semantics.get("uncertainty_notes"), list)
                    else []
                ),
                "dating_range_count": len(row.get("dating_range_rows", []))
                if isinstance(row.get("dating_range_rows"), list)
                else 0,
                "relative_period_count": len(row.get("relative_period_rows", []))
                if isinstance(row.get("relative_period_rows"), list)
                else 0,
                "bibliography_count": len(row.get("bibliography_rows", []))
                if isinstance(row.get("bibliography_rows"), list)
                else 0,
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
        "schema_version": "sead-temporal-review.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "comparability_posture_counts": posture_counts,
        "rows": review_rows,
    }


def write_sead_review_outputs(
    output_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, str]:
    """Write SEAD review surfaces beside raw and normalized outputs."""
    review_root = Path(output_root) / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    payload = build_sead_temporal_review(rows, records)
    write_json(review_root / "temporal_review.json", payload)
    (review_root / "temporal_review.md").write_text(
        render_sead_temporal_review_markdown(payload),
        encoding="utf-8",
    )
    (review_root / "temporal_review.csv").write_text(
        _render_sead_temporal_review_csv(payload["rows"]),
        encoding="utf-8",
    )
    return {
        "temporal_review_json": "review/temporal_review.json",
        "temporal_review_markdown": "review/temporal_review.md",
        "temporal_review_csv": "review/temporal_review.csv",
    }


def render_sead_temporal_review_markdown(payload: dict[str, object]) -> str:
    rows = payload["rows"]
    lines = [
        "# SEAD temporal review",
        "",
        "This review keeps SEAD honest about site-level time semantics. It distinguishes numeric site spans, mixed site spans plus cultural labels, and label-only rows that should not be read like sample-owned dates.",
        "",
        f"- Reviewed sites: `{payload['row_count']}`",
    ]
    posture_counts = payload.get("comparability_posture_counts", {})
    if isinstance(posture_counts, dict):
        for key in sorted(posture_counts):
            lines.append(f"- {key.replace('_', ' ')}: `{posture_counts[key]}`")
    lines.extend(
        [
            "",
            "| Site | Country | Comparability posture | Time summary | Normalized period labels | Uncertainty notes |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['site_name']} (`{row['site_id']}`) | {row['country']} | "
            f"{row['comparability_posture']} | {row['summary_label']} | "
            f"{', '.join(row['normalized_period_labels']) or 'None'} | "
            f"{' | '.join(row['uncertainty_notes']) or 'None'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_sead_temporal_review_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return "site_id,site_name,comparability_posture,summary_label\n"
    fieldnames = list(rows[0].keys())
    lines = [",".join(fieldnames)]
    for row in rows:
        values = []
        for field in fieldnames:
            value = row.get(field)
            if isinstance(value, list):
                values.append(json.dumps(value, ensure_ascii=False))
            else:
                text = str(value).replace('"', '""')
                values.append(f'"{text}"' if "," in text or '"' in text else text)
        lines.append(",".join(values))
    lines.append("")
    return "\n".join(lines)
