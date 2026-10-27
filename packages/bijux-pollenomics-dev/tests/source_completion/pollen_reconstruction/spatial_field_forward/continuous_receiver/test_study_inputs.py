"""Fake public packets exercise ownership, exact capture and source receipts."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    study_inputs as inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    DYADIC_RADIAL,
)


def packets() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    original = {
        "schema_version": "spatial-field-forward-protocol.v1",
        "projected_axis": list(inputs.AXIS),
        "cores": [
            {"id": core, "radius_m": radius}
            for core, radius in zip(inputs.CORES, (80, 69, 89), strict=True)
        ],
        "physical": {
            "wind_speed_m_s": 3.0,
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "regional_extent_m": 100000.0,
        },
    }
    result: dict[str, Any] = {
        "schema_version": "spatial-field-forward-account.v1",
        "axis": list(inputs.AXIS),
        "fall_speed_m_s": [0.024, 0.032],
        "geometry": [],
    }
    for core, taxon in inputs.OWNERS:
        index = inputs.CORES.index(core)
        result["geometry"].append(
            {
                "core": core,
                "taxon": taxon,
                "anchor_order": [name for name in inputs.CORES if name != core],
                "anchor_xy_m": [[index * 10 + 1.25, -3.5], [index * 10 + 12.5, 4.5]],
                "homogeneous_baseline": {
                    "taxon": taxon,
                    "status": "qualified",
                    "factor": 0.3,
                },
                "primary": {"homogeneous_factor": 0.3, "anchor_factors": [0.1, 0.2]},
            }
        )
    protocol = {
        "schema_version": "continuous-receiver-study.v1",
        "population": {
            "cases": [{"core": core, "taxon": taxon} for core, taxon in inputs.OWNERS],
            "case_count": 6,
            "complete_coefficient_population": 18,
            "coefficients_per_case": ["K", "B1", "B2"],
            "retain_all_case_statuses": True,
        },
        "method": {"rule": SEVEN_NODE_RULE, "partition": DYADIC_RADIAL},
        "input_files": {
            name: {"bytes": 1, "sha256": "0" * 64} for name in inputs.INPUT_PATHS
        },
        "resources": dict(inputs.RESOURCE_LIMITS),
        "numerical_contract": {
            "epsilon_exact": "1/1000000000",
            "saved_point_absolute_error_exact": "1/1000000000",
            "legacy_correspondence_absolute": 1e-9,
            "legacy_correspondence_relative": 1e-8,
            "arithmetic_bits": 96,
            "quadrature_derivative_order": 8,
            "maximum_radial_bands": 11,
        },
    }
    return result, original, protocol


def fake_files(repository: Path) -> Path:
    result, original, protocol = packets()
    for name, payload in zip(inputs.INPUT_PATHS, (result, original), strict=True):
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(payload, allow_nan=False).encode("utf-8")
        path.write_bytes(raw)
        protocol["input_files"][name] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    path = repository / "study-profile.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "name,value",
    [
        ("complete_coefficient_population", 18.0),
        ("coefficients_per_case", ["K", "B2", "B1"]),
        ("retain_all_case_statuses", 1),
    ],
)
def test_population_contract_rejects_coercion_axis_drift_and_status_dropping(
    name: str, value: object
) -> None:
    _, _, protocol = packets()
    protocol["population"][name] = value
    with pytest.raises(ValueError):
        inputs.validate_protocol(protocol)


def test_prefix_is_captured_once_per_taxon_with_exact_dyadics_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result, original, protocol = packets()
    calls: list[tuple[float, ...]] = []

    def prefix(*parameters: float) -> float:
        calls.append(parameters)
        return 0.5

    monkeypatch.setattr(inputs, "gpm_values", prefix)
    selected = inputs.prepare_inputs(result, original, protocol)
    assert calls == [(1.0, 0.024, 0.12, 0.25, 3.0), (1.0, 0.032, 0.12, 0.25, 3.0)]
    assert [(case.core, case.taxon) for case in selected.cases] == list(inputs.OWNERS)
    assert all(
        case.geometry.coefficient == Fraction(-math.log(0.5)) for case in selected.cases
    )
    assert selected.cases[0].geometry.first == (Fraction(1.25), Fraction(-3.5))
    for row in selected.native_prefix:
        a = row["A"]
        assert Fraction(a["numerator"], a["denominator"]) == Fraction(
            float.fromhex(a["hex"])
        )
        assert row["S1"] == {"hex": (0.5).hex(), "numerator": 1, "denominator": 2}
    references = {row.name: row.value for row in selected.cases[0].references}
    assert references["primary_anchor_sum"] == Fraction(0.1) + Fraction(0.2)
    assert references["primary_anchor_sum"] != Fraction(0.1 + 0.2)


@pytest.mark.parametrize(
    "damage",
    [
        "duplicate",
        "missing",
        "foreign",
        "cross_taxon_xy",
        "anchor_order",
        "axis",
        "fall",
        "radius",
        "physical",
        "baseline_owner",
    ],
)
def test_owner_or_profile_damage_refuses_before_any_native_capture(
    monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    result, original, protocol = packets()
    if damage == "duplicate":
        result["geometry"][1] = deepcopy(result["geometry"][0])
    elif damage == "missing":
        result["geometry"].pop()
    elif damage == "foreign":
        result["geometry"][0]["core"] = "OTHER"
    elif damage == "cross_taxon_xy":
        result["geometry"][1]["anchor_xy_m"][0][0] += 1
    elif damage == "anchor_order":
        result["geometry"][0]["anchor_order"].reverse()
    elif damage == "axis":
        result["axis"].reverse()
    elif damage == "fall":
        result["fall_speed_m_s"].reverse()
    elif damage == "radius":
        original["cores"][0]["radius_m"] = 81
    elif damage == "physical":
        original["physical"]["diffusion_coefficient"] = 0.13
    else:
        result["geometry"][0]["homogeneous_baseline"]["taxon"] = "OTHER"
    calls: list[object] = []
    monkeypatch.setattr(inputs, "gpm_values", lambda *args: calls.append(args))
    with pytest.raises(ValueError):
        inputs.prepare_inputs(result, original, protocol)
    assert not calls


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), "1.0"])
def test_non_native_geometry_numeric_values_are_refused(
    monkeypatch: pytest.MonkeyPatch, bad: object
) -> None:
    result, original, protocol = packets()
    result["geometry"][0]["anchor_xy_m"][0][0] = bad
    monkeypatch.setattr(inputs, "gpm_values", lambda *args: 0.5)
    with pytest.raises(ValueError, match="Finite"):
        inputs.prepare_inputs(result, original, protocol)


@pytest.mark.parametrize("survival", [0.0, 1.0, -0.5, float("nan"), float("inf")])
def test_native_prefix_does_not_impute_an_invalid_survival(
    monkeypatch: pytest.MonkeyPatch, survival: float
) -> None:
    result, original, protocol = packets()
    monkeypatch.setattr(inputs, "gpm_values", lambda *args: survival)
    with pytest.raises(ValueError, match="survival"):
        inputs.prepare_inputs(result, original, protocol)


def test_pinned_two_file_reader_and_duplicate_nonfinite_json_refusals(
    tmp_path: Path,
) -> None:
    path = fake_files(tmp_path)
    protocol = inputs.decode_json(path.read_bytes())
    result, original = inputs.read_inputs(tmp_path, protocol)
    assert result["axis"] == list(inputs.AXIS) and len(original["cores"]) == 3
    source = tmp_path / inputs.SOURCE_RESULT
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="receipt"):
        inputs.read_inputs(tmp_path, protocol)
    for payload in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
        with pytest.raises(ValueError):
            inputs.decode_json(payload)


@pytest.mark.parametrize(
    "name,value",
    [
        ("epsilon_exact", "1/1000"),
        ("saved_point_absolute_error_exact", "1/1000"),
        ("legacy_correspondence_absolute", 1e-6),
        ("legacy_correspondence_relative", 1e-5),
        ("arithmetic_bits", 64),
        ("quadrature_derivative_order", 4),
        ("maximum_radial_bands", True),
    ],
)
def test_typed_numerical_contract_cannot_silently_change(
    name: str, value: object
) -> None:
    _, _, protocol = packets()
    protocol["numerical_contract"][name] = value
    with pytest.raises(ValueError):
        inputs.validate_protocol(protocol)
