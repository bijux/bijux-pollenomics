from __future__ import annotations

from datetime import date
import json
from pathlib import Path

from ....core.files import write_json
from ...models import ContextPointRecord

__all__ = [
    "build_neotoma_temporal_review",
    "render_neotoma_temporal_review_markdown",
    "write_neotoma_review_outputs",
]


def build_neotoma_temporal_review(
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> dict[str, object]:
    """Build one governed Neotoma review of chronology comparability and coverage."""
    record_lookup = {record.record_id: record for record in records}
    review_rows: list[dict[str, object]] = []
    posture_counts: dict[str, int] = {}
    for row in rows:
        site_id = str(row.get("siteid", "")).strip()
        record = record_lookup.get(site_id)
        semantics = record.temporal_semantics if record is not None else {}
        posture = (
            str(semantics.get("comparability_posture", "")).strip() or "unresolved"
        )
        posture_counts[posture] = posture_counts.get(posture, 0) + 1
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("sitename", "")).strip(),
                "country": str(record.country if record is not None else "").strip(),
                "comparability_posture": posture,
                "temporal_window_label": str(
                    semantics.get("temporal_window_label", "")
                ).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "dataset_count": _parse_int_or_default(row.get("dataset_count")),
                "collection_unit_count": len(row.get("collectionunits", []))
                if isinstance(row.get("collectionunits"), list)
                else 0,
                "sample_count": _parse_int_or_default(row.get("sample_count")),
                "chronology_count": _parse_int_or_default(row.get("chronology_count")),
                "supported_age_range_count": len(
                    [
                        age_range
                        for age_range in row.get("age_ranges", [])
                        if isinstance(age_range, dict)
                        and "bp" in str(age_range.get("units", "")).strip().casefold()
                    ]
                )
                if isinstance(row.get("age_ranges"), list)
                else 0,
                "all_age_range_count": len(row.get("age_ranges", []))
                if isinstance(row.get("age_ranges"), list)
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
    coverage_summary = _coverage_summary(rows)
    return {
        "schema_version": "neotoma-temporal-review.v1",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "comparability_posture_counts": posture_counts,
        "coverage_summary": coverage_summary,
        "rows": review_rows,
    }


def write_neotoma_review_outputs(
    output_root: Path,
    *,
    rows: list[dict[str, object]],
    records: list[ContextPointRecord],
) -> None:
    """Write checked-in Neotoma review packets beside normalized outputs."""
    review_root = Path(output_root) / "review"
    review_root.mkdir(parents=True, exist_ok=True)
    temporal_review = build_neotoma_temporal_review(rows, records)
    write_json(review_root / "temporal_review.json", temporal_review)
    (review_root / "temporal_review.md").write_text(
        render_neotoma_temporal_review_markdown(temporal_review),
        encoding="utf-8",
    )
    (review_root / "temporal_review.csv").write_text(
        _render_review_csv(temporal_review["rows"]),
        encoding="utf-8",
    )


def render_neotoma_temporal_review_markdown(payload: dict[str, object]) -> str:
    """Render the Neotoma temporal review in plain repository markdown."""
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        rows = []
    counts = payload.get("comparability_posture_counts", {})
    if not isinstance(counts, dict):
        counts = {}
    coverage_summary = payload.get("coverage_summary", {})
    if not isinstance(coverage_summary, dict):
        coverage_summary = {}
    summary = (
        "\n".join(f"- {key}: `{value}`" for key, value in sorted(counts.items()))
        or "- unresolved: `0`"
    )
    coverage_lines = ""
    if coverage_summary:
        coverage_lines = "\n".join(
            [
                f"- Sites with age ranges: `{coverage_summary.get('site_count_with_age_ranges', 0)}`",
                f"- Sites with BP age ranges: `{coverage_summary.get('site_count_with_bp_age_ranges', 0)}`",
                f"- Sites with chronology rows: `{coverage_summary.get('site_count_with_chronologies', 0)}`",
                f"- Sites without publishable BP windows: `{coverage_summary.get('site_count_without_bp_age_ranges', 0)}`",
            ]
        )
    table_rows = "\n".join(
        (
            f"| {row.get('site_name', 'Unknown')} (`{row.get('site_id', '')}`) | "
            f"{row.get('country', '') or 'Unknown'} | "
            f"{row.get('comparability_posture', '') or 'unresolved'} | "
            f"{row.get('summary_label', '') or 'Unresolved time semantics'} | "
            f"{row.get('supported_age_range_count', 0)} | "
            f"{row.get('chronology_count', 0)} |"
        )
        for row in rows
    )
    if not table_rows:
        table_rows = "| No reviewed sites | Unknown | unresolved | Unresolved time semantics | 0 | 0 |"
    return f"""# Neotoma temporal review

This review keeps Neotoma pollen sites honest about chronology comparability. It separates sites with usable BP coverage from sites that only carry non-BP age labels or no publishable time window at all.

- Reviewed sites: `{payload.get("row_count", 0)}`
{summary}
{coverage_lines}

| Site | Country | Comparability posture | Time summary | Supported BP age ranges | Chronologies |
| --- | --- | --- | --- | ---: | ---: |
{table_rows}
"""


def _render_review_csv(rows: object) -> str:
    if not isinstance(rows, list) or not rows:
        return ""
    fieldnames = list(rows[0].keys())
    rendered_rows = [",".join(fieldnames)]
    for row in rows:
        if not isinstance(row, dict):
            continue
        rendered_rows.append(
            ",".join(_csv_cell(row.get(fieldname, "")) for fieldname in fieldnames)
        )
    return "\n".join(rendered_rows) + "\n"


def _csv_cell(value: object) -> str:
    text = (
        json.dumps(value, ensure_ascii=False) if isinstance(value, list) else str(value)
    )
    escaped = text.replace('"', '""')
    if any(token in escaped for token in (",", '"', "\n")):
        return f'"{escaped}"'
    return escaped


def _parse_int_or_default(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0


def _coverage_summary(rows: list[dict[str, object]]) -> dict[str, int]:
    def _age_ranges(row: dict[str, object]) -> list[dict[str, object]]:
        age_ranges = row.get("age_ranges")
        if not isinstance(age_ranges, list):
            return []
        return [age_range for age_range in age_ranges if isinstance(age_range, dict)]

    def _has_bp_age_range(row: dict[str, object]) -> bool:
        return any(
            "bp" in str(age_range.get("units", "")).strip().casefold()
            for age_range in _age_ranges(row)
        )

    site_count_with_age_ranges = sum(1 for row in rows if _age_ranges(row))
    site_count_with_bp_age_ranges = sum(1 for row in rows if _has_bp_age_range(row))
    site_count_with_chronologies = sum(
        1 for row in rows if _parse_int_or_default(row.get("chronology_count")) > 0
    )
    return {
        "site_count_with_age_ranges": site_count_with_age_ranges,
        "site_count_with_bp_age_ranges": site_count_with_bp_age_ranges,
        "site_count_with_chronologies": site_count_with_chronologies,
        "site_count_without_bp_age_ranges": len(rows) - site_count_with_bp_age_ranges,
    }
