"""Configuration seeds must execute without changing accepted entropy."""

import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from bijux_pollenomics_lra.models.configuration import (
    LoveConfig,
    LRAConfig,
    RegionalDrawLoveConfig,
    RevealsConfig,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.resources.examples import load_love_example
from bijux_pollenomics_lra.workflows.paired import run_lra
from bijux_pollenomics_lra.workflows.regional import run_reveals


def config(kind: str, seed: Any) -> Any:
    if kind == "reveals":
        return RevealsConfig("lake", 300, iterations=4, seed=seed)
    if kind == "love":
        return LoveConfig("analytical", "lake", 300, 12.9, 10, repeats=2, seed=seed)
    if kind == "regional_draws":
        return RegionalDrawLoveConfig(12.9, 10, repeats=2, seed=seed)
    return LRAConfig(
        RevealsConfig("lake", 300, iterations=4),
        LoveConfig("analytical", "lake", 300, 12.9, 10, repeats=2),
        seed=seed,
    )


@pytest.mark.parametrize("kind", ["reveals", "love", "regional_draws", "paired"])
@pytest.mark.parametrize("seed", [42.0, "42", "42.0", [42.0], np.array(42)])
def test_previously_failing_seed_is_normalized_to_exact_integer(
    kind: str, seed: Any
) -> None:
    result = config(kind, seed)
    assert type(result.seed) is int and result.seed == 42
    assert result.as_dict()["seed"] == 42


@pytest.mark.parametrize("kind", ["reveals", "love", "regional_draws", "paired"])
@pytest.mark.parametrize("seed", [[42], (42,), np.array([42]), ["42"]])
def test_working_singleton_sequence_preserves_seed_representation(
    kind: str, seed: Any
) -> None:
    result = config(kind, seed)
    assert result.seed is seed
    assert result.as_dict()["seed"] is seed
    np.testing.assert_array_equal(
        np.random.SeedSequence(result.seed).generate_state(8),
        np.random.SeedSequence(seed).generate_state(8),
    )


@pytest.mark.parametrize("kind", ["reveals", "love", "regional_draws", "paired"])
@pytest.mark.parametrize("seed", [2**53 + 1, np.int64(2**53 + 1), "9007199254740993"])
def test_large_integer_entropy_stays_exact(kind: str, seed: Any) -> None:
    result = config(kind, seed)
    assert int(result.seed) == 2**53 + 1
    assert int(result.as_dict()["seed"]) == 2**53 + 1
    np.testing.assert_array_equal(
        np.random.SeedSequence(result.seed).generate_state(8),
        np.random.SeedSequence(2**53 + 1).generate_state(8),
    )


@pytest.mark.parametrize("kind", ["reveals", "love", "regional_draws", "paired"])
@pytest.mark.parametrize(
    "seed", [True, -1, 42.5, float("nan"), "42.00000000000000000001", [1, 2]]
)
def test_invalid_or_inexact_seed_refuses_early(kind: str, seed: Any) -> None:
    with pytest.raises(ValidationError, match="seed"):
        config(kind, seed)


def test_normalized_seed_executes_and_is_saved_as_used(tmp_path: Path) -> None:
    _, regional, inputs, _ = load_love_example()
    configuration = RevealsConfig(
        "lake",
        300,
        iterations=4,
        stochastic=True,
        retain_samples=True,
        seed=cast(Any, "9007199254740993"),
    )
    first = run_reveals(regional, inputs["ppes"], configuration)
    second = run_reveals(regional, inputs["ppes"], configuration)
    np.testing.assert_array_equal(first.samples, second.samples)
    path = first.manifest.write(tmp_path / "manifest.json")
    saved = json.loads(path.read_text())
    assert saved["seed"] == saved["parameters"]["seed"] == 2**53 + 1


def test_working_singleton_sequence_runs_with_unchanged_manifest(
    tmp_path: Path,
) -> None:
    local, regional, inputs, rings = load_love_example()
    configuration = config("paired", [42])
    first = run_lra(local, regional, inputs["ppes"], rings, configuration)
    second = run_lra(local, regional, inputs["ppes"], rings, configuration)
    assert first.manifest.as_dict()["seed"] == [42]
    assert first.manifest.as_dict()["parameters"]["seed"] == [42]
    assert first.regional.manifest.seed == second.regional.manifest.seed
    assert first.local.manifest.seed == second.local.manifest.seed
    np.testing.assert_array_equal(
        first.regional.table.to_numpy(), second.regional.table.to_numpy()
    )
    np.testing.assert_array_equal(
        first.local.cover["mean"].to_numpy(), second.local.cover["mean"].to_numpy()
    )


@pytest.mark.parametrize("seed", [42.0, "42", [42]])
def test_supported_seed_forms_match_integer_workflow_draws(seed: Any) -> None:
    _, regional, inputs, _ = load_love_example()
    reference = run_reveals(
        regional,
        inputs["ppes"],
        RevealsConfig(
            "lake", 300, iterations=4, stochastic=True, retain_samples=True, seed=42
        ),
    )
    actual = run_reveals(
        regional,
        inputs["ppes"],
        RevealsConfig(
            "lake", 300, iterations=4, stochastic=True, retain_samples=True, seed=seed
        ),
    )
    np.testing.assert_array_equal(actual.samples, reference.samples)
    expected_seed = seed if isinstance(seed, list) else 42
    assert actual.manifest.as_dict()["seed"] == expected_seed


def test_mutable_legacy_seed_is_caller_owned() -> None:
    seed = [42]
    configuration = config("reveals", seed)
    seed[0] = -1
    assert configuration.seed is seed and configuration.as_dict()["seed"] == [-1]
    with pytest.raises(ValueError):
        np.random.SeedSequence(configuration.seed)


def test_fraction_and_decimal_seed_normalization_is_exact() -> None:
    from decimal import Decimal
    from fractions import Fraction

    assert config("reveals", Fraction(84, 2)).seed == 42
    assert config("reveals", Decimal("9007199254740993")).seed == 2**53 + 1
    with pytest.raises(ValidationError, match="seed"):
        config("reveals", Fraction(90071992547409931, 10))


def test_numpy_large_seed_provenance_is_exact(tmp_path: Path) -> None:
    _, regional, inputs, _ = load_love_example()
    configuration = RevealsConfig(
        "lake", 300, iterations=2, stochastic=True, seed=cast(Any, np.int64(2**53 + 1))
    )
    result = run_reveals(regional, inputs["ppes"], configuration)
    payload = json.loads(
        result.manifest.write(tmp_path / "numpy-seed.json").read_text()
    )
    assert payload["seed"] == payload["parameters"]["seed"] == 2**53 + 1


def test_float_coercible_object_without_exact_integer_refuses() -> None:
    class FloatOnly:
        def __float__(self) -> float:
            return 42.0

    with pytest.raises(ValidationError, match="seed"):
        config("reveals", FloatOnly())
