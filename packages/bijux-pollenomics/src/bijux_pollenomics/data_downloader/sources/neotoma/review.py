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
        age_ranges = _age_ranges(row)
        bp_age_ranges = _bp_age_ranges(row)
        bp_support_posture = _bp_support_posture(row)
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
                "bp_support_posture": bp_support_posture,
                "supported_age_range_count": len(bp_age_ranges),
                "all_age_range_count": len(age_ranges),
                "bp_age_range_units": [
                    str(age_range.get("units", "")).strip()
                    for age_range in bp_age_ranges
                    if str(age_range.get("units", "")).strip()
                ],
                "all_age_range_units": [
                    str(age_range.get("units", "")).strip()
                    for age_range in age_ranges
                    if str(age_range.get("units", "")).strip()
                ],
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
        "schema_version": "neotoma-temporal-review.v2",
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
                f"- Sites with BP age ranges but no chronology rows: `{coverage_summary.get('site_count_with_bp_age_ranges_but_no_chronology_rows', 0)}`",
                f"- Sites with chronology-backed BP age ranges: `{coverage_summary.get('site_count_with_bp_age_ranges_and_chronology_rows', 0)}`",
                f"- Sites with non-BP age ranges only: `{coverage_summary.get('site_count_with_non_bp_age_ranges_only', 0)}`",
                f"- Sites with no age ranges at all: `{coverage_summary.get('site_count_with_no_age_ranges', 0)}`",
                f"- Sites without publishable BP windows: `{coverage_summary.get('site_count_without_bp_age_ranges', 0)}`",
                f"- Capture posture: `{coverage_summary.get('chronology_capture_posture', 'unknown')}`",
            ]
        )
    table_rows = "\n".join(
        (
            f"| {row.get('site_name', 'Unknown')} (`{row.get('site_id', '')}`) | "
            f"{row.get('country', '') or 'Unknown'} | "
            f"{row.get('comparability_posture', '') or 'unresolved'} | "
            f"{row.get('summary_label', '') or 'Unresolved time semantics'} | "
            f"{row.get('bp_support_posture', '') or 'unknown'} | "
            f"{row.get('supported_age_range_count', 0)} | "
            f"{row.get('chronology_count', 0)} |"
        )
        for row in rows
    )
    if not table_rows:
        table_rows = (
            "| No reviewed sites | Unknown | unresolved | "
            "Unresolved time semantics | unknown | 0 | 0 |"
        )
    return f"""# Neotoma temporal review

This review keeps Neotoma pollen sites honest about chronology comparability. It separates site-level BP coverage windows from explicit chronology-row support, so broad age ranges do not get mistaken for richer sample-model chronologies when the checked-in raw capture does not actually contain those rows.

- Reviewed sites: `{payload.get("row_count", 0)}`
{summary}
{coverage_lines}

| Site | Country | Comparability posture | Time summary | BP support posture | Supported BP age ranges | Chronologies |
| --- | --- | --- | --- | --- | ---: | ---: |
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


def _coverage_summary(rows: list[dict[str, object]]) -> dict[str, int | str]:
    site_count_with_age_ranges = sum(1 for row in rows if _age_ranges(row))
    site_count_with_bp_age_ranges = sum(1 for row in rows if _bp_age_ranges(row))
    site_count_with_chronologies = sum(
        1 for row in rows if _parse_int_or_default(row.get("chronology_count")) > 0
    )
    site_count_with_bp_age_ranges_but_no_chronology_rows = sum(
        1
        for row in rows
        if _bp_support_posture(row) == "bp_age_ranges_without_chronology_rows"
    )
    site_count_with_bp_age_ranges_and_chronology_rows = sum(
        1
        for row in rows
        if _bp_support_posture(row) == "bp_age_ranges_with_chronology_rows"
    )
    site_count_with_non_bp_age_ranges_only = sum(
        1 for row in rows if _bp_support_posture(row) == "non_bp_age_ranges_only"
    )
    site_count_with_no_age_ranges = sum(
        1 for row in rows if _bp_support_posture(row) == "no_age_ranges"
    )
    chronology_capture_posture = _chronology_capture_posture(
        site_count_with_bp_age_ranges=site_count_with_bp_age_ranges,
        site_count_with_chronologies=site_count_with_chronologies,
    )
    return {
        "site_count_with_age_ranges": site_count_with_age_ranges,
        "site_count_with_bp_age_ranges": site_count_with_bp_age_ranges,
        "site_count_with_chronologies": site_count_with_chronologies,
        "site_count_with_bp_age_ranges_but_no_chronology_rows": site_count_with_bp_age_ranges_but_no_chronology_rows,
        "site_count_with_bp_age_ranges_and_chronology_rows": site_count_with_bp_age_ranges_and_chronology_rows,
        "site_count_with_non_bp_age_ranges_only": site_count_with_non_bp_age_ranges_only,
        "site_count_with_no_age_ranges": site_count_with_no_age_ranges,
        "site_count_without_bp_age_ranges": len(rows) - site_count_with_bp_age_ranges,
        "chronology_capture_posture": chronology_capture_posture,
    }


def _age_ranges(row: dict[str, object]) -> list[dict[str, object]]:
    age_ranges = row.get("age_ranges")
    if not isinstance(age_ranges, list):
        return []
    return [age_range for age_range in age_ranges if isinstance(age_range, dict)]


def _bp_age_ranges(row: dict[str, object]) -> list[dict[str, object]]:
    return [
        age_range
        for age_range in _age_ranges(row)
        if "bp" in str(age_range.get("units", "")).strip().casefold()
    ]


def _bp_support_posture(row: dict[str, object]) -> str:
    if _bp_age_ranges(row):
        if _parse_int_or_default(row.get("chronology_count")) > 0:
            return "bp_age_ranges_with_chronology_rows"
        return "bp_age_ranges_without_chronology_rows"
    if _age_ranges(row):
        return "non_bp_age_ranges_only"
    return "no_age_ranges"


def _chronology_capture_posture(
    *,
    site_count_with_bp_age_ranges: int,
    site_count_with_chronologies: int,
) -> str:
    if site_count_with_chronologies > 0:
        return "bp_site_spans_with_some_chronology_rows"
    if site_count_with_bp_age_ranges > 0:
        return "bp_site_spans_without_chronology_rows"
    return "no_publishable_bp_age_ranges"
