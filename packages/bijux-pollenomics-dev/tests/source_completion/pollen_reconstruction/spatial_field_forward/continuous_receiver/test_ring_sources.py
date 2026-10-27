"""Count-free captured-law and original-source ownership mutation controls."""

from copy import deepcopy
from fractions import Fraction as Q
import json
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.contracts import (
    VerificationError,
    identity,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification.ring_sources import (
    AXIS,
    BASE,
    CAPTURE,
    CONTINUOUS_PROTOCOL,
    CORES,
    RADIAL_PROTOCOL,
    bind_raw_inputs,
    nested_edges,
    select_sources,
    validate_protocol,
)


def capture(value: float) -> dict[str, Any]:
    numerator, denominator = value.as_integer_ratio()
    return {"hex": value.hex(), "numerator": numerator, "denominator": denominator}


def source_fixture() -> tuple[dict[str, Any], ...]:
    owners = [(core, taxon) for core in CORES for taxon in AXIS]
    annuli = [
        {"inner_radius_m": float(2**i), "outer_radius_m": float(2 ** (i + 1))}
        for i in range(8)
    ]
    edges = [Q(1)]
    for row in annuli:
        left, right = row["inner_radius_m"], row["outer_radius_m"]
        edges.extend(
            Q(math.exp(math.log(left) + (math.log(right) - math.log(left)) * j / 16))
            for j in range(1, 16)
        )
        edges.append(Q(right))
    contract = {
        "endpoint_full_width_exact": "1/10000000000",
        "coefficient_full_width_exact": "1/1000000000",
        "arithmetic_bits": 96,
        "rule": "closed-newton-cotes-seven.v1",
        "endpoint_population": 774,
        "coefficient_population": 18,
        "prediction_contexts": 18,
        "family_slots": 54,
        "all_initial_endpoints_before_refinement": True,
    }
    protocol: dict[str, Any] = {
        "schema_version": "continuous-receiver-monotone-rings.v1",
        "cases": [{"core": c, "taxon": t} for c, t in owners],
        "numerical_contract": contract,
        "resources": {
            "wall_seconds": 180,
            "integration_work_seconds": 160,
            "peak_rss_bytes_posthoc": 805306368,
            "all_output_bytes": 5000000,
            "per_case_maximum_leaves": 4096,
            "per_case_maximum_attempted_panels": 8191,
            "per_case_maximum_node_evaluations": 73719,
            "per_case_maximum_live_queue": 4096,
        },
        "independent_resources": {
            "wall_seconds": 180,
            "replay_work_seconds": 160,
            "peak_rss_bytes_posthoc": 805306368,
            "all_output_bytes": 5000000,
        },
        "no_new_fits": True,
        "no_new_point_forecasts": True,
        "no_parameter_or_score_tuning": True,
        "retain_all_refusals": True,
        "unchanged_rerun_permitted": False,
        "captured_law_source_commit": "a" * 40,
        "edges_exact": {c: [str(x) for x in edges] for c in CORES},
    }
    original = {
        "schema_version": "spatial-field-forward-protocol.v1",
        "projected_axis": list(AXIS),
        "physical": {
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "wind_speed_m_s": 3.0,
            "regional_extent_m": 256.0,
        },
        "cores": [{"id": c, "radius_m": 1.0} for c in CORES],
    }
    public = {
        "schema_version": "spatial-field-forward-account.v1",
        "axis": list(AXIS),
        "fall_speed_m_s": [0.024, 0.032],
        "geometry": [
            {
                "core": c,
                "taxon": t,
                "anchor_order": [a for a in CORES if a != c],
                "anchor_xy_m": [[3.0, 1.0], [-3.0, -1.0]],
            }
            for c, t in owners
        ],
    }
    prediction = {
        "schema_version": "spatial-field-forward-predictions.v1",
        "axis": list(AXIS),
        "geometry": [
            {
                "core": c,
                "radius_m": 1.0,
                "anchor_order": [a for a in CORES if a != c],
                "anchor_xy_m": [[3.0, 1.0], [-3.0, -1.0]],
                "taxa": [{"step_bounds": {"annuli": deepcopy(annuli)}} for _ in AXIS],
            }
            for c in CORES
        ],
    }
    coefficient = -math.log(0.5)
    freeze = {
        "schema_version": "continuous-receiver-input-freeze.v1",
        "source_commit": "a" * 40,
        "historical_A_authenticated": False,
        "native_prefix": [
            {
                "taxon": t,
                "parameters": {
                    "diffusion_coefficient": 0.12,
                    "turbulence_parameter": 0.25,
                    "wind_speed_m_s": 3.0,
                    "fall_speed_m_s": speed,
                },
                "S1": capture(0.5),
                "A": capture(coefficient),
            }
            for t, speed in zip(AXIS, (0.024, 0.032), strict=True)
        ],
        "cases": [
            {
                "core": c,
                "taxon": t,
                "anchor_order": [a for a in CORES if a != c],
                "geometry": {
                    "coefficient_A": str(Q(coefficient)),
                    "receiver_radius_m": "1",
                    "outer_radius_m": "256",
                    "first_anchor_xy_m": ["3", "1"],
                    "second_anchor_xy_m": ["-3", "-1"],
                },
            }
            for c, t in owners
        ],
    }
    return protocol, public, original, freeze, prediction


def test_source_binding_preserves_all_original_coarse_boundaries() -> None:
    protocol, public, original, freeze, prediction = source_fixture()
    geometries, edges = select_sources(protocol, public, original, freeze, prediction)
    assert len(geometries) == len(edges) == 6
    assert all(len(row) == 129 for row in edges)
    assert all(row[::16] == tuple(Q(2**i) for i in range(9)) for row in edges)
    assert all(g.receiver == 1 and g.outer == 256 for g in geometries)


@pytest.mark.parametrize(
    "mutation",
    [
        "edge",
        "capture",
        "owner",
        "anchor",
        "radius",
        "historical",
        "parameter",
        "exponent",
    ],
)
def test_source_binding_rejects_literal_or_scientific_drift(mutation: str) -> None:
    protocol, public, original, freeze, prediction = source_fixture()
    if mutation == "edge":
        protocol["edges_exact"]["BOKE"][1] = "3/2"
    elif mutation == "capture":
        freeze["native_prefix"][0]["A"]["numerator"] += 1
    elif mutation == "owner":
        freeze["cases"][0]["core"] = "BUS"
    elif mutation == "anchor":
        public["geometry"][0]["anchor_order"].reverse()
    elif mutation == "radius":
        original["cores"][0]["radius_m"] = 2.0
    elif mutation == "historical":
        freeze["historical_A_authenticated"] = True
    elif mutation == "parameter":
        freeze["native_prefix"][0]["parameters"]["wind_speed_m_s"] = 4.0
    else:
        original["physical"]["turbulence_parameter"] = 0.5
    with pytest.raises((VerificationError, ValueError)):
        select_sources(protocol, public, original, freeze, prediction)


def test_taxon_specific_annulus_values_are_not_mistaken_for_geometry() -> None:
    _, _, _, _, prediction = source_fixture()
    for i, row in enumerate(
        prediction["geometry"][0]["taxa"][1]["step_bounds"]["annuli"]
    ):
        row["factor"] = i + 10
    assert len(nested_edges(prediction["geometry"][0], Q(1), Q(256))) == 129
    prediction["geometry"][0]["taxa"][1]["step_bounds"]["annuli"][1][
        "inner_radius_m"
    ] = 3.0
    with pytest.raises(VerificationError, match="Cross-taxon"):
        nested_edges(prediction["geometry"][0], Q(1), Q(256))


@pytest.mark.parametrize(
    "key,value",
    [
        ("endpoint_population", 774.0),
        ("coefficient_population", True),
        ("arithmetic_bits", 95),
        ("endpoint_full_width_exact", "1/1000000000"),
    ],
)
def test_typed_protocol_population_and_precision_are_not_coercible(
    key: str, value: object
) -> None:
    protocol = source_fixture()[0]
    protocol["numerical_contract"][key] = value
    with pytest.raises(VerificationError):
        validate_protocol(protocol)


def raw_fixture() -> tuple[dict[str, Any], dict[str, bytes]]:
    protocol = source_fixture()[0]
    paths = {
        role: f"artifacts/qualified/{role}.json"
        for role in (
            "source_prediction",
            "source_result",
            "source_verification",
            "source_execution",
        )
    }
    packets: dict[str, Any] = {
        BASE + "protocol.json": {},
        BASE + "result.json": {},
        CONTINUOUS_PROTOCOL: {},
        CAPTURE: {},
    }
    packets[paths["source_prediction"]] = {"source_commit": "b" * 40}
    packets[paths["source_result"]] = {"fixed": "saved-result"}
    bodies = {name: json.dumps(row).encode() for name, row in packets.items()}
    packets[CAPTURE] = {
        "input_files": {
            name: identity(bodies[name])
            for name in (BASE + "result.json", BASE + "protocol.json")
        },
        "protocol_file": {
            "path": CONTINUOUS_PROTOCOL,
            **identity(bodies[CONTINUOUS_PROTOCOL]),
        },
    }
    prediction_sha = identity(bodies[paths["source_prediction"]])["sha256"]
    result_sha = identity(bodies[paths["source_result"]])["sha256"]
    packets[paths["source_verification"]] = {
        "predictions_sha256": prediction_sha,
        "result_sha256": result_sha,
        "source_rows": 147,
        "selected_samples": 59,
        "source_contexts": 18,
        "scores": {"scored_rows": 54, "refused_rows": 0},
    }
    packets[paths["source_execution"]] = {
        "source_commit": "c" * 40,
        "exit_code": 0,
        "pytest_passed": 1,
        "source_results": {
            "predictions_sha256": prediction_sha,
            "result_sha256": result_sha,
        },
    }
    bodies = {name: json.dumps(row).encode() for name, row in packets.items()}
    packets[RADIAL_PROTOCOL] = {
        **paths,
        "prior_producer_source_commit": "b" * 40,
        "prior_observer_source_commit": "c" * 40,
        "repository_inputs": {name: identity(bodies[name]) for name in paths.values()},
    }
    bodies[RADIAL_PROTOCOL] = json.dumps(packets[RADIAL_PROTOCOL]).encode()
    protocol["input_files"] = {name: identity(raw) for name, raw in bodies.items()}
    return protocol, bodies


def test_raw_source_binding_retains_exact_qualified_inventory() -> None:
    protocol, raw = raw_fixture()
    assert set(bind_raw_inputs(protocol, raw)) == set(raw)
    raw[CAPTURE] += b" "
    with pytest.raises(VerificationError, match="identity"):
        bind_raw_inputs(protocol, raw)


def test_raw_source_binding_refuses_undeclared_and_relabelled_qualification() -> None:
    protocol, raw = raw_fixture()
    raw["artifacts/extra.json"] = b"{}"
    protocol["input_files"]["artifacts/extra.json"] = identity(b"{}")
    with pytest.raises(VerificationError, match="population"):
        bind_raw_inputs(protocol, raw)
    protocol, raw = raw_fixture()
    packet = json.loads(raw[RADIAL_PROTOCOL])
    packet["prior_observer_source_commit"] = "d" * 40
    raw[RADIAL_PROTOCOL] = json.dumps(packet).encode()
    protocol["input_files"][RADIAL_PROTOCOL] = identity(raw[RADIAL_PROTOCOL])
    with pytest.raises(VerificationError, match="qualification"):
        bind_raw_inputs(protocol, raw)
