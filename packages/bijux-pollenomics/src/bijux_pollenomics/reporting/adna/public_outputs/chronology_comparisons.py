from __future__ import annotations

import json
from pathlib import Path

from ....core.temporal_semantics import (
    InvalidBpIntervalError,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)
from ...models import CountryReport


def _build_animal_human_chronology_overlap(
    country_payloads: list[dict[str, object]],
    country_reports: tuple[CountryReport, ...],
) -> dict[str, object]:
    report_by_country = {report.country: report for report in country_reports}
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        report = report_by_country.get(country)
        if report is None:
            continue
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            key = (str(row["species_latin_name"]), str(row["animal_scope"]))
            grouped.setdefault(key, []).append(row)
        for (species_name, animal_scope), species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for human_locality in report.localities:
                matched = False
                comparable = False
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    human_interval = _interval_from_record(human_locality)
                    if animal_interval is None or human_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, human_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": animal_scope,
                    "animal_locality_count": len(species_rows),
                    "human_locality_count": len(report.localities),
                    "overlapping_human_localities": overlapping,
                    "non_overlapping_human_localities": non_overlapping,
                    "noncomparable_human_localities": noncomparable,
                    "assignment_confidence": str(
                        species_rows[0]["country_assignment_confidence"]
                    ),
                    "overlap_status": _overlap_status(
                        overlapping, non_overlapping, noncomparable
                    ),
                }
            )
    return {
        "schema_version": "animal-human-chronology-overlap.v1",
        "rows": rows,
    }


def _build_animal_pollen_chronology_overlap(
    country_payloads: list[dict[str, object]],
    atlas_output_dir: Path,
) -> dict[str, object]:
    pollen_records = _load_pollen_records(atlas_output_dir)
    rows: list[dict[str, object]] = []
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            key = (str(row["species_latin_name"]), str(row["animal_scope"]))
            grouped.setdefault(key, []).append(row)
        country_pollen = [row for row in pollen_records if row["country"] == country]
        for (species_name, animal_scope), species_rows in sorted(grouped.items()):
            overlapping = 0
            non_overlapping = 0
            noncomparable = 0
            for pollen_row in country_pollen:
                matched = False
                comparable = False
                pollen_interval = _interval_from_row(pollen_row)
                for row in species_rows:
                    animal_interval = _interval_from_row(row)
                    if animal_interval is None or pollen_interval is None:
                        continue
                    comparable = True
                    if _intervals_overlap(animal_interval, pollen_interval):
                        matched = True
                        break
                if matched:
                    overlapping += 1
                elif comparable:
                    non_overlapping += 1
                else:
                    noncomparable += 1
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(species_rows[0]["species_common_name"]),
                    "animal_scope": animal_scope,
                    "animal_locality_count": len(species_rows),
                    "pollen_record_count": len(country_pollen),
                    "overlapping_pollen_records": overlapping,
                    "non_overlapping_pollen_records": non_overlapping,
                    "noncomparable_pollen_records": noncomparable,
                    "assignment_confidence": str(
                        species_rows[0]["country_assignment_confidence"]
                    ),
                    "overlap_status": _overlap_status(
                        overlapping, non_overlapping, noncomparable
                    ),
                }
            )
    return {
        "schema_version": "animal-pollen-chronology-overlap.v1",
        "rows": rows,
    }


def _load_pollen_records(atlas_output_dir: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for filename in (
        "nordic_pollen_sites.geojson",
        "nordic_pollen_site_sequences.geojson",
    ):
        path = atlas_output_dir / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if not isinstance(properties, dict):
                continue
            records.append(
                {
                    "country": str(properties.get("country", "")),
                    "time_start_bp": _optional_int(properties.get("time_start_bp")),
                    "time_end_bp": _optional_int(properties.get("time_end_bp")),
                    "time_mean_bp": _optional_int(properties.get("time_mean_bp")),
                    "time_label": str(properties.get("time_label", "")),
                    "source": str(properties.get("source", "")),
                    "name": str(properties.get("name", "")),
                }
            )
    return records


def _interval_from_record(record: object) -> tuple[int, int] | None:
    time_start = getattr(record, "time_start_bp", None)
    time_end = getattr(record, "time_end_bp", None)
    time_mean = getattr(record, "time_mean_bp", None)
    return _normalize_interval(time_start, time_end, time_mean)


def _interval_from_row(row: dict[str, object]) -> tuple[int, int] | None:
    return _normalize_interval(
        _optional_int(row.get("time_start_bp")),
        _optional_int(row.get("time_end_bp")),
        _optional_int(row.get("time_mean_bp")),
    )


def _normalize_interval(
    time_start: int | None,
    time_end: int | None,
    time_mean: int | None,
) -> tuple[int, int] | None:
    try:
        interval = canonical_bp_interval(time_start, time_end)
        if interval is None and time_mean is not None:
            interval = canonical_bp_interval(time_mean, time_mean)
    except InvalidBpIntervalError:
        return None
    if interval is None:
        return None
    return (int(interval.younger_bp), int(interval.older_bp))


def _intervals_overlap(
    left: tuple[int, int],
    right: tuple[int, int],
) -> bool:
    try:
        left_interval = canonical_bp_interval(*left)
        right_interval = canonical_bp_interval(*right)
    except InvalidBpIntervalError:
        return False
    if left_interval is None or right_interval is None:
        return False
    return closed_bp_intervals_overlap(left_interval, right_interval)


def _overlap_status(
    overlapping: int,
    non_overlapping: int,
    noncomparable: int,
) -> str:
    if overlapping > 0:
        return "overlap_detected"
    if non_overlapping > 0:
        return "no_overlap_detected"
    if noncomparable > 0:
        return "chronology_not_comparable"
    return "no_context_rows"


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value)
        except ValueError:
            return None
    return None
