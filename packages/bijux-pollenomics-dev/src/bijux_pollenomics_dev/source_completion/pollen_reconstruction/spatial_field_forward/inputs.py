"""Freeze native sample/panel support separately from held-place prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..swedish_static_basin.sources import explicit_panel, pollen_counts, selected_age
from .sources import AXIS, require


@dataclass(frozen=True)
class TargetGeometry:
    """A predictor target carries identities and geometry, never observed counts."""

    core: str
    site_id: int
    dataset_id: int
    collection_unit_id: int
    centre_lon_lat: tuple[float, float]
    radius_m: float
    window: tuple[int, int]
    sample_ids: tuple[int, ...]


@dataclass(frozen=True)
class SourcePanel:
    """One other physical place's fixed projected training observations."""

    core: str
    site_id: int
    dataset_id: int
    collection_unit_id: int
    centre_lon_lat: tuple[float, float]
    radius_m: float
    window: tuple[int, int]
    sample_ids: tuple[int, ...]
    counts: tuple[int, int]


def prepare_inputs(loaded: dict[str, Any]) -> dict[str, Any]:
    """Keep every source sample and inherited completeness decision explicit."""
    edges = loaded["protocol"]["window_edges_native_bp"]
    windows = list(zip(edges[:-1], edges[1:], strict=True))
    accounts, cells = [], {}
    for source in loaded["cores"].values():
        declared, site = source["declaration"], source["site"]
        dataset = site["collectionunit"]["dataset"]
        raw_samples = dataset["samples"]
        require(
            len(raw_samples)
            == len({s["sampleid"] for s in raw_samples})
            == declared["native_samples"],
            "Native sample population differs",
        )
        grouped: dict[tuple[int, int], list[dict[str, Any]]] = {w: [] for w in windows}
        for raw in sorted(raw_samples, key=lambda r: r["sampleid"]):
            parsed = pollen_counts(raw)
            native_pairings = dict(
                zip(AXIS, loaded["protocol"]["native_taxon_ids"], strict=True)
            )
            require(
                all(
                    row["name"] not in native_pairings
                    or row["taxon_id"] == native_pairings[row["name"]]
                    for row in parsed["datum_rows"]
                ),
                "Projected taxon label/native ID pairing differs",
            )
            age, age_reason = selected_age(parsed, declared["chronology_id"])
            point = None if age is None else age["age"]
            window = next(
                (w for w in windows if point is not None and w[0] <= point < w[1]), None
            )
            inherited, panel_reason = explicit_panel(parsed, declared["source_axis"])
            projected, projected_reason = explicit_panel(parsed, list(AXIS))
            status = (
                "refused_named_age"
                if age_reason
                else "outside_requested_windows"
                if window is None
                else "refused_inherited_source_panel"
                if panel_reason
                else "refused_projected_panel"
                if projected_reason
                else "selected_frozen_subset"
            )
            account = {
                "core": declared["id"],
                "site_id": declared["site_id"],
                "dataset_id": declared["dataset_id"],
                "collection_unit_id": declared["collection_unit_id"],
                "sample_id": raw["sampleid"],
                "depth_native": raw["depth"],
                "source_age_native_bp": point,
                "chronology_id": declared["chronology_id"],
                "raw_age_bounds": None
                if age is None
                else {"younger": age.get("ageyounger"), "older": age.get("ageolder")},
                "window": window,
                "status": status,
                "source_axis": declared["source_axis"],
                "projected_axis": list(AXIS),
                "source_panel_N": None if inherited is None else sum(inherited),
                "projected_panel_N": None if projected is None else sum(projected),
                "excluded_panel_N": None
                if inherited is None or projected is None
                else sum(inherited) - sum(projected),
                "all_reported_pollen_NISP": parsed["reported_all_pollen_NISP_sum"],
                "outside_source_axis_N": None
                if inherited is None
                else parsed["reported_all_pollen_NISP_sum"] - sum(inherited),
                "missing_source_taxa": [
                    n for n in declared["source_axis"] if n not in parsed["counts"]
                ],
                "missing_projected_taxa": [
                    n for n in AXIS if n not in parsed["counts"]
                ],
            }
            account["projected_datum_rows"] = [
                row for row in parsed["datum_rows"] if row["name"] in AXIS
            ]
            accounts.append(account)
            if status == "selected_frozen_subset":
                assert (
                    window is not None
                    and inherited is not None
                    and projected is not None
                )
                grouped[window].append(
                    {"account": account, "inherited": inherited, "projected": projected}
                )
        for window, expected in zip(
            windows, declared["expected_window_sample_ids"], strict=True
        ):
            members = grouped[window]
            ids = [m["account"]["sample_id"] for m in members]
            require(ids == expected, "Frozen comparison sample identities differ")
            cells[declared["id"], window] = {
                "core": declared["id"],
                "site_id": declared["site_id"],
                "dataset_id": declared["dataset_id"],
                "collection_unit_id": declared["collection_unit_id"],
                "window": window,
                "sample_ids": ids,
                "source_axis": declared["source_axis"],
                "source_panel_counts": [
                    sum(m["inherited"][i] for m in members)
                    for i in range(len(declared["source_axis"]))
                ],
                "projected_axis": list(AXIS),
                "projected_counts": [
                    sum(m["projected"][i] for m in members) for i in range(2)
                ],
                "source_panel_N": sum(m["account"]["source_panel_N"] for m in members),
                "projected_panel_N": sum(
                    m["account"]["projected_panel_N"] for m in members
                ),
                "excluded_panel_N": sum(
                    m["account"]["excluded_panel_N"] for m in members
                ),
                "all_reported_pollen_NISP": sum(
                    m["account"]["all_reported_pollen_NISP"] for m in members
                ),
                "outside_source_axis_N": sum(
                    m["account"]["outside_source_axis_N"] for m in members
                ),
            }
    require(
        len(accounts) == 147
        and sum(r["status"] == "selected_frozen_subset" for r in accounts) == 59
        and len(cells) == 18,
        "Declared sample/context population differs",
    )
    return {**loaded, "sample_accounts": accounts, "cells": cells, "windows": windows}


def predictor_inputs(
    prepared: dict[str, Any], core_id: str, window: tuple[int, int]
) -> tuple[TargetGeometry, tuple[SourcePanel, SourcePanel]]:
    """Keep the matching target outcome out of the complete callable boundary."""
    declarations = {c["id"]: c for c in prepared["protocol"]["cores"]}
    own = declarations[core_id]
    cell = prepared["cells"][core_id, window]
    target = TargetGeometry(
        core_id,
        own["site_id"],
        own["dataset_id"],
        own["collection_unit_id"],
        tuple(own["analysis_centre_lon_lat"]),
        own["radius_m"],
        window,
        tuple(cell["sample_ids"]),
    )
    anchors = []
    for name in sorted(declarations):
        declared = declarations[name]
        if declared["site_id"] == target.site_id:
            continue
        cell = prepared["cells"][name, window]
        anchors.append(
            SourcePanel(
                name,
                declared["site_id"],
                declared["dataset_id"],
                declared["collection_unit_id"],
                tuple(declared["analysis_centre_lon_lat"]),
                declared["radius_m"],
                window,
                tuple(cell["sample_ids"]),
                tuple(cell["projected_counts"]),
            )
        )
    require(
        len(anchors) == 2 and len({a.site_id for a in anchors}) == 2,
        "Exactly two other physical places required",
    )
    return target, (anchors[0], anchors[1])
