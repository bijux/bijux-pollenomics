"""Native panel identity and held-place sample-support controls."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.inputs import (
    predictor_inputs,
    prepare_inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.sources import (
    PROTOCOL,
    named_chronology,
)

REPOSITORY = Path(__file__).resolve().parents[6]


def controlled_inputs() -> dict[str, Any]:
    """Use frozen identity shapes with invented counts, never native outcomes."""
    protocol = json.loads((REPOSITORY / PROTOCOL).read_bytes())
    cores = {}
    for declared in protocol["cores"]:
        ages = {
            number: protocol["window_edges_native_bp"][i]
            for i, group in enumerate(declared["expected_window_sample_ids"])
            for number in group
        }
        samples = []
        ids = list(ages) + [
            100000000 + declared["dataset_id"] * 100 + i
            for i in range(declared["native_samples"] - len(ages))
        ]
        for number in ids:
            data = [
                {
                    "element": "pollen",
                    "elementtype": "pollen",
                    "units": "NISP",
                    "variablename": name,
                    "taxonid": {"Betula": 29, "Ulmus": 310}.get(name, 1000 + i),
                    "value": i + 1,
                }
                for i, name in enumerate(declared["source_axis"])
            ]
            samples.append(
                {
                    "sampleid": number,
                    "analysisunitid": number + 1,
                    "depth": number / 1000,
                    "ages": [
                        {
                            "age": ages.get(number, -5),
                            "chronologyid": declared["chronology_id"],
                            "agetype": "Calibrated radiocarbon years BP",
                            "ageyounger": None,
                            "ageolder": None,
                        }
                    ],
                    "datum": data,
                }
            )
        cores[declared["dataset_id"]] = {
            "declaration": declared,
            "site": {"collectionunit": {"dataset": {"samples": samples}}},
        }
    return {
        "protocol": protocol,
        "cores": cores,
        "ppe": [2.0, 1.0],
        "fall": [0.02, 0.03],
        "input_sha256": {},
        "attribution": [],
        "policy_urls": [],
    }


def test_native_sample_accounts_keep_signed_ages_and_excluded_mass() -> None:
    prepared = prepare_inputs(controlled_inputs())
    assert len(prepared["sample_accounts"]) == 147
    selected = [
        r
        for r in prepared["sample_accounts"]
        if r["status"] == "selected_frozen_subset"
    ]
    assert len(selected) == 59 and len(prepared["cells"]) == 18
    assert any(r["source_age_native_bp"] == -5 for r in prepared["sample_accounts"])
    assert all(
        r["source_panel_N"] == r["projected_panel_N"] + r["excluded_panel_N"]
        for r in selected
    )
    assert all(r["projected_datum_rows"][0]["taxon_id"] == 29 for r in selected)


def test_same_label_different_id_cannot_pool_into_projected_ppe() -> None:
    loaded = controlled_inputs()
    raw = next(iter(loaded["cores"].values()))["site"]["collectionunit"]["dataset"][
        "samples"
    ][0]
    raw["datum"].append({**raw["datum"][0], "taxonid": 999})
    with pytest.raises(ValueError, match="label/native ID"):
        prepare_inputs(loaded)


def test_missing_source_panel_member_refuses_frozen_membership() -> None:
    loaded = controlled_inputs()
    raw = loaded["cores"][54001]["site"]["collectionunit"]["dataset"]["samples"][0]
    raw["datum"] = [d for d in raw["datum"] if d["variablename"] != "Fraxinus"]
    with pytest.raises(ValueError, match="Frozen comparison sample identities"):
        prepare_inputs(loaded)


def test_target_counts_never_cross_predictor_input_boundary() -> None:
    prepared = prepare_inputs(controlled_inputs())
    target, anchors = predictor_inputs(prepared, "BOKE", (2700, 3200))
    changed = copy.deepcopy(prepared)
    changed["cells"]["BOKE", (2700, 3200)]["projected_counts"] = [999, 1]
    assert predictor_inputs(changed, "BOKE", (2700, 3200)) == (target, anchors)
    assert not hasattr(target, "counts")
    assert {a.site_id for a in anchors}.isdisjoint({target.site_id})


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "uncalibrated"])
def test_model_identity_is_checked_before_sample_age_selection(corruption: str) -> None:
    model: dict[str, Any] = {
        "chronologyid": 10,
        "chronology": {"modelagetype": "Calibrated radiocarbon years BP"},
    }
    unit = {"chronologies": [{"chronology": model}]}
    assert named_chronology(unit, 10) == model
    if corruption == "missing":
        model["chronologyid"] = 11
    elif corruption == "duplicate":
        unit["chronologies"].append({"chronology": copy.deepcopy(model)})
    else:
        model["chronology"]["modelagetype"] = "Radiocarbon years BP"
    with pytest.raises(ValueError, match="unique calibrated BP source model"):
        named_chronology(unit, 10)
