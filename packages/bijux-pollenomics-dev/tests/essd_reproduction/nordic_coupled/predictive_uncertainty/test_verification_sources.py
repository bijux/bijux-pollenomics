"""Independently certify the reader's observed packet against portable saved sources."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty import (
    inputs,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification import (
    sources,
)

from .test_inputs import saved_inputs


@pytest.fixture(scope="module")
def saved_packet(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, Any]]:
    root = tmp_path_factory.mktemp("source-binding")
    protocol = saved_inputs(root)
    # The maintained reader is the object under examination, never the oracle.
    packet: dict[str, Any] = json.loads(
        json.dumps(asdict(inputs.load_inputs(root, protocol)))
    )
    packet["protocol"] = protocol
    return root, packet


@pytest.fixture
def observed(saved_packet: tuple[Path, dict[str, Any]]) -> tuple[Path, dict[str, Any]]:
    return saved_packet[0], deepcopy(saved_packet[1])


def test_reader_packet_is_bound_to_raw_sources_and_saved_native_coefficients(
    observed: tuple[Path, dict[str, Any]],
) -> None:
    root, packet = observed
    result = sources.bind_sources(root, packet)
    assert result["status"] == "passed"
    assert result["owners_verified"] == 24
    assert result["active_fold_kernels_verified"] == 3
    assert result["nominal_predictions_verified"] == 9
    assert result["source_files_verified"] == len(packet["source_files"])


@pytest.mark.parametrize(
    "defect",
    [
        "counts",
        "self_consistent_wrong_N",
        "raw_owner",
        "projection_owner",
        "kernel",
        "kernel_ref",
        "target_geometry",
        "parameters",
        "forward",
        "distance",
        "nominal",
        "dispositions",
        "missing_source",
        "extra_source",
    ],
)
def test_authentic_bytes_do_not_certify_wrong_reader_meaning(
    observed: tuple[Path, dict[str, Any]], defect: str
) -> None:
    root, packet = observed
    case = packet["cases"][0]
    target = case["target_id"]
    owner = next(row for row in packet["owners"] if row["owner_id"] == target)
    fold = next(row for row in packet["folds"] if row["case_id"] == case["case_id"])
    lineage = packet["accounting"]["owner_lineage"]
    if defect == "counts":
        owner["counts"] = [9, 1]
    elif defect == "self_consistent_wrong_N":
        owner["counts"] = [8, 3]
        lineage[target]["panel_N"] = 11
        lineage[target]["projection"]["projected_panel_N"] = 11
    elif defect == "raw_owner":
        lineage[target]["raw"] = lineage[case["regional_owner_id"]]["raw"]
    elif defect == "projection_owner":
        inactive = next(
            value
            for value in lineage.values()
            if value["core"] == "BOKE" and "cal-bp-3200-3700" in value["raw"]["path"]
        )
        foreign = next(
            value
            for value in lineage.values()
            if value["core"] == "BUS" and "cal-bp-3200-3700" in value["raw"]["path"]
        )
        inactive["core"], inactive["projection"] = (
            foreign["core"],
            foreign["projection"],
        )
    elif defect == "kernel":
        case["local_owners"][0]["local_k"] = [[0.21, 0.3], [0.2, 0.3]]
    elif defect == "kernel_ref":
        fold["kernel_refs"][0]["local_owner_id"] = target
    elif defect == "target_geometry":
        fold["target_geometry_ref"] = fold["parameter_ref"]
    elif defect == "parameters":
        fold["parameter_ref"] = fold["target_geometry_ref"]
    elif defect == "forward":
        case["forward_regional_k"] = [0.4, 0.3]
    elif defect == "distance":
        case["distances_km"] = list(reversed(case["distances_km"]))
    elif defect == "nominal":
        packet["nominal_predictions"][0]["prediction_manifest_sha256"] = "d" * 64
    elif defect == "dispositions":
        packet["dispositions"][-1]["status"] = "predicted"
    elif defect == "missing_source":
        packet["source_files"].pop()
    else:
        path = root / "unowned.json"
        body = b'{"not":"a declared scientific source"}'
        path.write_bytes(body)
        packet["source_files"].append(
            {
                "path": "unowned.json",
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
        )
    with pytest.raises(ValueError):
        sources.bind_sources(root, packet)


@pytest.mark.parametrize("defect", ["changed", "symlink", "escape"])
def test_source_identity_and_ordinary_repository_ownership_are_required(
    observed: tuple[Path, dict[str, Any]], defect: str
) -> None:
    root, packet = observed
    proof = next(iter(packet["accounting"]["owner_lineage"].values()))["raw"]
    path = root / proof["path"]
    original = path.read_bytes()
    if defect == "changed":
        path.write_bytes(path.read_bytes() + b" ")
    elif defect == "symlink":
        copy = root / "alias-target.json"
        copy.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(copy)
    else:
        proof["path"] = "../outside.json"
    try:
        with pytest.raises(ValueError):
            sources.bind_sources(root, packet)
    finally:
        if path.is_symlink():
            path.unlink()
        path.write_bytes(original)


@pytest.mark.parametrize(
    "raw",
    [
        b"index,Ulmus,Betula\n1,1,2\n2,1,2\n",
        b"index,Betula,Ulmus\n2,1,2\n1,1,2\n",
        b"index,Betula,Ulmus\n1,nan,2\n2,1,2\n",
    ],
)
def test_inner_csv_axis_ring_order_and_finiteness_have_independent_controls(
    raw: bytes,
) -> None:
    with pytest.raises(ValueError):
        sources._matrix(raw, [{"mean_m": 1.0}, {"mean_m": 2.0}])
