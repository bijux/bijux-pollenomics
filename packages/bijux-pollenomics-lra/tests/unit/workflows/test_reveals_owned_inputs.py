"""Opt-in REVEALS input capture binds consumed values to legacy hashes."""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd
import pytest

from bijux_pollenomics_lra.api import RevealsConfig, ValidationError, run_reveals
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows import regional


def test_snapshot_is_used_for_calculation_and_manifest_after_caller_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, pollen, inputs, _ = load_love_example()
    params = inputs["ppes"]
    pollen.index = pd.Index(["source"], dtype=object)
    pollen_draws = np.tile(
        pollen.iloc[:, 1:].to_numpy(dtype=float)[:, None, :], (1, 2, 1)
    )
    ppe_draws = np.tile(params["ppe"].to_numpy(dtype=float)[None, None, :], (1, 2, 1))
    seed = [42]
    config = RevealsConfig(
        "lake", 300, iterations=2, stochastic=False, seed=cast(Any, seed)
    )
    prior_hashes = {
        "pollen": sha256_object(pollen),
        "params": sha256_object(params),
        "pollen_draws": sha256_object(pollen_draws),
        "ppe_draws": sha256_object(ppe_draws),
    }
    expected = run_reveals(
        pollen, params, config, pollen_draws=pollen_draws, ppe_draws=ppe_draws
    )
    expected_table = expected.table.copy(deep=True)
    expected_table.index = expected.table.index.copy(deep=True)
    expected_table.columns = expected.table.columns.copy(deep=True)
    original = cast(Any, regional)._reconstruct_frame

    def mutate_then_reconstruct(*args: Any, **kwargs: Any) -> object:
        pollen.iloc[0, 1] = 12345
        cast(Any, pollen.index)._values[0] = "changed"
        cast(Any, pollen.columns)._values[0] = "changed coordinate"
        params.iloc[0, params.columns.get_loc("ppe")] = 999
        pollen_draws[0, 0, 0] += 1
        ppe_draws[0, 0, 0] *= 2
        seed[0] = 99
        return original(*args, **kwargs)

    monkeypatch.setattr(regional, "_reconstruct_frame", mutate_then_reconstruct)
    actual = run_reveals(
        pollen,
        params,
        config,
        pollen_draws=pollen_draws,
        ppe_draws=ppe_draws,
        input_ownership="snapshot",
    )
    pd.testing.assert_frame_equal(actual.table, expected_table)
    assert actual.manifest.inputs == prior_hashes
    assert cast(Any, actual.manifest.seed) == [42]


def test_snapshot_refuses_mutable_custom_label_but_default_keeps_support() -> None:
    class MutableLabel:
        def __str__(self) -> str:
            return "source"

    _, pollen, inputs, _ = load_love_example()
    pollen.index = pd.Index([MutableLabel()], dtype=object)
    config = RevealsConfig("lake", 300, iterations=2, stochastic=False)
    assert run_reveals(pollen, inputs["ppes"], config).manifest.inputs["pollen"]
    with pytest.raises(ValidationError, match="snapshot"):
        run_reveals(pollen, inputs["ppes"], config, input_ownership="snapshot")


def test_snapshot_preserves_stochastic_result_and_legacy_input_hashes() -> None:
    _, pollen, inputs, _ = load_love_example()
    config = RevealsConfig(
        "lake",
        300,
        iterations=4,
        stochastic=True,
        retain_samples=True,
        seed=cast(Any, [42]),
    )
    first = run_reveals(pollen, inputs["ppes"], config)
    second = run_reveals(pollen, inputs["ppes"], config, input_ownership="snapshot")
    pd.testing.assert_frame_equal(first.table, second.table, check_exact=True)
    np.testing.assert_array_equal(first.samples, second.samples)
    assert first.manifest.inputs == second.manifest.inputs
    assert "input_ownership" not in first.manifest.parameters
    assert second.manifest.parameters["input_ownership"] == "snapshot"
    assert cast(Any, first.manifest.seed) == cast(Any, second.manifest.seed) == [42]


