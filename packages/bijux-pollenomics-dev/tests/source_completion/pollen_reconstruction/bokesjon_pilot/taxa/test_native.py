"""Literal source observations and conditional nondetection stay separate."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest


def datum(label: str, taxon_id: int, value: Any) -> dict[str, Any]:
    return {
        "taxonid": taxon_id,
        "variablename": label,
        "value": value,
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "context": None,
    }


def source() -> dict[str, Any]:
    samples = []
    for sid, age, rows in [
        (1, 2700, [datum("Betula", 29, 10), datum("Poaceae", 25, 0)]),
        (2, 3199, [datum("Betula", 29, 20)]),
        (3, 3200, [datum("Secale", 300, 2), datum("Poaceae", 25, 5)]),
    ]:
        samples.append(
            {
                "sampleid": sid,
                "depth": sid * 10,
                "analysisunitid": sid + 100,
                "thickness": None,
                "datum": rows,
                "ages": [
                    {
                        "chronologyid": 7,
                        "agetype": "Calibrated radiocarbon years BP",
                        "chronologyname": "selected",
                        "age": age,
                        "ageolder": None,
                        "ageyounger": None,
                    }
                ],
            }
        )
    return {
        "rows": [
            {
                "site": {
                    "siteid": 20,
                    "dataset": {"datasetid": 10},
                    "collectionunit": {
                        "collectionunitid": 30,
                        "handle": "example",
                        "dataset": {"datasetid": 10, "samples": samples},
                    },
                }
            }
        ]
    }


def audit(raw: dict[str, Any]) -> dict[str, Any]:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        audit_native_window,
    )

    return audit_native_window(
        raw, dataset_id=10, collection_unit_id=30, chronology_id=7, window=(2700, 3200)
    )


def test_literal_zero_and_omitted_dataset_taxon_are_not_conflated() -> None:
    result = audit(source())
    assert result["selected_sample_ids"] == [1, 2]
    assert result["window_native_pollen_N"] == 30
    assert result["source_sample_count"] == 3
    taxa = {r["native_label"]: r for r in result["taxon_axis"]}
    assert taxa["Betula"]["known_NISP_sum"] == 30
    assert taxa["Poaceae"]["cells"][0]["state"] == "reported_zero"
    assert (
        taxa["Poaceae"]["cells"][1]["state"]
        == "omitted_known_dataset_taxon_conditional_nondetection"
    )
    assert taxa["Poaceae"]["aggregate_all_owner_count"] is None
    assert all(c["count"] is None for c in taxa["Secale"]["cells"])
    assert all(
        c["state"] == "omitted_known_dataset_taxon_conditional_nondetection"
        for c in taxa["Secale"]["cells"]
    )
    assert result["zero_imputation_applied"] is False
    assert result["qualified_terrestrial_denominator"] is False


@pytest.mark.parametrize("bad", [None, 1.5, "1", True, -1])
def test_invalid_reported_counts_suppress_native_denominator(bad: Any) -> None:
    raw = source()
    raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"][0][
        "value"
    ] = bad
    result = audit(raw)
    assert result["window_native_pollen_N"] is None
    assert (
        result["samples"][0]["pollen_denominator_status"]
        == "refused_invalid_or_duplicate_pollen_rows"
    )


def test_duplicate_rows_are_not_summed_to_make_a_complete_axis() -> None:
    raw = source()
    rows = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"]
    rows.append(deepcopy(rows[0]))
    result = audit(raw)
    assert result["window_native_pollen_N"] is None
    taxon = next(t for t in result["taxon_axis"] if t["native_label"] == "Betula")
    assert taxon["cells"][0]["state"] == "duplicate_or_conflicting_identity"


def test_unknown_age_owner_cannot_silently_leave_window_population() -> None:
    raw = source()
    raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][2]["ages"] = []
    result = audit(raw)
    assert result["unassignable_age_sample_ids"] == [3]
    assert result["window_native_pollen_N"] is None
    assert result["known_window_native_pollen_N"] == 30


def test_wrong_units_prevent_omission_from_becoming_a_zero_candidate() -> None:
    raw = source()
    row = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][2]["datum"][0]
    row["units"] = "percent"
    result = audit(raw)
    taxon = next(t for t in result["taxon_axis"] if t["native_label"] == "Secale")
    assert taxon["conditional_nondetection_eligible"] is False
    assert all(
        c["state"] == "omitted_incompatible_dataset_taxon" for c in taxon["cells"]
    )


def test_outside_duplicate_does_not_qualify_a_conditional_nondetection() -> None:
    raw = source()
    rows = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][2]["datum"]
    rows.append(deepcopy(rows[0]))
    taxon = next(t for t in audit(raw)["taxon_axis"] if t["native_label"] == "Secale")
    assert taxon["conditional_nondetection_eligible"] is False


@pytest.mark.parametrize(
    "kind,want",
    [
        ("missing", "missing_native_value"),
        ("null", "null_native_value"),
        ("fractional", "invalid_native_count"),
    ],
)
def test_reported_value_failures_keep_their_native_states(kind: str, want: str) -> None:
    raw = source()
    row = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][0]["datum"][0]
    if kind == "missing":
        del row["value"]
    else:
        row["value"] = None if kind == "null" else 0.5
    taxon = next(t for t in audit(raw)["taxon_axis"] if t["native_label"] == "Betula")
    assert taxon["cells"][0]["state"] == want


def test_zero_only_dataset_axis_does_not_qualify_omission_as_nondetection() -> None:
    raw = source()
    outside = raw["rows"][0]["site"]["collectionunit"]["dataset"]["samples"][2]
    outside["datum"] = [d for d in outside["datum"] if d["variablename"] != "Poaceae"]
    taxon = next(t for t in audit(raw)["taxon_axis"] if t["native_label"] == "Poaceae")
    assert taxon["conditional_nondetection_eligible"] is False
    assert taxon["cells"][0]["state"] == "reported_zero"
    assert taxon["cells"][0]["count"] == 0
    assert taxon["cells"][1]["state"] == "omitted_incompatible_dataset_taxon"
    assert taxon["cells"][1]["count"] is None
