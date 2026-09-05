from __future__ import annotations


def inventory_summary(rows: list[dict[str, object]]) -> dict[str, int | str]:
    def sites_with_records(key: str) -> int:
        count = 0
        for row in rows:
            value = row.get(key)
            if isinstance(value, list) and value:
                count += 1
        return count

    def record_count(key: str) -> int:
        return sum(
            len(value) for row in rows if isinstance((value := row.get(key)), list)
        )

    numeric_interval_row_count = sum(
        1
        for row in rows
        if isinstance(row.get("time_start_bp"), int)
        and isinstance(row.get("time_end_bp"), int)
    )
    temporal_row_keys = (
        "dating_range_rows",
        "relative_period_rows",
        "analysis_entity_age_rows",
        "geochronology_rows",
        "dendro_date_rows",
    )
    dating_range_row_count = record_count("dating_range_rows")
    relative_period_row_count = record_count("relative_period_rows")
    analysis_entity_age_row_count = record_count("analysis_entity_age_rows")
    geochronology_row_count = record_count("geochronology_rows")
    dendro_date_row_count = record_count("dendro_date_rows")
    bibliography_row_count = record_count("bibliography_rows")
    site_inventory_only_row_count = sum(
        1 for row in rows if sead_row_capture_posture(row) == "site_inventory_only"
    )
    temporal_capture_posture = (
        "linked_chronology_captured"
        if any(
            count > 0
            for count in (
                numeric_interval_row_count,
                dating_range_row_count,
                relative_period_row_count,
            )
        )
        else "site_inventory_only"
    )
    return {
        "numeric_interval_row_count": numeric_interval_row_count,
        "dating_range_row_count": dating_range_row_count,
        "dating_range_site_count": sites_with_records("dating_range_rows"),
        "relative_period_row_count": relative_period_row_count,
        "relative_period_site_count": sites_with_records("relative_period_rows"),
        "analysis_entity_age_row_count": analysis_entity_age_row_count,
        "analysis_entity_age_site_count": sites_with_records(
            "analysis_entity_age_rows"
        ),
        "geochronology_row_count": geochronology_row_count,
        "geochronology_site_count": sites_with_records("geochronology_rows"),
        "dendro_date_row_count": dendro_date_row_count,
        "dendro_date_site_count": sites_with_records("dendro_date_rows"),
        "chronology_record_count": sum(record_count(key) for key in temporal_row_keys),
        "bibliography_row_count": bibliography_row_count,
        "bibliography_site_count": sites_with_records("bibliography_rows"),
        "unresolved_site_count": len(rows) - numeric_interval_row_count,
        "site_inventory_only_row_count": site_inventory_only_row_count,
        "temporal_capture_posture": temporal_capture_posture,
    }


def sead_row_capture_posture(row: dict[str, object]) -> str:
    has_temporal_rows = any(
        isinstance(row.get(key), list) and bool(row.get(key))
        for key in (
            "dating_range_rows",
            "relative_period_rows",
            "analysis_entity_age_rows",
            "geochronology_rows",
            "dendro_date_rows",
        )
    )
    has_bibliography = isinstance(row.get("bibliography_rows"), list) and bool(
        row.get("bibliography_rows")
    )
    if has_temporal_rows:
        return "linked_temporal_rows_captured"
    if has_bibliography:
        return "bibliography_only"
    return "site_inventory_only"
