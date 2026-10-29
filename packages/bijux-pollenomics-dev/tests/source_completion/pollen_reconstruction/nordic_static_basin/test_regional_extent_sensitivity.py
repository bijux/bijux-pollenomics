"""Complete artificial regional-cutoff flow, without kernel or model calls."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.transport_sensitivity import (
    calculation,
    inputs,
    regional_extent,
)

from .test_transport_sensitivity import artificial_report
from .test_transport_sensitivity import protocol as wind_protocol


def protocol() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[6]
    value: dict[str, Any] = json.loads(
        (repository / regional_extent.PROTOCOL).read_bytes()
    )
    return value


def stubs(monkeypatch: pytest.MonkeyPatch) -> list[tuple[float, float, int, float]]:
    calls: list[tuple[float, float, int, float]] = []

    def kernel(
        radius: float, speed: float, wind: int, *, outer_radius_m: float = 100000
    ) -> dict[str, float]:
        calls.append((radius, speed, wind, outer_radius_m))
        return {"factor": outer_radius_m / 1000000, "estimated_absolute_error": 0.0}

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


def test_complete_matched_cutoff_flow_preserves_source_and_denominators(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = artificial_report()
    before = copy.deepcopy(source)
    calls = stubs(monkeypatch)
    result = regional_extent.calculate(source, protocol(), wind_protocol())
    assert (
        len(calls) == len(set(calls)) == result["unique_physical_tuple_requests"] == 46
    )
    assert {row[2] for row in calls} == {3}
    assert {row[3] for row in calls} == {50000, 200000}
    assert result["requested_alternative_cases"] == 18
    assert result["requested_alternative_windows"] == result["computed_windows"] == 364
    assert result["refused_windows"] == 0 and source == before
    for case in result["cases"]:
        saved = next(
            c for c in source["cases"] if c["case_id"] == case["baseline_case_id"]
        )
        assert case["source_case_sha256"] == inputs.fingerprint(saved)
        assert case["regional_extent_m"] in (50000, 200000)
        for actual, old in zip(case["windows"], saved["results"], strict=True):
            assert actual["baseline_window_sha256"] == inputs.fingerprint(old)
            assert actual["source_window"] == {
                key: value
                for key, value in old.items()
                if key not in inputs.VECTOR_FIELDS + inputs.MATRIX_FIELDS
            }
            assert (
                actual["moments"]["conditional_cover"][0]
                == case["regional_extent_m"] / 1000000
            )
            assert actual["alternative_minus_saved_extent100km"]["conditional_cover"][
                0
            ] == (case["regional_extent_m"] / 1000000 - old["conditional_cover"][0])


@pytest.mark.parametrize(
    "field,value",
    [
        ("alternative_regional_extent_m", [200000, 50000]),
        ("alternative_regional_extent_m", [100000, 200000]),
        ("alternative_regional_extent_m", [0, 200000]),
        ("wind_speed_m_s", 4),
        ("source_report_sha256", "0" * 64),
        ("baseline_regional_extent_m", 50000),
        ("unknown_profile_dimension", 1),
    ],
)
def test_undeclared_profiles_refuse_before_any_callback(
    monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    calls = stubs(monkeypatch)
    altered = protocol()
    altered[field] = value
    with pytest.raises(ValueError, match="Frozen numerical regional-cutoff"):
        regional_extent.calculate(artificial_report(), altered, wind_protocol())
    assert calls == []


def test_native_count_axis_refusal_precedes_new_physics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stubs(monkeypatch)
    source = artificial_report()
    source["cases"][0]["results"][0]["counts"][0][0] = True
    with pytest.raises(ValueError, match="integer counts"):
        regional_extent.calculate(source, protocol(), wind_protocol())
    assert calls == []


def test_one_known_kernel_refusal_retains_all_request_and_window_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stubs(monkeypatch)
    original = calculation._kernel

    def kernel(
        radius: float, speed: float, wind: int, *, outer_radius_m: float = 100000
    ) -> dict[str, float]:
        value = original(radius, speed, wind, outer_radius_m=outer_radius_m)
        if (radius, speed, outer_radius_m) == (285, 0.024, 50000):
            raise calculation.NumericalRefusal(
                "circular annulus quadrature did not converge"
            )
        return value

    monkeypatch.setattr(calculation, "_kernel", kernel)
    result = regional_extent.calculate(artificial_report(), protocol(), wind_protocol())
    assert len(calls) == 46 and result["refused_windows"] == 24
    assert result["computed_windows"] == 340
    first = result["cases"][0]
    assert len(first["windows"]) == 24
    assert all(
        row["status"] == "refused"
        and row["moments"] is None
        and row["alternative_minus_saved_extent100km"] is None
        for row in first["windows"]
    )
    assert first["windows"][0]["reason"]["tuple_ids"] == [
        first["physical_tuple_ids"][0]
    ]


def test_all_known_refusals_preserve_complete_failed_population(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def kernel(
        radius: float, speed: float, wind: int, *, outer_radius_m: float = 100000
    ) -> dict[str, float]:
        raise calculation.NumericalRefusal(
            "circular annulus quadrature did not converge"
        )

    monkeypatch.setattr(calculation, "_kernel", kernel)
    result = regional_extent.calculate(artificial_report(), protocol(), wind_protocol())
    assert result["unique_physical_tuple_requests"] == 46
    assert result["requested_alternative_windows"] == result["refused_windows"] == 364
    assert result["computed_windows"] == 0
    assert all(
        row["status"] == "refused" and row["response"] is None
        for row in result["physical_responses"]
    )


@pytest.mark.parametrize(
    "error", [RuntimeError("implementation fault"), ValueError("engine unavailable")]
)
def test_unknown_faults_remain_fatal(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    def kernel(
        radius: float, speed: float, wind: int, *, outer_radius_m: float = 100000
    ) -> dict[str, float]:
        raise error

    monkeypatch.setattr(calculation, "_kernel", kernel)
    with pytest.raises(type(error)) as caught:
        regional_extent.calculate(artificial_report(), protocol(), wind_protocol())
    assert caught.value is error
