"""Measurements retain every attempt and distinguish compute from validated calls."""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from bijux_pollenomics_dev.native_backend import profiling
from bijux_pollenomics_dev.native_backend.profiling import Workload, measure, workloads
from bijux_pollenomics_lra.api import LRAError


def test_measure_keeps_first_call_and_every_warm_attempt() -> None:
    calls = []

    def consume() -> list[float]:
        calls.append(True)
        return [0.25, 0.75]

    result = measure(Workload("fixed", {}, consume), 3)
    assert result["attempted"] == 4
    assert len(result["warm_seconds"]) == 3
    assert len(calls) == 5  # Profiling uses a separate, untimed scientific call.
    assert result["identical_scientific_outputs"] is True
    assert result["status"] == "measured"
    assert result["scientific_output"] == [0.25, 0.75]


def test_refusal_is_retained_in_each_attempt() -> None:
    def consume() -> object:
        raise LRAError("declared unsupported input")

    result = measure(Workload("refused", {}, consume), 2)
    assert result["status"] == "refused"
    assert result["attempted"] == 3
    assert len(result["warm_seconds"]) == 2
    assert result["failure"]["type"] == "LRAError"
    assert result["scientific_output"] is None


def test_compute_only_dot_preserves_public_forward_scientific_output() -> None:
    selection = {workload.name: workload for workload in workloads()}
    public = cast(list[float], selection["forward-validated"].consume())
    compute = cast(list[float], selection["forward-dot-compute"].consume())
    np.testing.assert_allclose(public, compute, rtol=1e-10, atol=1e-12)
    assert "compute only" in selection["forward-dot-compute"].contract["validation"]
    assert (
        "no independent sites" in selection["lra-replicated-series"].contract["source"]
    )


def test_selected_forward_workload_avoids_other_source_fixtures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unrelated_source(*_args: object) -> None:
        raise AssertionError("Unrelated source fixture was loaded")

    monkeypatch.setattr(profiling, "load_love_example", unrelated_source)
    monkeypatch.setattr(profiling, "load_dataset", unrelated_source)
    selected = workloads("forward-validated")
    assert len(selected) == 1
    assert selected[0].name == "forward-validated"
    assert len(cast(list[float], selected[0].consume())) == 32
    with pytest.raises(ValueError, match="Undeclared"):
        workloads("missing-workload")


def test_single_favorable_timing_is_refused() -> None:
    with pytest.raises(ValueError, match="two timing repetitions"):
        measure(Workload("single", {}, lambda: [1.0]), 1)


def test_undefined_scientific_output_remains_null_with_native_reason() -> None:
    result = measure(Workload("undefined", {}, lambda: [[float("nan"), 0.0]]), 2)
    assert result["scientific_output"] == [[None, 0.0]]
    assert result["nonfinite_output_semantics"][0] == [
        {"path": "output[0][0]", "source_value": "nan"}
    ]
    assert result["identical_scientific_outputs"] is True
