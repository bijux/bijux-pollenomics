"""Refresh repository-derived fields on persisted SEAD site rows."""

from __future__ import annotations

from bijux_pollenomics.core.text import clean_optional_text

from .chronology_records import (
    _analysis_entity_age_interval,
    _dendro_date_interval,
    _geochronology_interval,
)
from .temporal import (
    _interval_from_relative_age_label,
    _normalize_optional_interval,
    _normalized_period_labels,
    _relative_interval_from_range,
    _uncertainty_labels,
    merge_sead_intervals,
    sead_dating_interval,
    sead_interval_is_canonical,
)
from .values import parse_optional_int, parse_required_int


def _dict_rows(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def refresh_sead_repository_rows(rows: list[dict[str, object]]) -> None:
    """Backfill repository-owned derived SEAD fields from checked-in linked rows."""
    for row in rows:
        relative_rows = _dict_rows(row.get("relative_period_rows"))
        dating_rows = _dict_rows(row.get("dating_range_rows"))
        entity_age_rows = _dict_rows(row.get("analysis_entity_age_rows"))
        geochronology_rows = _dict_rows(row.get("geochronology_rows"))
        dendro_date_rows = _dict_rows(row.get("dendro_date_rows"))
        bibliography_rows = _dict_rows(row.get("bibliography_rows"))
        numeric_intervals: list[tuple[int, int]] = []
        for dating_row in dating_rows:
            interval = sead_dating_interval(
                dating_row,
                age_type=clean_optional_text(dating_row.get("age_type")),
            ) or _relative_interval_from_range(
                dating_row,
                age_type=clean_optional_text(dating_row.get("age_type")),
            )
            dating_row["time_start_bp"] = interval[0] if interval is not None else None
            dating_row["time_end_bp"] = interval[1] if interval is not None else None
            if interval is not None and sead_interval_is_canonical(interval):
                numeric_intervals.append(interval)
        for entity_age_row in entity_age_rows:
            interval = _analysis_entity_age_interval(entity_age_row)
            entity_age_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            entity_age_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None and sead_interval_is_canonical(interval):
                numeric_intervals.append(interval)
        for geochronology_row in geochronology_rows:
            interval = _geochronology_interval(geochronology_row)
            geochronology_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            geochronology_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None and sead_interval_is_canonical(interval):
                numeric_intervals.append(interval)
        for dendro_date_row in dendro_date_rows:
            interval = _dendro_date_interval(
                dendro_date_row,
                age_type=clean_optional_text(dendro_date_row.get("age_type")),
            )
            dendro_date_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            dendro_date_row["time_end_bp"] = (
                interval[1] if interval is not None else None
            )
            if interval is not None and sead_interval_is_canonical(interval):
                numeric_intervals.append(interval)
        contextual_intervals: list[tuple[int, int]] = []
        for relative_row in relative_rows:
            interval = _normalize_optional_interval(
                parse_optional_int(relative_row.get("time_start_bp")),
                parse_optional_int(relative_row.get("time_end_bp")),
            )
            if interval is None:
                interval = _interval_from_relative_age_label(
                    clean_optional_text(relative_row.get("relative_age_label"))
                )
                if interval is not None:
                    relative_row["interval_source"] = "encoded_relative_age_label"
            relative_row["time_start_bp"] = (
                interval[0] if interval is not None else None
            )
            relative_row["time_end_bp"] = interval[1] if interval is not None else None
            if interval is not None and sead_interval_is_canonical(interval):
                contextual_intervals.append(interval)
        numeric_time_interval = merge_sead_intervals(numeric_intervals)
        contextual_time_interval = merge_sead_intervals(contextual_intervals)
        time_interval = numeric_time_interval or contextual_time_interval
        row["relative_date_count"] = len(relative_rows)
        row["dating_range_count"] = len(dating_rows)
        row["analysis_entity_age_count"] = len(entity_age_rows)
        row["geochronology_count"] = len(geochronology_rows)
        row["dendro_date_count"] = len(dendro_date_rows)
        row["reference_count"] = max(
            parse_required_int(row.get("reference_count")),
            len(bibliography_rows),
        )
        row["time_start_bp"] = time_interval[0] if time_interval is not None else None
        row["time_end_bp"] = time_interval[1] if time_interval is not None else None
        row["numeric_time_start_bp"] = (
            numeric_time_interval[0] if numeric_time_interval is not None else None
        )
        row["numeric_time_end_bp"] = (
            numeric_time_interval[1] if numeric_time_interval is not None else None
        )
        row["contextual_time_start_bp"] = (
            contextual_time_interval[0]
            if contextual_time_interval is not None
            else None
        )
        row["contextual_time_end_bp"] = (
            contextual_time_interval[1]
            if contextual_time_interval is not None
            else None
        )
        row["temporal_summary"] = {
            "relative_period_count": len(relative_rows),
            "dating_range_count": len(dating_rows),
            "analysis_entity_age_count": len(entity_age_rows),
            "geochronology_count": len(geochronology_rows),
            "dendro_date_count": len(dendro_date_rows),
            "bibliography_count": len(bibliography_rows),
            "time_start_bp": row["time_start_bp"],
            "time_end_bp": row["time_end_bp"],
            "numeric_time_start_bp": row["numeric_time_start_bp"],
            "numeric_time_end_bp": row["numeric_time_end_bp"],
            "contextual_time_start_bp": row["contextual_time_start_bp"],
            "contextual_time_end_bp": row["contextual_time_end_bp"],
            "normalized_period_labels": _normalized_period_labels(relative_rows),
            "uncertainty_labels": _uncertainty_labels(
                relative_rows,
                dating_rows,
                entity_age_rows,
                geochronology_rows,
                dendro_date_rows,
            ),
        }


__all__ = ["refresh_sead_repository_rows"]
