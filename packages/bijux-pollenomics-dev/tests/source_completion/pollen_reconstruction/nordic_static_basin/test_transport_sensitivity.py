"""Exercise fixed population and callback flow, with no kernel or model calls."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.transport_sensitivity import (
    calculation,
    inputs,
    producer,
)


def protocol() -> dict[str, Any]:
    return {
        "schema_version": inputs.PROFILE,
        "source_report_sha256": inputs.REPORT_SHA256,
        "baseline_wind_speed_m_s": 3,
        "alternative_wind_speed_m_s": [2, 4],
        "regional_extent_m": 100000,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
        "alternative_status": "declared_conditional_assumptions_not_measured_winds",
        "justification": "Reuse the Swedish static-basin wind2/4 one-axis sensitivity around the same3m/s baseline; test numerical sensitivity, not physical likelihood or Nordic wind observations.",
        "geometry_policy": "retain_all_nine_original_static_geometries_without_new_radius_or_shape",
        "claims": {
            "measured_wind": False,
            "source_qualified_alternative_extent": False,
            "historical_reproduction": False,
            "vegetation_accuracy": False,
            "whole_lci_030": False,
        },
    }


def artificial_report() -> dict[str, Any]:
    """Complete artificial axes, retaining real finite scope sizes, not field data."""
    core_axes = {
        52082: (28072, 37925, [0.024, 0.031]),
        20034: (13388, 14989, [0.024, 0.031, 0.035]),
        4445: (3432, 4303, [0.024, 0.038]),
        4446: (3432, 4304, [0.021, 0.024, 0.038, 0.025, 0.032, 0.032]),
    }
    radii = [
        285,
        284.9017742606504,
        160,
        151.3879513212096,
        159.57691216057307,
        89,
        89.20620580763855,
        89,
        89.20620580763855,
    ]
    cases = []
    for (case_id, length), radius in zip(
        inputs.CASE_WINDOWS.items(), radii, strict=True
    ):
        did = int(case_id.split(".")[0])
        site, collection, speeds = core_axes[did]
        size = len(speeds)
        windows = []
        for index in range(length):
            counts = [index + 1] * size
            zero_matrix = [[0.0] * size for _ in range(size)]
            windows.append(
                {
                    "younger_cal_bp": index * 100,
                    "older_cal_bp_exclusive": (index + 1) * 100,
                    "counts": [counts],
                    "panel_count_denominator": sum(counts),
                    "reported_all_pollen_NISP_sum": sum(counts) + 1,
                    "unparameterized_reported_NISP_sum": 1,
                    "actual_source_panel_presence": True,
                    "assumed_zero_cells": 0,
                    "local_actual_source_support_sha256": inputs.fingerprint(
                        ["artificial", did, index]
                    ),
                    "conditional_cover": [1 / size] * size,
                    "direct_pollen_panel_fraction": [1 / size] * size,
                    "conditional_standard_error": [0.0] * size,
                    "counting_covariance": zero_matrix,
                    "assumed_ppe_covariance": zero_matrix,
                    "total_conditional_covariance": zero_matrix,
                }
            )
        cases.append(
            {
                "case_id": case_id,
                "native_dataset_id": did,
                "native_site_id": site,
                "native_collection_unit_id": collection,
                "occupied_windows": length,
                "parameter_taxa": [f"artificial-taxon-{i}" for i in range(size)],
                "PPE": [1.0] * size,
                "PPE_SD": [0.0] * size,
                "fall_speed_m_s": speeds,
                "static_geometry": {"radius_m": radius},
                "physical_response": {"factors": [[0.5] * size]},
                "panel_N_not_full_NISP": True,
                "source_present_not_hypothesized_zero": True,
                "results": windows,
            }
        )
    return {
        "candidate": inputs.SOURCE_EPOCH,
        "source_samples": 314,
        "accepted_source_samples": 313,
        "unique_physical_tuples": 23,
        "physical_tuple_case_uses": 29,
        "source_population": [
            {"native_dataset_id": did, "source_samples": n, "accepted_samples": k}
            for did, n, k in [
                (52082, 150, 150),
                (20034, 72, 72),
                (4445, 66, 65),
                (4446, 26, 26),
            ]
        ],
        "protocol": {
            "wind_speed_m_s": 3,
            "regional_extent_m": 100000,
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
        },
        "cases": cases,
    }


def stubs(monkeypatch: pytest.MonkeyPatch) -> list[tuple[float, float, int]]:
    calls = []

    def kernel(radius: float, speed: float, wind: int) -> dict[str, float]:
        calls.append((radius, speed, wind))
        return {"factor": wind / 10, "estimated_absolute_error": 0.0}

    def moments(
        case: dict[str, Any], window: dict[str, Any], factors: list[float]
    ) -> dict[str, Any]:
        result = {
            key: copy.deepcopy(window[key])
            for key in inputs.VECTOR_FIELDS + inputs.MATRIX_FIELDS
        }
        result["conditional_cover"][0] = factors[0]
        return result

    monkeypatch.setattr(calculation, "_kernel", kernel)
    monkeypatch.setattr(calculation, "_moments", moments)
    return calls


def test_complete_callback_flow_preserves_matches_and_all_requested_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = artificial_report()
    before = copy.deepcopy(report)
    calls = stubs(monkeypatch)
    result = calculation.calculate(report, protocol())
    assert (
        len(calls) == len(set(calls)) == result["unique_physical_tuple_requests"] == 46
    )
    assert result["requested_alternative_cases"] == 18
    assert result["requested_alternative_windows"] == result["computed_windows"] == 364
    assert result["refused_windows"] == 0 and report == before
    for case in result["cases"]:
        baseline = next(
            row for row in report["cases"] if row["case_id"] == case["baseline_case_id"]
        )
        for row, old in zip(case["windows"], baseline["results"], strict=True):
            assert row["baseline_window_sha256"] == inputs.fingerprint(old)
            assert row["source_window"]["counts"] == old["counts"]
            assert (
                row["source_window"]["panel_count_denominator"]
                == old["panel_count_denominator"]
            )
            assert row["moments"]["conditional_cover"][0] == case["wind_speed_m_s"] / 10
            assert (
                row["alternative_minus_saved_wind3"]["conditional_cover"][0]
                == case["wind_speed_m_s"] / 10 - old["conditional_cover"][0]
            )


@pytest.mark.parametrize(
    "change",
    [
        "missing_case",
        "duplicate_case",
        "foreign_core",
        "missing_window",
        "duplicate_window",
        "count_bool",
        "wrong_N",
        "missing_axis",
        "nonfinite",
        "geometry_membership",
    ],
)
def test_changed_population_or_native_axis_refuses(change: str) -> None:
    report = artificial_report()
    case = report["cases"][0]
    if change == "missing_case":
        report["cases"].pop()
    elif change == "duplicate_case":
        report["cases"][-1] = copy.deepcopy(case)
    elif change == "foreign_core":
        case["native_dataset_id"] = 999
    elif change == "missing_window":
        case["results"].pop()
    elif change == "duplicate_window":
        case["results"][1] = copy.deepcopy(case["results"][0])
    elif change == "count_bool":
        case["results"][0]["counts"][0][0] = True
    elif change == "wrong_N":
        case["results"][0]["panel_count_denominator"] += 1
    elif change == "missing_axis":
        case["PPE"].pop()
    elif change == "nonfinite":
        case["PPE"][0] = float("nan")
    else:
        report["cases"][1]["results"][0]["local_actual_source_support_sha256"] = (
            "f" * 64
        )
    with pytest.raises(ValueError):
        inputs.prepare(report, protocol())


@pytest.mark.parametrize(
    "field,value",
    [
        ("alternative_wind_speed_m_s", [1, 5]),
        ("regional_extent_m", 50000),
        ("alternative_wind_speed_m_s", [4, 2]),
    ],
)
def test_undeclared_transport_profile_refuses(field: str, value: object) -> None:
    value_protocol = protocol()
    value_protocol[field] = value
    with pytest.raises(ValueError):
        inputs.prepare(artificial_report(), value_protocol)


def test_known_kernel_refusal_retains_364_dispositions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stubs(monkeypatch)
    original = calculation._kernel

    def kernel(radius: float, speed: float, wind: int) -> dict[str, float]:
        result = original(radius, speed, wind)
        if (radius, speed, wind) == (285, 0.024, 2):
            raise calculation.NumericalRefusal(
                "circular annulus quadrature did not converge"
            )
        return result

    monkeypatch.setattr(calculation, "_kernel", kernel)
    result = calculation.calculate(artificial_report(), protocol())
    assert len(calls) == 46
    assert result["refused_windows"] == 24 and result["computed_windows"] == 340
    assert result["requested_alternative_windows"] == 364
    assert sum(row["status"] == "refused" for row in result["physical_responses"]) == 1


def test_unknown_failure_stays_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    def fault(*args: object) -> dict[str, float]:
        raise RuntimeError("artificial infrastructure failure")

    stubs(monkeypatch)
    monkeypatch.setattr(calculation, "_kernel", fault)
    with pytest.raises(RuntimeError, match="infrastructure"):
        calculation.calculate(artificial_report(), protocol())


def test_confined_atomic_publication_retains_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "artifacts").mkdir()
    monkeypatch.setattr(
        producer, "load", lambda root: (artificial_report(), protocol())
    )
    stubs(monkeypatch)
    destination = tmp_path / "artifacts/wind-sensitivity"
    result = producer.publish(tmp_path, destination, execution_epoch="a" * 40)
    assert json.loads((destination / "report.json").read_text()) == result
    with pytest.raises(ReportRebuildError):
        producer.publish(tmp_path, destination, execution_epoch="a" * 40)
    with pytest.raises(ReportRebuildError):
        producer.publish(tmp_path, tmp_path / "outside", execution_epoch="a" * 40)


def test_known_covariance_refusal_retains_window_mass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stubs(monkeypatch)
    original = calculation._moments

    def moments(
        case: dict[str, Any], window: dict[str, Any], factors: list[float]
    ) -> dict[str, Any]:
        if window["counts"][0][0] == 1 and factors[0] == 0.4:
            raise calculation.NumericalRefusal(
                "Fixed-site propagated covariance is invalid"
            )
        return original(case, window, factors)

    monkeypatch.setattr(calculation, "_moments", moments)
    result = calculation.calculate(artificial_report(), protocol())
    assert result["refused_windows"] == 9
    assert result["computed_windows"] == 355
    assert result["requested_alternative_windows"] == 364


def test_unknown_typed_engine_failure_is_not_a_refused_atom(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_lra.dispersal import receiver_annulus
    from bijux_pollenomics_lra.models.errors import ValidationError

    error = ValidationError(
        "artificial infrastructure unavailable", reason_code="engine_unavailable"
    )

    def fail(**kwargs: object) -> object:
        raise error

    monkeypatch.setattr(receiver_annulus, "circular_receiver_annulus", fail)
    with pytest.raises(ValidationError) as caught:
        calculation._kernel(1.0, 0.024, 2)
    assert caught.value is error and caught.value.reason_code == "engine_unavailable"


def test_retained_reader_compatibility_without_numerical_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.authority import (
        CAPTURE_PINS,
        DESCRIPTOR,
    )

    root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    for name in (*CAPTURE_PINS, DESCRIPTOR, producer.PROTOCOL):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / name, target)

    def no_kernel(*args: object) -> dict[str, float]:
        raise AssertionError("reader must not call a kernel")

    monkeypatch.setattr(calculation, "_kernel", no_kernel)
    report, declared = producer.load(tmp_path)
    assert len(report["cases"]) == 9
    assert sum(len(case["results"]) for case in report["cases"]) == 182
    assert declared == protocol()
    path = tmp_path / producer.PROTOCOL
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="protocol changed"):
        producer.load(tmp_path)
    shutil.copyfile(root / producer.PROTOCOL, path)
    baseline = tmp_path / inputs.REPORT
    baseline.write_bytes(baseline.read_bytes() + b" ")
    with pytest.raises(ValueError, match="source bytes changed"):
        producer.load(tmp_path)


def test_cli_retains_all_rows_before_nonzero_known_refusal_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "artifacts").mkdir()
    monkeypatch.setattr(
        producer, "load", lambda root: (artificial_report(), protocol())
    )
    stubs(monkeypatch)

    def refuse(*args: object) -> dict[str, float]:
        raise calculation.NumericalRefusal(
            "circular annulus quadrature did not converge"
        )

    monkeypatch.setattr(calculation, "_kernel", refuse)
    destination = tmp_path / "artifacts/known-refusals"
    assert (
        producer.main(
            [
                "--repository",
                str(tmp_path),
                "--output",
                str(destination),
                "--execution-epoch",
                "a" * 40,
            ]
        )
        == 1
    )
    result = json.loads((destination / "report.json").read_text())
    assert result["refused_windows"] == result["requested_alternative_windows"] == 364
    assert result["computed_windows"] == 0
    assert len(result["physical_responses"]) == 46
