"""Fixed-start and exact regional-stage handoff on invented temporal requests."""

from __future__ import annotations

from copy import deepcopy
import csv
from dataclasses import make_dataclass
import io
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)

ROOT = Path.cwd()
PREFIX = ROOT / "docs/report/pollen-reconstruction/author-lra-constrained"
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT",
    ROOT / "reports/science/author-love-temporal-fixed-start/source",
)
REPLAY = runpy.run_path(str(SOURCE / "replay.py"), run_name="bijux_fixed_temporal_test")
TRAINING = runpy.run_path(
    str(SOURCE / "training.py"), run_name="bijux_fixed_training_test"
)
REGIONAL = runpy.run_path(
    str(SOURCE / "regional.py"), run_name="bijux_fixed_regional_test"
)
HELPER = runpy.run_path(
    str(PREFIX / "optimizer-start-sensitivity/replay.py"),
    run_name="bijux_fixed_start_grid_test",
)
ORIGINAL = runpy.run_path(
    str(PREFIX / "optimizer-gradient/replay.py"),
    run_name="bijux_original_fixed_math_test",
)
MATH = runpy.run_path(
    str(PREFIX / "development-fold/training.py"), run_name="bijux_fixed_gate_test"
)
TEMPORAL = runpy.run_path(
    str(PREFIX / "temporal-development/replay.py"), run_name="bijux_fixed_io_test"
)
TOPOLOGY = runpy.run_path(
    str(PREFIX / "temporal-development/topology.py"),
    run_name="bijux_fixed_topology_test",
)
FIXTURE = runpy.run_path(
    str(
        ROOT
        / "packages/bijux-pollenomics-dev/tests/source_completion/pollen_reconstruction/test_author_temporal_development.py"
    )
)


@pytest.mark.parametrize("mass", [0.99999, 1.0, 1.00001])
def test_original_start_vectors_preserve_raw_regional_mass(mass: float) -> None:
    observed = np.asarray([0.25, 0.75, *([0.0] * 28)])
    regional = np.asarray([0.4, mass - 0.4, *([0.0] * 28)])
    raw = regional.tobytes()
    starts = HELPER["_starts"](observed, regional)
    assert len(starts) == len({name for name, _ in starts}) == 32
    assert regional.tobytes() == raw
    assert np.array_equal(starts[0][1], 0.5 * np.full(30, 1 / 30) + 0.5 * observed)
    assert np.array_equal(
        starts[1][1], 0.5 * np.full(30, 1 / 30) + 0.5 * regional / regional.sum()
    )
    assert all(
        np.all(value > 0) and abs(float(value.sum()) - 1) < 1e-12 for _, value in starts
    )


