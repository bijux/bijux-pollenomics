"""Artificial cohort extension preserves old sources and exercises train-only readers."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import inputs, workflow
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.cohorts import flink_nordic

from ..test_inputs import fixture as source_fixture


def fixture(tmp_path: Path) -> tuple[dict[str, bytes], dict[str, Any], dict[str, Any]]:
    """Construct full miniature membership without reading a saved scientific product."""
    cores, old_protocol = source_fixture()
    nominal = tmp_path / "nominal"
    inputs.project(cores, old_protocol, nominal)
    (nominal / "source-pins.json").write_text("[]\n")
    buffers = {
        p.relative_to(nominal).as_posix(): p.read_bytes()
        for p in nominal.rglob("*.json")
    }
    samples: list[dict[str, Any]] = [
        {
            "sample_id": i,
            "window": None,
            "panel_complete": True,
            "nonnegative_age": True,
        }
        for i in range(1, 110)
    ]
    windows: list[dict[str, Any]] = []
    for i, window in enumerate(inputs.WINDOWS):
        samples[i]["window"] = list(window)
        windows.append(
            {
                "window_cal_bp_half_open": list(window),
                "status": "projected",
                "sample_ids": [i + 1],
                "panel_counts": [6, 4],
                "panel_N": 10,
                "pollen_N": 13,
                "excluded_pollen_N": 3,
                "support_sha256": "1" * 64,
            }
        )
    # Unselected missing and negative rows remain documented, never zero-filled.
    samples[-1]["panel_complete"] = False
    samples[-2]["nonnegative_age"] = False
    projection = {
        "schema_version": "flink-native-panel-results.v1",
        "identity": dict(flink_nordic.IDENTITY),
        "axis": [
            {"label": "Betula", "taxon_id": 29},
            {"label": "Ulmus", "taxon_id": 310},
        ],
        "sample_count": 109,
        "engine_calls": 0,
        "samples": samples,
        "windows": windows,
        "chronology": {"default_chronology_id": 38438},
        "scope": "Artificial native-source projection only",
    }
    protocol = {
        "schema_version": flink_nordic.SCHEMA,
        "baseline_protocol_sha256": workflow.PROTOCOL_SHA256,
        "model_assumptions": deepcopy(flink_nordic.ASSUMPTIONS),
        "scope": "Artificial conditional development, no historical or field admission",
    }
    return buffers, projection, protocol


def test_complete_cohort_preserves80_and_admits24folds_without_engine(
    tmp_path: Path,
) -> None:
    nominal, projection, protocol = fixture(tmp_path)
    snapshot = deepcopy((projection, protocol))
    buffers = flink_nordic.extend(nominal, projection, protocol)
    assert len(buffers) == 117
    assert all(buffers[name] == raw for name, raw in nominal.items())
    assert (projection, protocol) == snapshot
    output = tmp_path / "cohort"
    for name, raw in buffers.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    assert flink_nordic.admit(output) == {
        "geometry_reads": 24,
        "outer_folds": 24,
        "training_pair_requests": 48,
        "engine_calls": 0,
    }
    prefix = workflow.NAMES[0] + "/"
    payload = json.loads(buffers[prefix + "cohort-experiment.json"])
    assert len(payload["sites"]) == 4
    assert payload["regional_priority"][0].startswith("neotoma-4446-")
    assert payload["regional_priority"][-1].startswith("neotoma-54024-")
    original = json.loads(nominal[prefix + "experiment.json"])
    assert payload["sites"][:3] == original["sites"]
    assert (
        payload["request_template"]["configuration"]
        == original["request_template"]["configuration"]
    )
    geometry = json.loads(buffers[prefix + "FLINK-geometry.json"])
    assert geometry["basin"] == {"diameter_m": 196, "site_type": "lake"}
    assert geometry["inversion_rings"][0]["inner_m"] == 99
    assert geometry["forward_rings"][0]["inner_m"] == 98
    assert [geometry[k] for k in ("longitude", "latitude")] == [13.24333, 56.25444]
    copied = json.loads(buffers[prefix + "cohort-projection.json"])
    assert copied["flink_source_window"] == projection["windows"][0]
    assert copied["native_sample_ids"] == [1]


@pytest.mark.parametrize(
    "change",
    [
        "axis",
        "identity",
        "missing_window",
        "duplicate_window",
        "refused",
        "missing_count",
        "bool_count",
        "zero_panel",
        "denominator",
        "duplicate_sample",
        "foreign_sample",
        "missing_taxon",
        "membership",
        "protocol",
        "nominal_place",
        "parameter",
        "support",
    ],
)
def test_refuses_incomplete_or_foreign_membership(tmp_path: Path, change: str) -> None:
    nominal, projection, protocol = fixture(tmp_path)
    row = projection["windows"][0]
    if change == "axis":
        projection["axis"].reverse()
    elif change == "identity":
        projection["identity"]["site_id"] = 123
    elif change == "missing_window":
        projection["windows"].pop()
    elif change == "duplicate_window":
        projection["windows"][1] = deepcopy(row)
    elif change == "refused":
        row["status"] = "refused_missing_literal_taxon"
    elif change == "missing_count":
        row["panel_counts"][0] = None
    elif change == "bool_count":
        row["panel_counts"][0] = True
    elif change == "zero_panel":
        row.update(panel_counts=[0, 0], panel_N=0)
    elif change == "denominator":
        row["pollen_N"] = 12
    elif change == "duplicate_sample":
        row["sample_ids"] = [1, 1]
    elif change == "foreign_sample":
        row["sample_ids"] = [999]
    elif change == "missing_taxon":
        projection["samples"][0]["panel_complete"] = False
    elif change == "membership":
        projection["samples"][0]["window"] = None
    elif change == "protocol":
        protocol["model_assumptions"]["radius_m"] = 99
    elif change in {"nominal_place", "parameter"}:
        name = workflow.NAMES[0] + "/experiment.json"
        value = json.loads(nominal[name])
        if change == "nominal_place":
            value["sites"][0]["site_id"] = "neotoma-site-28889"
        else:
            value["request_template"]["parameters"][0]["ppe"] = 9
        nominal[name] = json.dumps(value).encode()
    else:
        row["support_sha256"] = "unknown"
    with pytest.raises(ValueError):
        flink_nordic.extend(nominal, projection, protocol)
