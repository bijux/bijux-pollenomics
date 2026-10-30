"""Fresh same-seed calls retain one product and observable failures."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics.analysis.lra.engine.discovery import load_engine
from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.execution import benchmark
from bijux_pollenomics.analysis.lra.outputs.publication import LRAProduct

from ..outputs.test_publication import Manifest, binding
from ..support import request_fixture


@dataclass
class Result:
    manifest: Manifest = field(default_factory=Manifest)
    table: pd.DataFrame = field(default_factory=lambda: pd.DataFrame({"Alnus": [0.5]}))
    samples: np.ndarray = field(default_factory=lambda: np.array([[0.5, 0.5]]))
    diagnostics: list[dict[str, object]] = field(
        default_factory=lambda: [{"success": True, "nfev": 1}]
    )


def test_actual_optional_engine_publishes_one_reference_for_each_operation(
    tmp_path: Path,
) -> None:
    for operation in ("reveals", "love", "lra", "series"):
        inputs = tmp_path / operation
        inputs.mkdir()
        result = benchmark.benchmark_lra_request(
            request_fixture(inputs, operation),
            input_root=inputs,
            destination=inputs / "reference",
            repeats=2,
        )
        assert result["status"] == "benchmarked_exploratory"
        assert result["operation"] == operation and result["seed"] == 7
        assert len(result["repeated_call_seconds"]) == 1
        assert result["first_call_seconds"] >= 0
        assert result["repeated_call_seconds"][0] >= 0
        assert result["engine"]["numerical_backend"] == "python-numpy-scipy"
        assert (inputs / "reference/manifest.json").is_file()
        assert sorted(p.name for p in inputs.iterdir() if p.is_dir()) == ["reference"]


@pytest.mark.parametrize("repeats", [True, 0, 1, 11, 2.0])
def test_invalid_repeat_budget_never_loads_or_runs_engine(
    tmp_path: Path, repeats: Any
) -> None:
    with (
        patch.object(benchmark, "load_engine") as load,
        pytest.raises(LRARefusal) as raised,
    ):
        benchmark.benchmark_lra_request(
            {}, input_root=tmp_path, destination=tmp_path / "out", repeats=repeats
        )
    assert raised.value.reason_code == "invalid_lra_benchmark_repeats"
    load.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        "numerical",
        "unexpected",
        "interrupted",
        "source",
        "code",
        "value",
        "axis",
        "diagnostic",
        "manifest",
    ],
)
def test_failure_preserves_attempts_and_refuses_reference_publication(
    tmp_path: Path, failure: str
) -> None:
    engine, payload = binding(tmp_path), request_fixture(tmp_path)
    shared = Result()
    calls = 0

    def calculate(*_: object) -> Result:
        nonlocal calls
        calls += 1
        if calls == 2:
            if failure == "numerical":
                raise LRARefusal(
                    "numerical_budget",
                    "real exhausted budget",
                    diagnostics={"steps": 12},
                )
            if failure == "unexpected":
                raise RuntimeError("unexpected native failure")
            if failure == "interrupted":
                raise KeyboardInterrupt
            if failure in ("code", "source"):
                (
                    tmp_path
                    / ("installed/api.py" if failure == "code" else "raw_snapshot.txt")
                ).write_text("changed")
            if failure == "value":
                shared.table.iloc[0, 0] = 0.6
            if failure == "axis":
                shared.table.columns = ["different taxon"]
            if failure == "diagnostic":
                shared.diagnostics[0]["nfev"] = 2
            if failure == "manifest":
                shared.manifest = ChangedManifest()
        # Same engine-owned object across calls must not mutate the reference.
        return shared

    with (
        patch.object(benchmark, "load_engine", return_value=engine),
        patch.object(benchmark, "validate_engine_configuration"),
        patch.object(benchmark, "reconstruct", side_effect=calculate),
        patch.object(benchmark, "publish_result") as publish,
        pytest.raises(LRARefusal) as raised,
    ):
        benchmark.benchmark_lra_request(
            payload, input_root=tmp_path, destination=tmp_path / "out", repeats=3
        )
    expected = {
        "numerical": "numerical_budget",
        "unexpected": "lra_benchmark_failed",
        "interrupted": "lra_benchmark_interrupted",
        "source": "evidence_digest_mismatch",
        "code": "lra_code_changed_during_run",
    }.get(failure, "lra_benchmark_nonrepeatable")
    assert raised.value.reason_code == expected
    diagnostics = raised.value.diagnostics
    assert isinstance(diagnostics, dict)
    assert diagnostics["attempted_calls"] == 2
    assert diagnostics["completed_calls"] == (
        1 if failure in ("numerical", "unexpected", "interrupted") else 2
    )
    assert len(diagnostics["call_seconds"]) == 2
    if failure == "numerical":
        assert diagnostics["cause"] == {"steps": 12}
    publish.assert_not_called()


class ChangedManifest(Manifest):
    def scientific_identity(self) -> dict[str, str]:
        return {"identity": "different"}


def test_shared_result_is_detached_and_only_one_reference_is_published(
    tmp_path: Path,
) -> None:
    engine, payload = binding(tmp_path), request_fixture(tmp_path)
    raw = Result()
    retained: list[object] = []

    def publish(reference: object, *_: object, **__: object) -> LRAProduct:
        retained.append(reference)
        return LRAProduct(tmp_path / "out", "0" * 64, "1" * 64)

    with (
        patch.object(benchmark, "load_engine", return_value=engine),
        patch.object(benchmark, "validate_engine_configuration"),
        patch.object(benchmark, "reconstruct", return_value=raw) as compute,
        patch.object(benchmark, "publish_result", side_effect=publish) as writer,
    ):
        result = benchmark.benchmark_lra_request(
            payload, input_root=tmp_path, destination=tmp_path / "out", repeats=3
        )
    assert compute.call_count == 3 and writer.call_count == 1
    assert retained[0] is not raw
    assert result["repeats"] == 3 and len(result["repeated_call_seconds"]) == 2
    raw.table.iloc[0, 0] = 0.9
    assert isinstance(retained[0], Result)
    assert retained[0].table.iloc[0, 0] == 0.5


def test_comparison_retains_nonfinite_masks_and_exact_dtype_axes() -> None:
    reference = Result(samples=np.array([[float("nan"), float("inf"), -float("inf")]]))
    benchmark._same_result(reference, deepcopy(reference))
    changed = deepcopy(reference)
    changed.samples[0, 0] = 0
    with pytest.raises(AssertionError):
        benchmark._same_result(reference, changed)
    changed = deepcopy(reference)
    changed.samples = changed.samples.astype(np.float32)
    with pytest.raises(AssertionError):
        benchmark._same_result(reference, changed)


def test_each_adapter_call_constructs_new_inputs_from_immutable_request(
    tmp_path: Path,
) -> None:
    engine = load_engine()
    payload = request_fixture(tmp_path)
    original = deepcopy(payload)
    observed: list[tuple[int, int]] = []
    raw = Result()

    def calculate(table: pd.DataFrame, parameters: pd.DataFrame, config: Any) -> Result:
        count = table.iloc[0, 1]
        assert isinstance(count, (int, np.integer))
        observed.append((int(count), config.seed))
        table.iloc[0, 1] = 999
        parameters.iloc[0, 1] = 999
        return raw

    with (
        patch.object(benchmark, "load_engine", return_value=engine),
        patch.object(engine.api, "run_reveals", side_effect=calculate),
        patch.object(
            benchmark,
            "publish_result",
            return_value=LRAProduct(tmp_path / "out", "0" * 64, "1" * 64),
        ),
    ):
        benchmark.benchmark_lra_request(
            payload, input_root=tmp_path, destination=tmp_path / "out", repeats=3
        )
    assert observed == [(60, 7)] * 3
    assert payload == original


def test_auxiliary_manifest_key_is_normal_public_data_not_a_run_manifest() -> None:
    from bijux_pollenomics_lra.models.results import LoveResult
    from bijux_pollenomics_lra.provenance.manifest import RunManifest

    reference = LoveResult(
        method="analytical",
        cover={"mean": pd.DataFrame({"Alnus": [0.5]})},
        manifest=RunManifest(
            algorithm="controlled", parameters={}, inputs={}, stochastic=False, seed=7
        ),
        auxiliary={"manifest": pd.DataFrame({"diagnostic": [0.25, 0.75]})},
    )
    actual = deepcopy(reference)
    benchmark._same_result(reference, actual)
    actual.auxiliary["manifest"].iloc[0, 0] = 0.5
    with pytest.raises(AssertionError):
        benchmark._same_result(reference, actual)
