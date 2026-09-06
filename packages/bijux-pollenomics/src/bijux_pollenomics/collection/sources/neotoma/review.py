from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ....core.files import write_json
from ...contracts.models import ContextPointRecord
from .chronology import neotoma_age_range_units_supported

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
    projected_site_ids = set(record_lookup)
    review_rows: list[dict[str, object]] = []
    posture_counts: dict[str, int] = {}
    for row in rows:
        site_id = str(row.get("siteid", "")).strip()
        record = record_lookup.get(site_id)
        semantics: dict[str, object] = {}
        if record is not None and isinstance(record.temporal_semantics, dict):
            semantics = record.temporal_semantics
        projected = record is not None
        posture = str(semantics.get("comparability_posture", "")).strip()
        if projected:
            posture = posture or "unresolved"
            posture_counts[posture] = posture_counts.get(posture, 0) + 1
        else:
            posture = "unresolved"
        age_ranges = _age_ranges(row)
        source_bp_ranges = _source_bp_labelled_age_ranges(row)
        calendar_comparable_ranges = _calendar_comparable_bp_system_age_ranges(row)
        bp_context_posture = _bp_context_posture(row)
        collection_units = row.get("collectionunits")
        review_rows.append(
            {
                "site_id": site_id,
                "site_name": str(row.get("sitename", "")).strip(),
                "country": str(
                    record.country if record is not None else "UNASSIGNED"
                ).strip(),
                "projection_status": (
                    "governed_country_projection"
                    if projected
                    else "excluded_from_governed_country_projection"
                ),
                "projection_exclusion_reason": (
                    "" if projected else "country_assignment_not_accepted"
                ),
                "comparability_posture": posture,
                "temporal_window_label": str(
                    semantics.get("temporal_window_label", "")
                ).strip(),
                "summary_label": str(semantics.get("summary_label", "")).strip(),
                "dataset_count": _parse_int_or_default(row.get("dataset_count")),
                "collection_unit_count": len(collection_units)
                if isinstance(collection_units, list)
                else 0,
                "sample_count": _parse_int_or_default(row.get("sample_count")),
                "compact_chronology_row_count": _parse_int_or_default(
                    row.get("chronology_count")
                ),
                "bp_context_posture": bp_context_posture,
                "source_bp_labelled_age_range_count": len(source_bp_ranges),
                "calendar_comparable_bp_system_age_range_count": len(
                    calendar_comparable_ranges
                ),
                "all_age_range_count": len(age_ranges),
                "source_bp_labelled_age_range_units": [
                    str(age_range.get("units", "")).strip()
                    for age_range in source_bp_ranges
                    if str(age_range.get("units", "")).strip()
                ],
                "calendar_comparable_bp_system_age_range_units": [
                    str(age_range.get("units", "")).strip()
                    for age_range in calendar_comparable_ranges
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
    projected_rows = [
        row for row in rows if str(row.get("siteid", "")).strip() in projected_site_ids
    ]
    coverage_summary = _coverage_summary(projected_rows)
    excluded_site_ids = sorted(
        {
            str(row.get("siteid", "")).strip()
            for row in rows
            if str(row.get("siteid", "")).strip() not in projected_site_ids
        }
    )
    return {
        "schema_version": "neotoma-temporal-review.v4",
        "generated_on": str(date.today()),
        "row_count": len(review_rows),
        "source_site_denominator": len(rows),
        "governed_country_projected_site_count": len(projected_site_ids),
        "excluded_site_count": len(excluded_site_ids),
        "excluded_site_ids": excluded_site_ids,
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
                f"- Sites with source BP-labelled context: `{coverage_summary.get('site_count_with_source_bp_labelled_context', 0)}`",
                f"- Sites with calendar-comparable BP-system context: `{coverage_summary.get('site_count_with_calendar_comparable_bp_system_context', 0)}`",
                f"- Sites with non-comparable BP-system context only: `{coverage_summary.get('site_count_with_noncomparable_bp_system_context_only', 0)}`",
                f"- Sites with compact chronology rows: `{coverage_summary.get('site_count_with_compact_chronology_rows', 0)}`",
                f"- Sites with non-BP age-range context only: `{coverage_summary.get('site_count_with_non_bp_age_range_context_only', 0)}`",
                f"- Sites without age-range context: `{coverage_summary.get('site_count_without_age_range_context', 0)}`",
                f"- Sites without source BP-labelled context: `{coverage_summary.get('site_count_without_source_bp_labelled_context', 0)}`",
                f"- Compact numeric site intervals: `{coverage_summary.get('compact_numeric_site_interval_count', 0)}`",
                f"- Sites without compact numeric intervals: `{coverage_summary.get('site_count_without_compact_numeric_interval', 0)}`",
                f"- Sites with non-continuous age-range context: `{coverage_summary.get('site_count_with_non_continuous_age_range_context', 0)}`",
                f"- Capture posture: `{coverage_summary.get('chronology_capture_posture', 'unknown')}`",
            ]
        )
    table_rows = "\n".join(
        (
            f"| {row.get('site_name', 'Unknown')} (`{row.get('site_id', '')}`) | "
            f"{row.get('country', '') or 'Unknown'} | "
            f"{row.get('projection_status', '') or 'unknown'} | "
            f"{row.get('comparability_posture', '') or 'unresolved'} | "
            f"{row.get('summary_label', '') or 'Unresolved time semantics'} | "
            f"{row.get('bp_context_posture', '') or 'unknown'} | "
            f"{row.get('source_bp_labelled_age_range_count', 0)} | "
            f"{row.get('calendar_comparable_bp_system_age_range_count', 0)} | "
            f"{row.get('compact_chronology_row_count', 0)} |"
        )
        for row in rows
    )
    if not table_rows:
        table_rows = (
            "| No reviewed sites | Unknown | unknown | unresolved | "
            "Unresolved time semantics | unknown | 0 | 0 | 0 |"
        )
    return f"""# Neotoma temporal review

This review keeps Neotoma pollen sites honest about chronology comparability. A source label containing BP is context, not proof of calendar comparability: uncalibrated radiocarbon and varve systems remain explicitly non-comparable. Even calendar-comparable systems are not emitted as one compact site interval because extrema across datasets and samples do not prove continuous evidence between their endpoints. Numeric map chronology comes from admitted sample-owned relational claims.

- Reviewed source sites: `{payload.get("source_site_denominator", payload.get("row_count", 0))}`
- Governed-country projected sites: `{payload.get("governed_country_projected_site_count", 0)}`
- Excluded unassigned sites: `{payload.get("excluded_site_count", 0)}`
{summary}
{coverage_lines}

| Site | Country | Projection status | Comparability posture | Time summary | BP context posture | Source BP-labelled ranges | Calendar-comparable BP-system ranges | Compact chronology rows |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: |
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
    site_count_with_source_bp_labelled_context = sum(
        1 for row in rows if _source_bp_labelled_age_ranges(row)
    )
    site_count_with_calendar_comparable_bp_system_context = sum(
        1 for row in rows if _calendar_comparable_bp_system_age_ranges(row)
    )
    site_count_with_noncomparable_bp_system_context_only = sum(
        1
        for row in rows
        if _source_bp_labelled_age_ranges(row)
        and not _calendar_comparable_bp_system_age_ranges(row)
    )
    site_count_with_compact_chronology_rows = sum(
        1 for row in rows if _parse_int_or_default(row.get("chronology_count")) > 0
    )
    site_count_with_source_bp_labelled_context_but_no_compact_chronology_rows = sum(
        1
        for row in rows
        if _source_bp_labelled_age_ranges(row)
        and _parse_int_or_default(row.get("chronology_count")) == 0
    )
    site_count_with_source_bp_labelled_context_and_compact_chronology_rows = sum(
        1
        for row in rows
        if _source_bp_labelled_age_ranges(row)
        and _parse_int_or_default(row.get("chronology_count")) > 0
    )
    site_count_with_non_bp_age_range_context_only = sum(
        1 for row in rows if _bp_context_posture(row) == "non_bp_context_only"
    )
    site_count_without_age_range_context = sum(
        1 for row in rows if _bp_context_posture(row) == "no_age_range_context"
    )
    chronology_capture_posture = _chronology_capture_posture(
        site_count_with_source_bp_labelled_context=(
            site_count_with_source_bp_labelled_context
        ),
        site_count_with_calendar_comparable_bp_system_context=(
            site_count_with_calendar_comparable_bp_system_context
        ),
        site_count_with_compact_chronology_rows=(
            site_count_with_compact_chronology_rows
        ),
    )
    return {
        "site_count_with_age_ranges": site_count_with_age_ranges,
        "site_count_with_source_bp_labelled_context": site_count_with_source_bp_labelled_context,
        "site_count_with_calendar_comparable_bp_system_context": site_count_with_calendar_comparable_bp_system_context,
        "site_count_with_noncomparable_bp_system_context_only": site_count_with_noncomparable_bp_system_context_only,
        "site_count_with_compact_chronology_rows": site_count_with_compact_chronology_rows,
        "site_count_with_source_bp_labelled_context_but_no_compact_chronology_rows": site_count_with_source_bp_labelled_context_but_no_compact_chronology_rows,
        "site_count_with_source_bp_labelled_context_and_compact_chronology_rows": site_count_with_source_bp_labelled_context_and_compact_chronology_rows,
        "site_count_with_non_bp_age_range_context_only": site_count_with_non_bp_age_range_context_only,
        "site_count_without_age_range_context": site_count_without_age_range_context,
        "site_count_without_source_bp_labelled_context": len(rows)
        - site_count_with_source_bp_labelled_context,
        "compact_numeric_site_interval_count": 0,
        "site_count_without_compact_numeric_interval": len(rows),
        "site_count_with_non_continuous_age_range_context": site_count_with_age_ranges,
        "chronology_capture_posture": chronology_capture_posture,
    }


def _age_ranges(row: dict[str, object]) -> list[dict[str, object]]:
    age_ranges = row.get("age_ranges")
    if not isinstance(age_ranges, list):
        return []
    return [age_range for age_range in age_ranges if isinstance(age_range, dict)]


def _source_bp_labelled_age_ranges(
    row: dict[str, object],
) -> list[dict[str, object]]:
    return [
        age_range
        for age_range in _age_ranges(row)
        if "bp" in str(age_range.get("units", "")).strip().casefold()
    ]


def _calendar_comparable_bp_system_age_ranges(
    row: dict[str, object],
) -> list[dict[str, object]]:
    return [
        age_range
        for age_range in _age_ranges(row)
        if neotoma_age_range_units_supported(str(age_range.get("units", "")).strip())
    ]


def _bp_context_posture(row: dict[str, object]) -> str:
    if _calendar_comparable_bp_system_age_ranges(row):
        if _parse_int_or_default(row.get("chronology_count")) > 0:
            return "calendar_comparable_system_with_compact_chronology_rows"
        return "calendar_comparable_system_context_only"
    if _source_bp_labelled_age_ranges(row):
        return "noncomparable_bp_system_context_only"
    if _age_ranges(row):
        return "non_bp_context_only"
    return "no_age_range_context"


def _chronology_capture_posture(
    *,
    site_count_with_source_bp_labelled_context: int,
    site_count_with_calendar_comparable_bp_system_context: int,
    site_count_with_compact_chronology_rows: int,
) -> str:
    if site_count_with_compact_chronology_rows > 0:
        return "compact_context_with_separate_sample_chronology"
    if site_count_with_calendar_comparable_bp_system_context > 0:
        return "calendar_comparable_system_context_without_compact_chronology"
    if site_count_with_source_bp_labelled_context > 0:
        return "noncomparable_bp_system_context_only"
    return "no_source_bp_labelled_context"