@pytest.mark.parametrize(
    "kind", ["object_array", "masked_array", "cyclic", "invalid_ownership"]
)
def test_snapshot_refuses_unsupported_draws_and_unknown_policy(kind: str) -> None:
    _, pollen, inputs, _ = load_love_example()
    config = RevealsConfig("lake", 300, iterations=2, stochastic=False)
    draws: object
    if kind == "object_array":
        draws = np.array([[[1]]], dtype=object)
    elif kind == "masked_array":
        draws = np.ma.array([[[1]]], mask=False)
    elif kind == "cyclic":
        sequence: list[object] = []
        sequence.append(sequence)
        draws = sequence
    else:
        draws = None
    with pytest.raises(ValidationError, match="ownership|snapshot"):
        run_reveals(
            pollen,
            inputs["ppes"],
            config,
            ppe_draws=draws,
            input_ownership="unknown" if kind == "invalid_ownership" else "snapshot",
        )


@pytest.mark.parametrize("ownership", ["borrowed", "snapshot"])
def test_mutation_after_reconstruction_changes_only_borrowed_input_hash(
    ownership: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, pollen, inputs, _ = load_love_example()
    params = inputs["ppes"]
    config = RevealsConfig("lake", 300, iterations=2, stochastic=False)
    expected = run_reveals(pollen, params, config)
    before = sha256_object(pollen)
    original = cast(Any, regional)._reconstruct_frame

    def mutate_after_reconstruct(*args: Any, **kwargs: Any) -> object:
        computed = original(*args, **kwargs)
        pollen.iloc[0, 1] = 12345
        return computed

    monkeypatch.setattr(regional, "_reconstruct_frame", mutate_after_reconstruct)
    actual = run_reveals(pollen, params, config, input_ownership=ownership)
    pd.testing.assert_frame_equal(actual.table, expected.table, check_exact=True)
    after = sha256_object(pollen)
    assert before != after
    assert actual.manifest.inputs["pollen"] == (
        before if ownership == "snapshot" else after
    )


def test_snapshot_detaches_nested_draws_and_numpy_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, pollen, inputs, _ = load_love_example()
    seed = np.array([42], dtype=np.int64)
    config = RevealsConfig(
        "lake", 300, iterations=2, stochastic=False, seed=cast(Any, seed)
    )
    draws = np.tile(
        pollen.iloc[:, 1:].to_numpy(dtype=float)[:, None, :], (1, 2, 1)
    ).tolist()
    before_hash = sha256_object(draws)
    expected = run_reveals(pollen, inputs["ppes"], config, pollen_draws=draws)
    original = cast(Any, regional)._reconstruct_frame

    def mutate_then_reconstruct(*args: Any, **kwargs: Any) -> object:
        draws[0][0][0] += 1
        seed[0] = 99
        return original(*args, **kwargs)

    monkeypatch.setattr(regional, "_reconstruct_frame", mutate_then_reconstruct)
    actual = run_reveals(
        pollen, inputs["ppes"], config, pollen_draws=draws, input_ownership="snapshot"
    )
    pd.testing.assert_frame_equal(actual.table, expected.table, check_exact=True)
    assert actual.manifest.inputs["pollen_draws"] == before_hash
    np.testing.assert_array_equal(actual.manifest.seed, [42])


def test_unhashable_ownership_is_validation_error() -> None:
    _, pollen, inputs, _ = load_love_example()
    config = RevealsConfig("lake", 300, iterations=2, stochastic=False)
    with pytest.raises(ValidationError, match="ownership"):
        run_reveals(pollen, inputs["ppes"], config, input_ownership=cast(Any, []))


def test_snapshot_detaches_range_index_and_column_storage() -> None:
    from bijux_pollenomics_lra.workflows.reveals_input_capture import (
        capture_reveals_inputs,
    )

    _, pollen, inputs, _ = load_love_example()
    pollen.index = pd.RangeIndex(len(pollen))
    config = RevealsConfig("lake", 300, iterations=2, stochastic=False)
    captured, captured_params, _, _, _ = capture_reveals_inputs(
        pollen, inputs["ppes"], config, None, None
    )
    assert not np.shares_memory(pollen.index.values, captured.index.values)
    assert not np.shares_memory(pollen.columns.values, captured.columns.values)
    assert not np.shares_memory(
        inputs["ppes"].columns.values, captured_params.columns.values
    )
