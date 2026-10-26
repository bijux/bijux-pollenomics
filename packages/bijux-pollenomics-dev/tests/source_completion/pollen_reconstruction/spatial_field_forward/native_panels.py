"""Original native sample eligibility and integer panel pooling without adapters."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

from .sources import AXIS, WINDOWS


def native_counts(raw: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    seen: set[tuple[int, str]] = set()
    concepts = {"Betula": 29, "Ulmus": 310}
    for datum in raw["datum"]:
        if (datum.get("element"), datum.get("elementtype")) != ("pollen", "pollen"):
            continue
        assert datum["units"] == "NISP"
        name, taxon, value = datum["variablename"], datum["taxonid"], datum["value"]
        assert isinstance(name, str) and name and type(taxon) is int
        assert type(value) in (int, float) and math.isfinite(value)
        exact = Fraction(value)
        assert exact.denominator == 1 and exact >= 0
        assert (taxon, name) not in seen
        seen.add((taxon, name))
        if name in concepts:
            assert taxon == concepts[name]
        # Alternate native IDs cannot silently merge into one literal name.
        assert name not in counts
        counts[name] = exact.numerator
    return counts


def core_panels(
    spec: dict[str, Any], site: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[tuple[int, int], dict[str, Any]]]:
    samples = site["collectionunit"]["dataset"]["samples"]
    assert (
        len(samples)
        == len({sample["sampleid"] for sample in samples})
        == spec["native_samples"]
    )
    accounts = []
    selected: dict[tuple[int, int], list[tuple[dict[str, Any], dict[str, int]]]] = {
        window: [] for window in WINDOWS
    }
    for raw in sorted(samples, key=lambda sample: sample["sampleid"]):
        counts = native_counts(raw)
        candidates = [
            age
            for age in raw["ages"]
            if age.get("chronologyid") == spec["chronology_id"]
        ]
        age = candidates[0] if len(candidates) == 1 else None
        point = None if age is None else age.get("age")
        if age is not None and (
            age.get("agetype") != "Calibrated radiocarbon years BP"
            or point is None
            or type(point) not in (int, float)
            or not math.isfinite(point)
        ):
            age, point = None, None
        window = next(
            (w for w in WINDOWS if point is not None and w[0] <= point < w[1]), None
        )
        inherited = (
            [counts[name] for name in spec["source_axis"]]
            if all(name in counts for name in spec["source_axis"])
            else None
        )
        projected = (
            [counts[name] for name in AXIS]
            if all(name in counts for name in AXIS)
            else None
        )
        inherited = inherited if inherited and sum(inherited) > 0 else None
        projected = projected if projected and sum(projected) > 0 else None
        status = (
            "refused_named_age"
            if age is None
            else "outside_requested_windows"
            if window is None
            else "refused_inherited_source_panel"
            if inherited is None
            else "refused_projected_panel"
            if projected is None
            else "selected_frozen_subset"
        )
        account = {
            "core": spec["id"],
            "site_id": spec["site_id"],
            "dataset_id": spec["dataset_id"],
            "collection_unit_id": spec["collection_unit_id"],
            "sample_id": raw["sampleid"],
            "depth_native": raw["depth"],
            "source_age_native_bp": point,
            "chronology_id": spec["chronology_id"],
            "raw_age_bounds": None
            if age is None
            else {"younger": age.get("ageyounger"), "older": age.get("ageolder")},
            "window": window,
            "status": status,
            "source_axis": spec["source_axis"],
            "projected_axis": list(AXIS),
            "source_panel_N": None if inherited is None else sum(inherited),
            "projected_panel_N": None if projected is None else sum(projected),
            "excluded_panel_N": None
            if inherited is None or projected is None
            else sum(inherited) - sum(projected),
            "all_reported_pollen_NISP": sum(counts.values()),
            "outside_source_axis_N": None
            if inherited is None
            else sum(counts.values()) - sum(inherited),
            "missing_source_taxa": [
                name for name in spec["source_axis"] if name not in counts
            ],
            "missing_projected_taxa": [name for name in AXIS if name not in counts],
        }
        account["projected_datum_rows"] = [
            {
                "ordinal": index,
                "taxon_id": datum["taxonid"],
                "name": datum["variablename"],
                "count": int(datum["value"]),
            }
            for index, datum in enumerate(raw["datum"])
            if (datum.get("element"), datum.get("elementtype")) == ("pollen", "pollen")
            and datum["variablename"] in AXIS
        ]
        accounts.append(account)
        if status == "selected_frozen_subset":
            assert window is not None
            selected[window].append((account, counts))
    panels = {}
    for window, expected in zip(
        WINDOWS, spec["expected_window_sample_ids"], strict=True
    ):
        group = selected[window]
        assert [account["sample_id"] for account, _ in group] == expected
        pooled = [
            sum(counts[name] for _, counts in group) for name in spec["source_axis"]
        ]
        projected = [sum(counts[name] for _, counts in group) for name in AXIS]
        panels[window] = {
            "core": spec["id"],
            "site_id": spec["site_id"],
            "dataset_id": spec["dataset_id"],
            "collection_unit_id": spec["collection_unit_id"],
            "window": window,
            "sample_ids": expected,
            "source_axis": spec["source_axis"],
            "source_panel_counts": pooled,
            "projected_axis": list(AXIS),
            "projected_counts": projected,
            "source_panel_N": sum(pooled),
            "projected_panel_N": sum(projected),
            "excluded_panel_N": sum(pooled) - sum(projected),
            "all_reported_pollen_NISP": sum(
                account["all_reported_pollen_NISP"] for account, _ in group
            ),
            "outside_source_axis_N": sum(
                account["outside_source_axis_N"] for account, _ in group
            ),
        }
    return accounts, panels
