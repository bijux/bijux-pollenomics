"""Closed source, parameter and coefficient origins with no real source execution."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer.inputs import (
    counts,
    load_inputs,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.country_transfer.responses import (
    build_responses,
)
from bijux_pollenomics_lra.models.errors import ValidationError

from .fixtures import protocol, saved_inputs, synthetic_response, write_pin


def test_all_qualified_owners_parameter_and_fixed_source_bindings(
    tmp_path: Path,
) -> None:
    profile, _ = saved_inputs(tmp_path)
    packet = load_inputs(tmp_path, profile)
    assert len(packet["sourcepins"]) == 27 and len(packet["cores"]) == 7
    assert packet["ppe"] == (5.10571, 6.05833)
    assert packet["covariance"] == ((0.092006056, 0.0), (0.0, 0.056016002))
    assert (
        sum(
            w["member_count"]
            for k in profile["profiles"][0]["cores"]
            for w in packet["cores"][k]["windows"]
        )
        == 155
    )
    assert (
        sum(
            w["member_count"]
            for k in profile["profiles"][2]["cores"]
            for w in packet["cores"][k]["windows"]
        )
        == 157
    )
    assert [w["status"] for w in packet["cores"]["solsoe81"]["windows"]][
        -1
    ] == "empty_window"


@pytest.mark.parametrize(
    "value",
    [[True, 1], [1.0, 2], [-1, 2], [0, 0], [2**53, 1], [2**53 - 1, 1], [1], None],
)
def test_native_integer_and_total_bounds_before_array_conversion(value: object) -> None:
    with pytest.raises(ValueError):
        counts(value)


def test_exact_zero_axis_and_large_integer_are_preserved() -> None:
    assert counts([0, 2**53 - 1]) == (0, 2**53 - 1)


@pytest.mark.parametrize(
    "role,damage",
    [
        ("swedish_response", "factor"),
        ("swedish_response", "radius"),
        ("nordic_response", "fall"),
        ("swedish_imports", "origin"),
        ("nordic_transport_protocol", "transport"),
        ("metadata_records", "rights"),
    ],
)
def test_self_consistent_source_pin_does_not_hide_wrong_scientific_binding(
    tmp_path: Path, role: str, damage: str
) -> None:
    profile, _ = saved_inputs(tmp_path)
    pin = profile["scientific_sources"][role]
    raw = (tmp_path / pin["path"]).read_bytes()
    if role == "metadata_records":
        rows = [json.loads(line) for line in raw.splitlines()]
        for cell in rows[0]["values"]:
            if cell["column"] == "DataRestricted/NotRestriced":
                cell["raw"] = "new permission"
        body = b"\n".join(json.dumps(r).encode() for r in rows)
        profile["scientific_sources"][role] = write_pin(
            tmp_path, pin["path"], body, raw=True
        )
    else:
        value = json.loads(raw)
        if damage == "factor":
            value["cores"][0]["quadrature"][0]["factors"][0][0] += 0.001
        elif damage == "radius":
            value["cores"][0]["metadata_static_radius_m"] += 1
        elif damage == "fall":
            value[1]["fall_speed_m_s"] = 0.031
        elif damage == "origin":
            value["module_origins"][0]["sha256"] = "0" * 64
        else:
            value["wind_speed_m_s"] = 4
        profile["scientific_sources"][role] = write_pin(tmp_path, pin["path"], value)
    with pytest.raises(ValueError):
        load_inputs(tmp_path, profile)


def test_changed_or_aliased_scientific_source_refuses(tmp_path: Path) -> None:
    profile, _ = saved_inputs(tmp_path)
    path = tmp_path / profile["scientific_sources"]["metadata_workbook"]["path"]
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="identity differs"):
        load_inputs(tmp_path, profile)


def test_only_three_missing_response_requests_call_current_operator() -> None:
    profile = protocol()
    calls = []

    def compute(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return synthetic_response(**kwargs)

    result = build_responses(profile, compute=compute)
    assert len(calls) == 3 and [r["receiver_radius_m"] for r in calls] == [
        80.0,
        69.0,
        89.0,
    ]
    assert len(result["rows"]) == 12
    assert sum(r["origin"] == "retained" for r in result["rows"]) == 9
    assert all(r["rigorous_error_bound"] is False for r in result["rows"])
    assert all(
        r["diagnostics"] is None and r["source_ref"] is not None
        for r in result["rows"][:9]
    )


@pytest.mark.parametrize(
    "factor,error,reason",
    [
        (0.0, 0.0, "nonpositive_receiver_response"),
        (-1.0, 0.0, "invalid_receiver_response"),
        (float("nan"), 0.0, "invalid_receiver_response"),
        (1.1, 0.0, "invalid_receiver_response"),
        (0.2, float("inf"), "invalid_receiver_response"),
    ],
)
def test_response_domain_refusal_is_explicit_without_clipping(
    factor: float, error: float, reason: str
) -> None:
    result = build_responses(
        protocol(),
        compute=lambda **_: SimpleNamespace(
            factor=factor, estimated_absolute_error=error
        ),
    )
    for row in result["rows"][9:]:
        assert row["status"] == "refused" and row["factor"] is None
        assert row["refusal"]["reason_code"] == reason
        assert row["rigorous_error_bound"] is False
        if factor == 0.0:
            assert row["diagnostics"] == {
                "factor": 0.0,
                "estimated_absolute_error": 0.0,
            }
    json.dumps(result, allow_nan=False)


def test_native_response_refusal_preserved_and_programming_error_propagates() -> None:
    def refused(**_: object) -> object:
        raise ValidationError(
            "controlled native refusal", reason_code="controlled_native"
        )

    result = build_responses(protocol(), compute=refused)
    assert all(
        r["refusal"]
        == {
            "error_type": "ValidationError",
            "reason_code": "controlled_native",
            "message": "controlled native refusal",
        }
        for r in result["rows"][9:]
    )

    def broken(**_: object) -> object:
        raise RuntimeError("programming fault")

    with pytest.raises(RuntimeError, match="programming fault"):
        build_responses(protocol(), compute=broken)


def test_source_profile_five_parent_module_contract_remains_separate() -> None:
    from bijux_pollenomics_dev.essd_reproduction.physical_forward import producer

    path = Path(producer.__file__).parent
    assert {p.name for p in path.glob("*.py")} == producer.SOURCE_NAMES
