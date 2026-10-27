"""Synthetic scientific-packet binding and independent closed-leaf replay controls."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import json
import math
from pathlib import Path
import platform
import sys
from typing import Any, cast

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    certificate,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    DYADIC_RADIAL,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    certificates as verify_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    contracts as verify_contracts,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    geometry as verify_geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    population as verify_population,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    sources as verify_sources,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.verification import (
    study as verify_study,
)
from bijux_pollenomics_lra.dispersal.kernels import gpm_values

PROTOCOL_PATH = "reports/science/pollen-reconstruction/spatial-field-forward/continuous-receiver/protocol.json"


def raw(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def captured(value: float) -> dict[str, Any]:
    numerator, denominator = value.as_integer_ratio()
    return {"hex": value.hex(), "numerator": numerator, "denominator": denominator}


def sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    original = {
        "schema_version": "spatial-field-forward-protocol.v1",
        "projected_axis": ["Betula", "Ulmus"],
        "physical": {
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "wind_speed_m_s": 3.0,
            "regional_extent_m": 2.0,
        },
        "cores": [
            {"id": core, "radius_m": 1.0} for core in ("BOKE", "BUS", "SOLSOE83")
        ],
    }
    source = {
        "schema_version": "spatial-field-forward-account.v1",
        "axis": ["Betula", "Ulmus"],
        "fall_speed_m_s": [0.024, 0.032],
        "geometry": [
            {
                "core": core,
                "taxon": taxon,
                "anchor_order": [
                    other for other in ("BOKE", "BUS", "SOLSOE83") if other != core
                ],
                "anchor_xy_m": [[3.0, 1.0], [-5.0, 2.0]],
                "homogeneous_baseline": {
                    "taxon": taxon,
                    "status": "qualified",
                    "factor": 0.5,
                },
                "primary": {
                    "homogeneous_factor": 0.375,
                    "anchor_factors": [0.125, 0.25],
                },
            }
            for core, taxon in verify_contracts.OWNERS
        ],
    }
    prefixes: list[dict[str, Any]] = []
    for taxon, speed in zip(("Betula", "Ulmus"), (0.024, 0.032), strict=True):
        s1 = float(gpm_values(1.0, speed, 0.12, 0.25, 3.0))
        prefixes.append(
            {
                "taxon": taxon,
                "parameters": {
                    "diffusion_coefficient": 0.12,
                    "turbulence_parameter": 0.25,
                    "wind_speed_m_s": 3.0,
                    "fall_speed_m_s": speed,
                },
                "S1": captured(s1),
                "A": captured(-math.log(s1)),
            }
        )
    protocol = {
        "schema_version": "continuous-receiver-study.v1",
        "population": {
            "cases": [
                {"core": core, "taxon": taxon}
                for core, taxon in verify_contracts.OWNERS
            ],
            "case_count": 6,
            "coefficients_per_case": ["K", "B1", "B2"],
            "complete_coefficient_population": 18,
            "retain_all_case_statuses": True,
        },
        "input_files": {
            verify_contracts.INPUT_NAMES[0]: verify_contracts.identity(raw(source)),
            verify_contracts.INPUT_NAMES[1]: verify_contracts.identity(raw(original)),
        },
        "method": {
            "rule": "closed-newton-cotes-seven.v1",
            "partition": "dyadic_radial",
        },
        "numerical_contract": {
            "epsilon_exact": "1/1000000000",
            "saved_point_absolute_error_exact": "1/1000000000",
            "legacy_correspondence_absolute": 1e-9,
            "legacy_correspondence_relative": 1e-8,
            "arithmetic_bits": 96,
            "quadrature_derivative_order": 8,
            "maximum_radial_bands": 11,
        },
        "resources": dict(verify_contracts.RESOURCE_LIMITS),
    }
    freeze: dict[str, Any] = {
        "schema_version": "continuous-receiver-input-freeze.v1",
        "source_commit": "a" * 40,
        "input_files": protocol["input_files"],
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "historical_A_authenticated": False,
        "native_prefix": prefixes,
        "cases": [],
    }
    for i, (core, taxon) in enumerate(verify_contracts.OWNERS):
        prefix = prefixes[0 if taxon == "Betula" else 1]
        a = Q(prefix["A"]["numerator"], prefix["A"]["denominator"])
        freeze["cases"].append(
            {
                "case_index": i,
                "core": core,
                "taxon": taxon,
                "anchor_order": [
                    other for other in ("BOKE", "BUS", "SOLSOE83") if other != core
                ],
                "geometry": {
                    "coefficient_A": str(a),
                    "receiver_radius_m": "1",
                    "outer_radius_m": "2",
                    "first_anchor_xy_m": ["3", "1"],
                    "second_anchor_xy_m": ["-5", "2"],
                },
            }
        )
    pin = {"path": PROTOCOL_PATH, **verify_contracts.identity(raw(protocol))}
    freeze["protocol_file"] = pin
    return protocol, source, original, freeze


def reference_rows(bounds: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for name, target, value in [
        ("standalone_K", "K", Q(1, 2)),
        ("primary_K", "K", Q(3, 8)),
        ("primary_anchor_sum", "K", Q(3, 8)),
        ("primary_B1", "B1", Q(1, 8)),
        ("primary_B2", "B2", Q(1, 4)),
    ]:
        lower, upper = map(Q, bounds[target])
        maximum = max(abs(value - lower), abs(value - upper))
        tolerance = Q(*(1e-9).as_integer_ratio()) + Q(*(1e-8).as_integer_ratio()) * abs(
            value
        )
        rows.append(
            {
                "name": name,
                "target": target,
                "value_exact": str(value),
                "bounds": bounds[target],
                "max_absolute_error_exact": str(maximum),
                "absolute_error_certified": maximum <= Q(1, 10**9),
                "correspondence_tolerance_exact": str(tolerance),
                "correspondence_pass": maximum <= tolerance,
            }
        )
    return rows


@pytest.fixture(scope="module")
def witness() -> tuple[tuple[dict[str, Any], ...], dict[str, Any]]:
    protocol, source, original, freeze = sources()
    a = Q(
        freeze["native_prefix"][0]["A"]["numerator"],
        freeze["native_prefix"][0]["A"]["denominator"],
    )
    budget = WorkBudget(max_leaves=4, max_attempts=4, max_nodes=112, max_queue=4)
    result = certify(
        Geometry(a, Q(1), Q(2), (Q(3), Q(1)), (Q(-5), Q(2))),
        budget,
        rule=SEVEN_NODE_RULE,
        partition=DYADIC_RADIAL,
    )
    proof = cast(dict[str, Any], certificate(result))
    independent_geometry = verify_geometry.Geometry(
        a, Q(1), Q(2), (Q(3), Q(1)), (Q(-5), Q(2))
    )
    checked = verify_certificates.verify_certificate(
        proof, independent_geometry, verify_contracts.Clock(seconds=30)
    )
    case_rows = []
    for i, (core, taxon) in enumerate(verify_contracts.OWNERS):
        case_rows.append(
            {
                "case_index": i,
                "core": core,
                "taxon": taxon,
                "backend_refusal": "not_executed:wall_seconds",
                "work": {
                    "attempted_panels": 0,
                    "reserved_node_evaluations": 0,
                    "completed_node_evaluations": 0,
                    "derivative_boxes": 0,
                    "leaf_reservations": 0,
                },
                "complete_geometry_certificate": False,
                "backend_status": None,
                "math_bounds": None,
                "widths_exact": None,
                "all_final_widths_pass": False,
                "positive_bounds_usable": False,
                "local_integral_allocations_pass": False,
                "endpoint_product_allocations_pass": False,
                "local_allocations_pass": False,
                "references": None,
            }
        )
    case_rows[0].update(
        {
            "backend_refusal": "leaf_ceiling",
            "work": {
                "attempted_panels": budget.attempts,
                "reserved_node_evaluations": budget.nodes,
                "completed_node_evaluations": budget.completed_nodes,
                "derivative_boxes": budget.derivative_boxes,
                "leaf_reservations": budget.leaves,
            },
            "complete_geometry_certificate": True,
            "backend_status": result.status,
            "math_bounds": proof["coefficient_bounds"],
            "widths_exact": {
                name: str(verify_contracts.bounds(value).width)
                for name, value in proof["coefficient_bounds"].items()
            },
            **{
                name: checked[name]
                for name in (
                    "all_final_widths_pass",
                    "positive_bounds_usable",
                    "local_integral_allocations_pass",
                    "endpoint_product_allocations_pass",
                    "local_allocations_pass",
                )
            },
            "references": reference_rows(proof["coefficient_bounds"]),
        }
    )
    packet = {
        "schema_version": "continuous-receiver-study-result.v1",
        "status": "refuse_unresolved",
        "source_commit": "a" * 40,
        "input_files": protocol["input_files"],
        "protocol_file": freeze["protocol_file"],
        "input_freeze": "input-freeze.json",
        "input_freeze_file": {
            "path": "input-freeze.json",
            **verify_contracts.identity(raw(freeze)),
        },
        "certificate_file": "certificates.json",
        "certificate_identity": {
            "path": "certificates.json",
            **verify_contracts.identity(raw([proof])),
        },
        "certificate_cases": [
            {"case_index": 0, "core": "BOKE", "taxon": "Betula", "certificate_index": 0}
        ],
        "certificate_closed": True,
        "certificate_refusal": None,
        "all_population_complete": False,
        "source_guards_pass": True,
        "resource_guards_pass": True,
        "resource_limits": dict(verify_contracts.RESOURCE_LIMITS),
        "elapsed_seconds": 1.0,
        "integration_elapsed_seconds": 0.9,
        "peak_rss_bytes": 10000000,
        "cases": case_rows,
    }
    return (
        protocol,
        source,
        original,
        freeze,
        packet,
        {"certificates": [proof]},
    ), checked


def test_independent_fixed_leaf_geometry_and_refused_width_are_explicit(
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
) -> None:
    values, checked = witness
    assert checked["leaves"] == 4 and checked["fixed_node_evaluations"] == 112
    assert checked["independent_all_final_widths_pass"] is False
    assert checked["saved_bounds"] == values[5]["certificates"][0]["coefficient_bounds"]
    assert all(
        max(
            Q(checked["saved_bounds"][key][0]), Q(checked["independent_bounds"][key][0])
        )
        <= min(
            Q(checked["saved_bounds"][key][1]), Q(checked["independent_bounds"][key][1])
        )
        for key in ("K", "B1", "B2")
    )


def audited(
    values: tuple[dict[str, Any], ...],
    monkeypatch: pytest.MonkeyPatch,
    checked: dict[str, Any],
) -> dict[str, Any]:
    monkeypatch.setattr(
        verify_population, "verify_certificate", lambda *_args: deepcopy(checked)
    )
    return verify_population.audit(
        values[0],
        values[1],
        values[2],
        values[3],
        values[4],
        values[5]["certificates"],
        verify_contracts.Clock(seconds=30),
    )


def test_partial_population_accounting_never_becomes_full_acceptance(
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values, checked = witness
    result = audited(deepcopy(values), monkeypatch, checked)
    assert (
        result["accounting_verified"] is True
        and result["status"] == "refuse_unresolved"
    )
    assert result["independent_all_18_widths_pass"] is False
    assert (
        len(result["cases"]) == 6
        and sum(
            row["status"] == "incomplete_source_geometry" for row in result["cases"]
        )
        == 5
    )


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "doubled",
        "reordered",
        "foreign_anchor",
        "native_ratio",
        "native_call",
        "historical",
        "reference",
        "negative_width",
        "work_reset",
        "derivative_reset",
        "promoted_incomplete",
        "certificate_mapping",
        "boolean_index",
        "typed_epsilon",
    ],
)
def test_scientific_binding_and_result_tampering_refuse(
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    values, checked = witness
    protocol, source, original, freeze, result, _ = deepcopy(values)
    if damage == "missing":
        result["cases"].pop()
    elif damage == "doubled":
        result["cases"][1] = deepcopy(result["cases"][0])
    elif damage == "reordered":
        result["cases"].reverse()
    elif damage == "foreign_anchor":
        freeze["cases"][0]["geometry"]["first_anchor_xy_m"][0] = "4"
    elif damage == "native_ratio":
        freeze["native_prefix"][0]["A"]["numerator"] += 1
    elif damage == "native_call":
        freeze["native_prefix"][0]["parameters"]["wind_speed_m_s"] = 4.0
    elif damage == "historical":
        freeze["historical_A_authenticated"] = True
    elif damage == "reference":
        result["cases"][0]["references"][0]["max_absolute_error_exact"] = "0"
    elif damage == "negative_width":
        result["cases"][0]["widths_exact"]["B1"] = "-1"
    elif damage == "work_reset":
        result["cases"][0]["work"]["completed_node_evaluations"] = 0
    elif damage == "derivative_reset":
        result["cases"][0]["work"]["derivative_boxes"] = 0
    elif damage == "promoted_incomplete":
        result["cases"][1]["all_final_widths_pass"] = True
    elif damage == "certificate_mapping":
        result["certificate_cases"].append(deepcopy(result["certificate_cases"][0]))
    elif damage == "boolean_index":
        result["cases"][1]["case_index"] = True
    else:
        protocol["numerical_contract"]["epsilon_exact"] = "1/1000"
    with pytest.raises(verify_contracts.VerificationError):
        audited(
            (protocol, source, original, freeze, result, values[5]),
            monkeypatch,
            checked,
        )


@pytest.mark.parametrize(
    "damage",
    [
        "missing_band",
        "foreign_receiver",
        "unknown_rule",
        "negative_radius",
        "missing_leaf",
        "duplicate_leaf",
        "wrong_allocation",
        "wrong_radial_sum",
    ],
)
def test_certificate_population_and_arithmetic_tampering_refuse(
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]], damage: str
) -> None:
    values, _ = witness
    proof = deepcopy(values[5]["certificates"][0])
    if damage == "missing_band":
        proof["radial_bands"].pop()
    elif damage == "foreign_receiver":
        proof["geometry"]["receiver_radius_m"] = "2"
    elif damage == "unknown_rule":
        proof["quadrature_rule"] = "unknown"
    elif damage == "negative_radius":
        proof["integrals"][0]["leaves"][0]["error_radius"] = "-1"
    elif damage == "missing_leaf":
        proof["integrals"][0]["leaves"] = []
    elif damage == "duplicate_leaf":
        proof["integrals"][0]["leaves"] *= 2
    elif damage == "wrong_allocation":
        proof["radial_domains"][0]["target_full_width"] = "1/8000000000"
    else:
        proof["radial_sum_bounds"] = ["0", "0"]
    geometry = values[3]["cases"][0]["geometry"]
    independent = verify_geometry.Geometry(
        Q(geometry["coefficient_A"]), Q(1), Q(2), (Q(3), Q(1)), (Q(-5), Q(2))
    )
    with pytest.raises(verify_contracts.VerificationError):
        verify_certificates.verify_certificate(
            proof, independent, verify_contracts.Clock(seconds=30)
        )


def test_original_absolute_error_and_legacy_correspondence_are_distinct() -> None:
    radius = Q(1, 2**29)
    interval = [str(Q(1, 4) - radius), str(Q(1, 4) + radius)]
    row = verify_sources.reference_checks([("known", "K", Q(1, 4))], {"K": interval})[0]
    assert row["max_absolute_error_exact"] == str(radius)
    assert (
        row["absolute_error_certified"] is False and row["correspondence_pass"] is True
    )
    assert row["correspondence_tolerance_exact"] == str(
        Q(4835703278458517, 2**82) + Q(3022314549036573, 2**78) / 4
    )


def write_packet(root: Path, values: tuple[dict[str, Any], ...]) -> tuple[Path, Path]:
    protocol, source, original, freeze, result, proof = deepcopy(values)
    protocol_path = root / PROTOCOL_PATH
    protocol_path.parent.mkdir(parents=True)
    protocol_path.write_bytes(raw(protocol))
    for name, value in zip(
        verify_contracts.INPUT_NAMES, (source, original), strict=True
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw(value))
    folder = root / "artifacts" / "closed-study"
    folder.mkdir(parents=True)
    (folder / "input-freeze.json").write_bytes(raw(freeze))
    (folder / "certificates.json").write_bytes(raw(proof["certificates"]))
    (folder / "result.json").write_bytes(raw(result))
    return protocol_path, folder


def test_raw_certificate_sha_and_path_ownership_are_enforced(
    tmp_path: Path, witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]]
) -> None:
    values, _ = witness
    protocol, folder = write_packet(tmp_path, values)
    assert (
        verify_study.load_packet(tmp_path, protocol, folder)[5]
        == values[5]["certificates"]
    )
    path = folder / "certificates.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(verify_contracts.VerificationError, match="identity"):
        verify_study.load_packet(tmp_path, protocol, folder)


def test_metadata_byte_cap_and_nonlattice_boundaries_refuse() -> None:
    with pytest.raises(verify_contracts.VerificationError):
        verify_study._pin_file(
            {"path": "certificates.json", "bytes": 5000001, "sha256": "a" * 64},
            "certificates.json",
        )
    with pytest.raises(verify_contracts.VerificationError):
        verify_study._pin_file(
            {"path": "../certificates.json", "bytes": 1, "sha256": "a" * 64},
            "certificates.json",
        )
    with pytest.raises(verify_contracts.VerificationError):
        verify_contracts.bounds(["0", "1/3"])
    with pytest.raises(verify_contracts.VerificationError):
        verify_contracts.bounds(["1", "0"])
    with pytest.raises(verify_contracts.VerificationError):
        verify_certificates._box([["0", "3/4"]], 1)


@pytest.mark.parametrize(
    "damage", ["coefficients", "eighteen", "retain", "boolean_count"]
)
def test_typed_complete_population_cannot_be_relaxed(damage: str) -> None:
    protocol, _, _, _ = sources()
    if damage == "coefficients":
        protocol["population"]["coefficients_per_case"] = ["K", "B1"]
    elif damage == "eighteen":
        protocol["population"]["complete_coefficient_population"] = 17
    elif damage == "retain":
        protocol["population"]["retain_all_case_statuses"] = False
    else:
        protocol["population"]["case_count"] = True
    with pytest.raises(verify_contracts.VerificationError):
        verify_sources.validate_protocol(protocol)


def test_owned_locator_refuses_symlink_and_parent_traversal(tmp_path: Path) -> None:
    folder = tmp_path / "artifacts"
    folder.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(folder, target_is_directory=True)
    with pytest.raises(verify_contracts.VerificationError, match="Symlink"):
        verify_study._owned(tmp_path, alias / "proof.json")
    with pytest.raises(verify_contracts.VerificationError, match="escapes"):
        verify_study._owned(tmp_path, folder / ".." / "proof.json")


def test_independent_fixed_rule_has_literal_peano_radius_and_signed_moments() -> None:
    node, radius, directions = verify_certificates.replay_leaf(
        lambda args: args[0] ** 8 - 2 * args[1] ** 8,
        ((Q(0), Q(1)),) * 2,
        verify_contracts.Clock(seconds=30),
    )
    unit = Q(1, 38880)
    assert directions == (unit, 2 * unit) and radius == 3 * unit
    expected = -Q(1, 9) - unit
    assert node.lower <= expected <= node.upper
    assert node.width < Q(1, 10**24)
    assert node.expanded(radius).lower <= -Q(1, 9) <= node.expanded(radius).upper


def test_unavailable_aggregate_certificate_preserves_all_backend_dispositions(
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values, checked = witness
    data = deepcopy(values)
    result = data[4]
    result.update(
        certificate_closed=False,
        certificate_cases=[],
        certificate_file=None,
        certificate_identity=None,
        certificate_refusal="certificate_byte_ceiling",
    )
    for row in result["cases"]:
        row.update(
            complete_geometry_certificate=False,
            all_final_widths_pass=False,
            positive_bounds_usable=False,
            references=None,
        )
    data[5]["certificates"] = []
    checked_result = audited(data, monkeypatch, checked)
    assert (
        checked_result["accounting_verified"] is True
        and checked_result["status"] == "refuse_unresolved"
    )
    assert len(checked_result["cases"]) == 6
    assert checked_result["cases"][0]["backend_status"] == "refuse_unresolved"
    assert checked_result["independent_all_18_widths_pass"] is False


def test_failed_packet_binding_is_retained_without_running_math(
    tmp_path: Path,
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values, _ = witness
    protocol, folder = write_packet(tmp_path, values)
    proof = folder / "certificates.json"
    proof.write_bytes(proof.read_bytes() + b" ")
    monkeypatch.setattr(
        verify_study, "_guard", lambda *_args: ("a" * 40, "fixed-index", ())
    )

    def forbidden(*_args: object) -> dict[str, Any]:
        raise AssertionError("unbound packet reached mathematical audit")

    monkeypatch.setattr(verify_study, "audit", forbidden)
    output = tmp_path / "artifacts" / "independent.json"
    result = verify_study.run_verification(tmp_path, protocol, folder, output)
    assert result["status"] == "failed" and result["accounting_verified"] is False
    assert "identity" in result["reason"] and output.is_file()
    with pytest.raises(verify_contracts.VerificationError, match="Fresh"):
        verify_study.run_verification(tmp_path, protocol, folder, output)


def test_closed_proof_mutation_during_observation_cannot_be_accepted(
    tmp_path: Path,
    witness: tuple[tuple[dict[str, Any], ...], dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values, _ = witness
    protocol, folder = write_packet(tmp_path, values)
    monkeypatch.setattr(
        verify_study, "_guard", lambda *_args: ("a" * 40, "fixed-index", ())
    )

    def mutation(*_args: object) -> dict[str, Any]:
        path = folder / "certificates.json"
        path.write_bytes(path.read_bytes() + b" ")
        return {"status": "passed", "accounting_verified": True}

    monkeypatch.setattr(verify_study, "audit", mutation)
    output = tmp_path / "artifacts" / "independent.json"
    with pytest.raises(verify_contracts.VerificationError, match="changed"):
        verify_study.run_verification(tmp_path, protocol, folder, output)
    assert not output.exists()


def test_independent_regular_band_is_replayed_from_a_closed_synthetic_partition() -> (
    None
):
    coefficient = Q(3, 5)
    budget = WorkBudget(max_leaves=5, max_attempts=5, max_nodes=161, max_queue=5)
    result = certify(
        Geometry(coefficient, Q(1), Q(4), (Q(3), Q(1)), (Q(-5), Q(2))),
        budget,
        rule=SEVEN_NODE_RULE,
        partition=DYADIC_RADIAL,
    )
    proof = cast(dict[str, Any], certificate(result))
    geometry = verify_geometry.Geometry(
        coefficient, Q(1), Q(4), (Q(3), Q(1)), (Q(-5), Q(2))
    )
    checked = verify_certificates.verify_certificate(
        proof, geometry, verify_contracts.Clock(seconds=30)
    )
    assert checked["initial_domains"] == checked["leaves"] == 5
    assert checked["fixed_node_evaluations"] == 161
    assert checked["independent_all_final_widths_pass"] is False
    assert proof["radial_domains"][-1]["kind"] == "regular_band"
    assert proof["radial_domains"][-1]["original_receiver_radius_m"] == "1"
    assert proof["radial_domains"][-1]["band_bounds_m"] == ["2", "4"]


def test_adaptive_dyadic_coverage_proves_nonuniform_rectangles_without_gaps() -> None:
    lower, half, upper = Q(0), Q(1, 2), Q(1)
    partition: list[verify_contracts.Box] = [
        ((lower, half), (lower, upper)),
        ((half, upper), (lower, half)),
        ((half, upper), (half, upper)),
    ]
    verify_certificates._coverage(partition, 2, verify_contracts.Clock(seconds=10))
    for damaged in (partition[:-1], partition + [partition[0]]):
        with pytest.raises(verify_contracts.VerificationError):
            verify_certificates._coverage(
                damaged, 2, verify_contracts.Clock(seconds=10)
            )
