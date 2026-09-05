from __future__ import annotations

from typing import cast

from .chronology_comparisons import _optional_int


def _build_first_appearance_by_country(
    country_payloads: list[dict[str, object]],
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    input_locality_count = 0
    dated_locality_count = 0
    undated_locality_count = 0
    for payload in country_payloads:
        country = str(payload.get("country", ""))
        localities = payload.get("localities", [])
        if not isinstance(localities, list):
            continue
        grouped: dict[str, list[dict[str, object]]] = {}
        for row in localities:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(str(row["species_latin_name"]), []).append(row)
        for species_name, species_rows in sorted(grouped.items()):
            input_locality_count += len(species_rows)
            dated_rows = [
                (row, first_signal)
                for row in species_rows
                if (first_signal := _first_signal_bp(row)) is not None
            ]
            dated_locality_count += len(dated_rows)
            undated_locality_count += len(species_rows) - len(dated_rows)
            if not dated_rows:
                continue
            oldest_row, first_signal_bp = max(dated_rows, key=lambda item: item[1])
            rows.append(
                {
                    "country": country,
                    "species_latin_name": species_name,
                    "species_common_name": str(oldest_row["species_common_name"]),
                    "animal_scope": str(oldest_row["animal_scope"]),
                    "first_signal_bp": first_signal_bp,
                    "time_label": str(oldest_row["time_label"]),
                    "project_accession": str(oldest_row["project_accession"]),
                    "locality": str(oldest_row["locality"]),
                    "assignment_confidence": str(
                        oldest_row["country_assignment_confidence"]
                    ),
                }
            )
    rows.sort(
        key=lambda row: (
            row["country"],
            -int(cast(str, row["first_signal_bp"])),
            row["species_latin_name"],
        )
    )
    return {
        "schema_version": "animal-first-appearance-by-country.v1",
        "reconciliation": {
            "input_locality_count": input_locality_count,
            "dated_locality_count": dated_locality_count,
            "undated_locality_count": undated_locality_count,
            "refusal_reason_counts": {
                "chronology_unavailable": undated_locality_count,
            },
        },
        "rows": rows,
    }


def _first_signal_bp(row: dict[str, object]) -> int | None:
    candidates = [
        value
        for value in (
            _optional_int(row.get("time_start_bp")),
            _optional_int(row.get("time_end_bp")),
            _optional_int(row.get("time_mean_bp")),
        )
        if value is not None
    ]
    return max(candidates) if candidates else None
