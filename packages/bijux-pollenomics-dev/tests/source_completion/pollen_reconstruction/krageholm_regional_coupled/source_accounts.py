"""Recheck KRAG audit owners without reopening the native archive part."""

from __future__ import annotations

from collections import Counter
from typing import Any

from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.native_rows import (
    age_selection,
    literal_axes,
    source_number,
)

from .reading import exact
from .scalar import require

WINDOWS = tuple((low, low + 500) for low in range(2700, 5700, 500))
SMALL = ("BOKE", "BUS", "SOLSOE83")


def integer(value: object, *, positive: bool = False) -> bool:
    """Recognize a literal integer in the selected positive or nonnegative domain."""
    return type(value) is int and (value > 0 if positive else value >= 0)


def checked_krag(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Check Krageholm source owners and pooled age-window support."""
    require(
        audit["schema_version"] == "krageholm-regional-source-support.v1"
        and audit["status"] == "literal_source_support_accounted"
        and audit["identity"]
        == {
            "site_id": 3204,
            "dataset_id": 23013,
            "collection_unit_id": 16622,
            "handle": "KRAGMJNY",
            "source_sample_count": 96,
        },
        "qualified KRAG source identity differs",
    )
    chronology = audit["chronology"]
    require(
        chronology["selected_chronology_id"] == 13366
        and chronology["native_collection_default_reference"] == 13365,
        "explicit selected chronology and source reference differ",
    )
    declarations = chronology["source_chronology_declarations"]
    ids = [row["chronology_id"] for row in declarations]
    require(
        all(type(identifier) is int for identifier in ids)
        and len(set(ids)) == len(ids),
        "unique typed chronology declarations required",
    )
    metadata = {row["chronology_id"]: row["native_metadata"] for row in declarations}
    require(
        all(metadata[identifier]["isdefault"] is True for identifier in (13365, 13366))
        and chronology["selected_native_metadata"] == metadata[13366],
        "both source default flags must remain distinct from explicit selection",
    )
    samples = audit["samples"]
    sample_ids = [row["sample_id"] for row in samples]
    require(
        len(samples) == len(set(sample_ids)) == 96
        and all(integer(identifier) for identifier in sample_ids),
        "all96 typed unique native owner IDs required",
    )
    windows: dict[str, dict[str, Any]] = {}
    by_window: dict[tuple[int, int], list[dict[str, Any]]] = {
        bounds: [] for bounds in WINDOWS
    }
    dispositions: Counter[str] = Counter()
    complete = 0
    for index, row in enumerate(samples):
        require(row["native_sample_index"] == index, "native owner order differs")
        state, selected = age_selection(row["native_ages"])
        require(
            state == row["selected_age_status"] == "selected_typed_point"
            and selected == row["selected_age"],
            "selected age claim or assignment unavailable",
        )
        assert selected is not None
        age = source_number(selected["age"])
        assert age is not None
        bounds = next(
            (bounds for bounds in WINDOWS if bounds[0] <= age < bounds[1]), None
        )
        disposition = (
            "negative_native_age_retained"
            if age < 0
            else "in_requested_window"
            if bounds
            else "outside_requested_windows"
        )
        require(
            row["age_disposition"] == disposition
            and row["window"] == (list(bounds) if bounds else None),
            "native point window/disposition differs",
        )
        dispositions[disposition] += 1
        datum: list[dict[str, Any]] = [{} for _ in range(row["datum_row_count"])]
        seen: dict[int, dict[str, Any]] = {}
        for axis in row["taxa"]:
            for match in axis["native_matches"]:
                position, native = match["datum_index"], match["native"]
                require(
                    integer(position) and position < len(datum),
                    "native literal datum ordinal differs",
                )
                require(
                    position not in seen or seen[position] == native,
                    "conflicting repeated native literal witness",
                )
                datum[position] = native
                seen[position] = native
        panel = literal_axes(datum)
        for key, value in panel.items():
            exact(row[key], value)
        complete += panel["panel_complete"]
        require(
            row["pollen_denominator_status"] == "complete"
            and integer(row["pollen_N"], positive=True)
            and row["pollen_N"] == row["known_valid_pollen_cell_sum"],
            "qualified full pollen denominator unavailable",
        )
        expected_excluded = (
            None if row["panel_N"] is None else row["pollen_N"] - row["panel_N"]
        )
        require(
            row["excluded_pollen_N"] == expected_excluded
            and (expected_excluded is None or integer(expected_excluded)),
            "audited excluded pollen mass differs",
        )
        if bounds is not None:
            require(
                panel["panel_complete"] is True
                and integer(panel["panel_N"], positive=True),
                "incomplete/zero KRAG selected panel cannot be materialized",
            )
            by_window[bounds].append(row)
    require(
        dict(dispositions) == audit["population"]["age_disposition_counts"]
        and complete == audit["population"]["panel_complete_samples"],
        "complete KRAG audit population differs",
    )
    for bounds, rows in by_window.items():
        saved = [row for row in audit["windows"] if row["window"] == list(bounds)]
        require(
            len(saved) == 1 and bool(rows), "one nonempty KRAG window audit required"
        )
        item = saved[0]
        counts = [sum(row["panel_counts"][axis] for row in rows) for axis in range(2)]
        require(
            item["status"] == "supported"
            and item["sample_ids"] == [row["sample_id"] for row in rows]
            and item["member_count"] == len(rows)
            and item["unassignable_source_sample_ids"] == []
            and item["panel_counts"] == counts
            and item["panel_N"] == sum(counts)
            and item["pollen_N"] == sum(row["pollen_N"] for row in rows)
            and item["excluded_pollen_N"] == item["pollen_N"] - sum(counts),
            "KRAG pooled window membership or exact mass differs",
        )
        windows[f"cal-bp-{bounds[0]}-{bounds[1]}"] = item
    require(
        sum(item["member_count"] for item in windows.values()) == 19
        and len(audit["windows"]) == len(windows) == 6,
        "all19 selected owners/all6 windows required",
    )
    require(
        audit["engine_calls"] == audit["model_fits"] == 0
        and audit["scientific_or_field_admission"] is False,
        "source audit role differs",
    )
    return windows