def exercise_attempts(
    optimizer: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    original = {**ORIGINAL, "optimize_box": optimizer}
    events: list[dict[str, Any]] = []
    rows = TRAINING["attempts"](
        HELPER,
        original,
        MATH,
        SimpleNamespace(item_id="invented", request_sha256="a" * 64),
        {"rings": [{"outer_m": 500}, {"outer_m": 1000}, {"outer_m": 10000}]},
        np.asarray([0.4, 0.59999, *([0.0] * 28)]),
        np.ones(30),
        np.asarray([np.full(30, 0.1), np.full(30, 0.2), np.full(30, 0.3)]),
        np.asarray([0.5, 0.25, 0.75]),
        np.full(30, 1 / 30),
        3618983171,
        1,
        events.append,
    )
    return rows, events


def test_all_starts_use_exact_objective_budgets_and_native_results() -> None:
    calls = []

    def optimizer(objective: Any, lower: Any, upper: Any, **kwargs: Any) -> Any:
        assert np.array_equal(lower, np.zeros(30)) and np.array_equal(
            upper, np.ones(30)
        )
        assert {
            key: kwargs[key]
            for key in ("maxiter", "tolerance", "max_evaluations", "rng")
        } == {
            "maxiter": 300,
            "tolerance": 1e-8,
            "max_evaluations": 16000,
            "rng": 3618983171,
        }
        adapter = kwargs["optimizer"]
        x = adapter.start.copy()
        assert np.isfinite(adapter.jacobian(x)).all()
        calls.append(x)
        return ORIGINAL["OptimizationResult"](
            x=x,
            fun=objective(x),
            nit=1,
            nfev=1,
            success=len(calls) != 1,
            message="invented line-search refusal"
            if len(calls) == 1
            else "invented success",
            algorithm="invented-result-original-objective",
        )

    rows, events = exercise_attempts(optimizer)
    assert len(calls) == len(rows) == 32 and len(events) == 64
    assert sum(row["accepted"] for row in rows) == 31
    assert rows[0]["result"]["success"] is False and rows[0]["accepted"] is False
    assert all(row["observed_calls"] == {"objective": 1, "jacobian": 1} for row in rows)
    assert [row["event"] for row in events] == [
        value for _ in range(32) for value in ("attempt_started", "attempt_completed")
    ]


def test_unknown_optimizer_fault_is_fatal_and_durably_declared() -> None:
    error = ValueError("invented source invariant failure")
    events: list[dict[str, Any]] = []

    def fail(*_args: Any, **_kwargs: Any) -> Any:
        raise error

    original = {**ORIGINAL, "optimize_box": fail}
    with pytest.raises(ValueError) as caught:
        TRAINING["attempts"](
            HELPER,
            original,
            MATH,
            SimpleNamespace(item_id="invented", request_sha256="a" * 64),
            {"rings": [{"outer_m": 500}, {"outer_m": 1000}, {"outer_m": 10000}]},
            np.full(30, 1 / 30),
            np.ones(30),
            np.full((3, 30), 0.1),
            np.ones(3),
            np.full(30, 1 / 30),
            3618983171,
            0,
            events.append,
        )
    assert caught.value is error
    assert [row["event"] for row in events] == ["attempt_started", "attempt_failed"]
    assert events[-1]["error_type"] == "ValueError"


def regional_table(mutation: str | None = None) -> tuple[bytes, list[str]]:
    taxa = ["Taxon" + str(index) for index in range(30)]
    values = [40.0, 59.999, *([0.0] * 28)]
    row: dict[str, Any] = {
        "Distance.weighting": "gpm neutral",
        "Basin.type": "lake",
        "coordinate": 1000,
    }
    for taxon, value in zip(taxa, values, strict=True):
        row.update({taxon + "." + k: value for k in ("mean", "median", "q10", "q90")})
        row[taxon + ".sd"] = 0
    if mutation == "missing-taxon":
        row.pop(taxa[-1] + ".mean")
    elif mutation == "nonidentical-draws":
        row[taxa[0] + ".sd"] = 0.1
    elif mutation == "unrounded":
        row[taxa[0] + ".mean"] = 40.00001
    elif mutation == "coordinate":
        row["coordinate"] = 2000
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return stream.getvalue().encode(), taxa


def test_saved_deterministic_percent_handoff_keeps_rounding_discrepancy() -> None:
    raw, taxa = regional_table()
    values = REGIONAL["saved_fraction"](raw, taxa, 1000)
    assert values == [0.4, 0.59999, *([0.0] * 28)]
    assert sum(values) != 1
    payload: dict[str, Any] = {
        "taxa": taxa,
        "parameters": [],
        "regional": {"basin": "invented"},
        "local": {"counts": [1]},
        "configuration": {"seed": 7, "reveals": {"stochastic": False}},
    }
    changed = deepcopy(payload)
    changed["local"] = {"counts": [99]}
    assert REGIONAL["stage_identity"](payload) == REGIONAL["stage_identity"](changed)
    changed["regional"] = {"basin": "foreign"}
    assert REGIONAL["stage_identity"](payload) != REGIONAL["stage_identity"](changed)
    changed["configuration"]["reveals"]["stochastic"] = True
    with pytest.raises(ValueError):
        REGIONAL["stage_identity"](changed)


@pytest.mark.parametrize(
    "mutation", ["missing-taxon", "nonidentical-draws", "unrounded", "coordinate"]
)
def test_incompatible_saved_regional_stage_refuses(mutation: str) -> None:
    raw, taxa = regional_table(mutation)
    with pytest.raises(ValueError):
        REGIONAL["saved_fraction"](raw, taxa, 1000)


@pytest.mark.parametrize("window", [4, 6])
def test_full_window_mixed_refusals_and_scoring_after_complete_freeze(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    window: int,
) -> None:
    prepared = tmp_path / "inputs"
    experiment, profile = FIXTURE["fixture"](prepared, window)
    spec = SourceExperimentSpec(experiment)
    top = TOPOLOGY["build"](spec, prepared, window, profile)
    composition = dict.fromkeys(experiment["request_template"]["taxa"], 1 / 30)
    product = {
        "regional_cover": [0.4, 0.59999, *([0.0] * 28)],
        "selections": [
            {"composition": composition},
            {"composition": composition, "selected_attempt_sha256": "a" * 64},
        ],
    }
    products = {key: {**product, "request_sha256": key} for key in top["numeric"]}

    def predict(
        one: Any, fold: Any, target: Any, fits: Any, *_args: Any, **_kwargs: Any
    ) -> Any:
        assert (
            len(fits.compositions) == len(spec.sites) - 2
            and fits.regional_cover[1] == 0.59999
        )
        baseline = one.baselines[0]
        if baseline == "nearest_site":
            raise ValidationRefusal(
                "forward_model_refused",
                "Forward deposition has nonfinite or zero total mass",
            )
        return [
            {
                "fold_id": fold.fold_id,
                "record_id": target.record.record_id,
                "baseline": baseline,
                "bin_id": "author-TW" + str(window),
                "pollen_fraction": composition,
            }
        ], {}

    namespace = TRAINING["predictions"].__globals__
    monkeypatch.setitem(namespace, "predict_fold", predict)
    slots = TRAINING["predictions"](spec, top, products, prepared, experiment)
    assert len(slots) == 3 * len(spec.sites)
    assert sum(row["status"] == "predicted" for row in slots) == 2 * len(spec.sites)
    output = tmp_path / "result"
    output.mkdir()
    existing = runpy.run_path(str(PREFIX / "cohort-development/replay.py"))
    real_outcome = existing["outcome_counts"]
    accesses = []

    def outcome(*args: Any, **kwargs: Any) -> Any:
        assert len(
            json.loads((output / "prediction-freeze.json").read_bytes())["slots"]
        ) == len(slots)
        assert (output / "outcome-access.jsonl").stat().st_size > 0
        accesses.append(True)
        return real_outcome(*args, **kwargs)

    existing["outcome_counts"] = outcome
    monkeypatch.setitem(
        REPLAY["score"].__globals__,
        "runpy",
        SimpleNamespace(run_path=lambda *_args, **_kwargs: existing),
    )
    inputs = [
        REPLAY["supplied"](p, __import__("hashlib").sha256(p.read_bytes()).hexdigest())
        for p in prepared.iterdir()
    ]
    _, scores = REPLAY["score"](
        tmp_path, prepared, output, spec, TEMPORAL, top, slots, {}, inputs
    )
    assert len(accesses) == len(spec.sites) and len(scores) == 2 * len(spec.sites)
    products[next(iter(products))] = {
        **product,
        "request_sha256": next(iter(products)),
        "selections": [None, None],
    }
    refused = TRAINING["predictions"](spec, top, products, prepared, experiment)
    assert any(
        row.get("reason_code") == "training_ring_has_no_accepted_start"
        for row in refused
    )
    failure = ValidationRefusal(
        "engine_identity_changed", "invented infrastructure error"
    )

    def fail(*_args: Any, **_kwargs: Any) -> Any:
        raise failure

    monkeypatch.setitem(namespace, "predict_fold", fail)
    with pytest.raises(ValidationRefusal) as caught:
        TRAINING["predictions"](
            spec,
            top,
            {k: {**product, "request_sha256": k} for k in products},
            prepared,
            experiment,
        )
    assert caught.value is failure


def test_saved_objective_inputs_are_exact_existing_arrays() -> None:
    taxa = ["invented:" + str(i) for i in range(30)]
    counts = [3, 7, *([0] * 28)]
    payload = {
        "taxa": taxa,
        "rings": [{"outer_m": x} for x in (500, 1000, 10000)],
        "method_profile": {"love": "ring-taxon-preserving"},
        "local": {"samples": [{"counts": counts}]},
    }
    kernels = np.asarray([np.full(30, x) for x in (0.1, 0.2, 0.3)])
    ppe = np.arange(1, 31, dtype=float)
    rings = pd.DataFrame({"ring": [100, 200, 400], "terrestrial": [50, 50, 300]})
    fields = (
        "max_ring",
        "repeats",
        "optimizer_iterations",
        "optimizer_max_evaluations",
        "optimizer_tolerance",
        "seed",
        "stochastic",
    )
    config = make_dataclass("InventedLoveConfig", [(key, Any) for key in fields])
    love = config(2, 1, 300, 16000, 1e-8, 7, False)
    calls = {"kernel": 0, "optimizer": 0}

    def kernel(*_args: Any) -> Any:
        calls["kernel"] += 1
        return pd.DataFrame(kernels)

    def optimizer(objective: Any, *_args: Any, **kwargs: Any) -> Any:
        calls["optimizer"] += 1
        start = kwargs["optimizer"].start.copy()
        return ORIGINAL["OptimizationResult"](
            x=start,
            fun=objective(start),
            nit=1,
            nfev=1,
            success=calls["optimizer"] != 1,
            message="invented",
            algorithm="invented-original-objective",
        )

    original = {
        **ORIGINAL,
        "validate_lra_inputs": lambda *_args, **_kwargs: SimpleNamespace(
            payload=lambda: payload
        ),
        "load_engine": lambda **_kwargs: None,
        "required_capability_for_profile": lambda _value: "invented",
        "_configuration": lambda *_args: (
            SimpleNamespace(iterations=2, stochastic=False),
            love,
            SimpleNamespace(seed=7),
        ),
        "_tables": lambda _payload: (None, pd.DataFrame({"ppe": ppe}), rings),
        "_prepare_love_params": lambda *_args: None,
        "calK": kernel,
        "optimize_box": optimizer,
    }
    events: list[dict[str, Any]] = []
    result, rows = TRAINING["fit"](
        original,
        HELPER,
        MATH,
        SimpleNamespace(
            item_id="invented", request_sha256="a" * 64, payload=lambda: payload
        ),
        ROOT,
        [0.4, 0.59999, *([0.0] * 28)],
        events.append,
        TOPOLOGY["digest"],
    )
    saved = result["objective_inputs"]
    assert saved == {
        "taxa": taxa,
        "rings": payload["rings"],
        "method_profile": payload["method_profile"],
        "native_kernels": kernels.tolist(),
        "terrestrial_fractions": [0.5, 0.25, 0.75],
        "ppe": ppe.tolist(),
        "observed_local_fractions": [0.3, 0.7, *([0.0] * 28)],
        "local_counts": counts,
    }
    assert all(type(value) is int for value in saved["local_counts"])
    assert calls == {"kernel": 1, "optimizer": 64}
    assert len(rows) == 64 and len(events) == 128
    assert sum(row["accepted"] for row in rows) == 63
    assert result["regional_cover"] == [0.4, 0.59999, *([0.0] * 28)]
    assert all(row["accepted"] >= 31 for row in result["selections"])
