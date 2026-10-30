"""Preserve every native sample while pooling the declared complete panel."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from .sources import TAXA, TAXON_IDS, WINDOWS, require


def native_counts(sample: dict[str, Any]) -> dict[str, Any]:
    """Separate literal integer pollen measurements from missing/nonpollen rows."""
    measured: dict[str, tuple[int, int]] = {}
    excluded = 0
    for datum in sample["datum"]:
        if datum.get("element") != "pollen" or datum.get("elementtype") != "pollen":
            excluded += 1
            continue
        require(datum.get("units") == "NISP", "Native pollen unit differs")
        value, name, taxon = (
            datum.get("value"),
            datum.get("variablename"),
            datum.get("taxonid"),
        )
        require(
            type(value) is int and value >= 0,
            "Native pollen count is not a nonnegative integer",
        )
        require(
            isinstance(name, str) and bool(name) and type(taxon) is int,
            "Native pollen identity differs",
        )
        require(
            name not in measured,
            "Duplicate native pollen label needs an aggregation decision",
        )
        measured[name] = (taxon, value)
    missing = [name for name in TAXA if name not in measured]
    for name, taxon in zip(TAXA, TAXON_IDS, strict=True):
        require(
            name not in measured or measured[name][0] == taxon,
            "Literal native/PPE concept pairing differs",
        )
    vector = [measured[name][1] for name in TAXA] if not missing else None
    return {
        "measured": measured,
        "missing": missing,
        "vector": vector,
        "all_nisp": sum(v[1] for v in measured.values()),
        "panel_subtotal": sum(measured.get(name, (0, 0))[1] for name in TAXA),
        "nonpollen_rows": excluded,
    }


def source_age(sample: dict[str, Any]) -> dict[str, Any] | None:
    """Use only the named finite source point age; no interpolation or clipping."""
    ages: list[dict[str, Any]] = [
        age for age in sample["ages"] if age.get("chronologyid") == 11516
    ]
    if len(ages) != 1 or ages[0].get("agetype") != "Calibrated radiocarbon years BP":
        return None
    value = ages[0].get("age")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return None
    return ages[0]


def panel_inputs(sources: dict[str, Any]) -> dict[str, Any]:
    """Account for all 107 source samples and exactly 29 declared window samples."""
    unit = sources["site"]["collectionunit"]
    samples = unit["dataset"]["samples"]
    require(
        len(samples) == len({s["sampleid"] for s in samples}) == 107,
        "Native sample identity population differs",
    )
    chronology = [
        c for c in unit["chronologies"] if c["chronology"]["chronologyid"] == 11516
    ]
    require(
        len(chronology) == 1
        and chronology[0]["chronology"]["chronology"]["modelagetype"]
        == "Calibrated radiocarbon years BP",
        "Named source chronology differs",
    )
    rows: list[dict[str, Any]] = []
    grouped: dict[int, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = {
        window: [] for window in WINDOWS
    }
    common = set(sources["parameter_labels"])
    for sample in sorted(samples, key=lambda s: s["sampleid"]):
        count, age = native_counts(sample), source_age(sample)
        value = None if age is None else age["age"]
        window = (
            None
            if value is None
            else next((b for b in WINDOWS if 500 * b <= value < 500 * (b + 1)), None)
        )
        status = (
            "refused_named_source_age"
            if age is None
            else "outside_requested_windows"
            if window is None
            else "refused_missing_explicit_panel"
            if count["missing"]
            else "refused_zero_panel"
            if sum(count["vector"]) == 0
            else "selected_complete_panel"
        )
        row = {
            "sample_id": sample["sampleid"],
            "depth_native": sample["depth"],
            "depth_unit": "native_depth_unit_not_explicit_in_payload",
            "source_age_bp": value,
            "chronology_id": None if age is None else 11516,
            "source_age_type": None if age is None else age["agetype"],
            "assumed_age_reference_year_ce": None if age is None else 1950,
            "raw_age_bounds": None
            if age is None
            else {"younger": age.get("ageyounger"), "older": age.get("ageolder")},
            "status": status,
            "window_id": window,
            "panel_missing_taxa": count["missing"],
            "panel_count_total": None
            if count["vector"] is None
            else sum(count["vector"]),
            "reported_panel_subtotal": count["panel_subtotal"],
            "all_reported_pollen_nisp": count["all_nisp"],
            "omitted_reported_pollen_nisp": count["all_nisp"] - count["panel_subtotal"],
            "excluded_nonpollen_rows": count["nonpollen_rows"],
        }
        rows.append(row)
        if status == "selected_complete_panel":
            assert window is not None
            common.intersection_update(count["measured"])
            grouped[window].append((sample, count, row))
    require(common == set(TAXA), "Declared maximal common literal panel differs")
    require(
        [len(grouped[b]) for b in WINDOWS] == [7, 9, 8, 5],
        "Frozen source window population differs",
    )
    windows = []
    selected_ids: set[int] = set()
    for b, members in grouped.items():
        ids = [s["sampleid"] for s, _, _ in members]
        require(
            not selected_ids.intersection(ids),
            "Raw sample overlap invalidates independent count groups",
        )
        selected_ids.update(ids)
        counts = [sum(c["vector"][j] for _, c, _ in members) for j in range(len(TAXA))]
        require(
            0 < sum(counts) < 2**53, "Pooled count population outside exact API range"
        )
        support = [
            {
                "sample_id": s["sampleid"],
                "datum": s["datum"],
                "ages": s["ages"],
                "depth": s["depth"],
            }
            for s, _, _ in members
        ]
        windows.append(
            {
                "window_id": b,
                "edges_cal_bp": [500 * b, 500 * (b + 1)],
                "sample_ids": ids,
                "native_sample_support_sha256": hashlib.sha256(
                    json.dumps(
                        support,
                        sort_keys=True,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode()
                ).hexdigest(),
                "pooled_panel_counts": counts,
                "panel_count_total": sum(counts),
                "all_reported_pollen_nisp": sum(
                    r["all_reported_pollen_nisp"] for _, _, r in members
                ),
                "omitted_reported_pollen_nisp": sum(
                    r["omitted_reported_pollen_nisp"] for _, _, r in members
                ),
            }
        )
    require(len(selected_ids) == 29, "Selected sample denominator differs")
    return {**sources, "sample_account": rows, "windows": windows}
