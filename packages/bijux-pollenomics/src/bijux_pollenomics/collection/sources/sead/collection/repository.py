from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from .validation import validate_sead_rows


def validate_repository_site_archive(raw_path: Path) -> None:
    """Fail on malformed legacy site input before consulting derived acquisitions."""
    if not raw_path.exists():
        return
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    rows = payload.get("rows") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise ValueError(f"SEAD archive rows are invalid: {raw_path}")
    if any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"SEAD archive contains a non-object row: {raw_path}")
    validate_sead_rows("tbl_sites", [row for row in rows if isinstance(row, Mapping)])


def load_sead_acquisition_rows(
    copied_files: Mapping[str, bytes], table: str
) -> list[dict[str, object]]:
    payload_path = f"payloads/{table}.json"
    payload_bytes = copied_files.get(payload_path)
    if payload_bytes is None:
        raise ValueError(f"SEAD acquisition table is missing: {payload_path}")
    payload = json.loads(payload_bytes)
    if not isinstance(payload, dict) or payload.get("table") != table:
        raise ValueError(f"SEAD acquisition table identity is invalid: {payload_path}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"SEAD acquisition rows are invalid: {payload_path}")
    return [dict(row) for row in rows]


def attach_sead_country_decisions(
    copied_files: Mapping[str, bytes], rows: list[dict[str, object]]
) -> None:
    decision_path = "country-decisions.json"
    decision_bytes = copied_files.get(decision_path)
    if decision_bytes is None:
        raise ValueError("SEAD country decisions are missing")
    payload = json.loads(decision_bytes)
    decisions = payload.get("decisions") if isinstance(payload, dict) else None
    if not isinstance(decisions, list) or any(
        not isinstance(decision, dict) for decision in decisions
    ):
        raise ValueError(f"SEAD country decisions are invalid: {decision_path}")
    decisions_by_site_id = {decision.get("site_id"): decision for decision in decisions}
    for row in rows:
        site_id = row.get("site_id")
        decision = decisions_by_site_id.get(site_id)
        if not isinstance(decision, dict):
            raise ValueError(f"SEAD admitted site lacks country decision: {site_id}")
        decision_detail = decision.get("decision")
        country_code = decision.get("governed_country_code")
        if country_code not in {"SE", "DK", "NO", "FI"} or not isinstance(
            decision_detail, dict
        ):
            raise ValueError(f"SEAD admitted site is not assigned: {site_id}")
        assignment_method = decision_detail.get("decision_method")
        if not isinstance(assignment_method, str) or not assignment_method:
            raise ValueError(f"SEAD country assignment method is missing: {site_id}")
        row["country_code"] = country_code
        row["country_assignment_method"] = assignment_method


def build_repository_inventory_summary(
    rows: list[dict[str, object]],
) -> dict[str, int | str]:
    def record_count(key: str) -> int:
        return sum(
            len(value) for row in rows if isinstance((value := row.get(key)), list)
        )

    def site_count(key: str) -> int:
        return sum(
            1
            for row in rows
            if isinstance((value := row.get(key)), list) and len(value) > 0
        )

    numeric_interval_row_count = sum(
        1
        for row in rows
        if isinstance(row.get("time_start_bp"), int)
        and isinstance(row.get("time_end_bp"), int)
    )
    dating_range_row_count = record_count("dating_range_rows")
    relative_period_row_count = record_count("relative_period_rows")
    analysis_entity_age_row_count = record_count("analysis_entity_age_rows")
    geochronology_row_count = record_count("geochronology_rows")
    dendro_date_row_count = record_count("dendro_date_rows")
    bibliography_row_count = record_count("bibliography_rows")
    chronology_record_count = sum(
        (
            dating_range_row_count,
            relative_period_row_count,
            analysis_entity_age_row_count,
            geochronology_row_count,
            dendro_date_row_count,
        )
    )
    temporal_counts = (
        dating_range_row_count,
        relative_period_row_count,
        analysis_entity_age_row_count,
        geochronology_row_count,
        dendro_date_row_count,
        numeric_interval_row_count,
    )
    temporal_capture_posture = (
        "linked_chronology_captured" if any(temporal_counts) else "site_inventory_only"
    )
    return {
        "row_count": len(rows),
        "site_row_count": len(rows),
        "bibliography_row_count": bibliography_row_count,
        "bibliography_site_count": site_count("bibliography_rows"),
        "dating_range_row_count": dating_range_row_count,
        "dating_range_site_count": site_count("dating_range_rows"),
        "relative_period_row_count": relative_period_row_count,
        "relative_period_site_count": site_count("relative_period_rows"),
        "analysis_entity_age_row_count": analysis_entity_age_row_count,
        "analysis_entity_age_site_count": site_count("analysis_entity_age_rows"),
        "geochronology_row_count": geochronology_row_count,
        "geochronology_site_count": site_count("geochronology_rows"),
        "dendro_date_row_count": dendro_date_row_count,
        "dendro_date_site_count": site_count("dendro_date_rows"),
        "chronology_record_count": chronology_record_count,
        "numeric_interval_row_count": numeric_interval_row_count,
        "unresolved_site_count": len(rows) - numeric_interval_row_count,
        "site_inventory_only_row_count": len(rows) - numeric_interval_row_count,
        "temporal_capture_posture": temporal_capture_posture,
    }
