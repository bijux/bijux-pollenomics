"""Independent draw-order and ownership checks for analytical preparation."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from bijux_pollenomics_lra.models.validation import normalise_parameters
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr
from bijux_pollenomics_lra.reconstruction.preparation import prepare_analytical_inputs
from bijux_pollenomics_lra.resources.examples import load_love_example


def test_prepared_arrays_own_labeled_inputs_and_are_read_only() -> None:
    local, regional, params, _ = load_love_example()
    table = normalise_parameters(params["ppes"], list(local.columns[1:]))
    prepared = prepare_analytical_inputs(
        local,
        regional,
        table,
        params,
        stochastic=True,
        needs_regional_deposition=True,
    )
    expected = prepared.local_counts.copy()
    local.iloc[0, 1:] = 0
    regional.iloc[0, 1:] = 0
    table.loc[:, "ppe"] = 99
    np.testing.assert_array_equal(prepared.local_counts, expected)
    assert prepared.regional_counts.sum() > 0
    assert not np.any(prepared.ppe_means == 99)
    for values in (
        prepared.local_counts,
        prepared.regional_counts,
        prepared.ppe_means,
        prepared.ppe_errors,
        prepared.regional_deposition,
    ):
        assert values is not None
        assert not values.flags.writeable
        with pytest.raises(ValueError):
            values[0] = 1


@pytest.mark.parametrize(
    "supplied_alpha,supplied_counts",
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_supplied_draws_preserve_ring_rng_order_and_unbounded_equation(
    supplied_alpha: bool,
    supplied_counts: bool,
) -> None:
    local, regional, params, rings = load_love_example()
    params = {**params, "error": True}
    table = normalise_parameters(params["ppes"], list(local.columns[1:]))
    means = table["ppe"].to_numpy()
    errors = table["ppe.error"].to_numpy()
    counts = local.iloc[0, 1:].to_numpy(dtype=float)
    regional_draws = np.full((2, 10), 0.1)
    alpha_draws = np.broadcast_to(means, (2, 10, 10)).copy()
    count_draws = np.broadcast_to(counts, (2, 10, 10)).copy()
    generator = np.random.default_rng(812)
    result = LOVEr(
        local,
        regional,
        params,
        rings,
        10,
        repeats=2,
        rng=generator,
        stochastic=True,
        regional_cover_draws=regional_draws,
        local_ppe_draws=alpha_draws if supplied_alpha else None,
        local_count_draws=count_draws if supplied_counts else None,
        return_samples=True,
    )
    expected_rng = np.random.default_rng(812)
    expected = np.full((2, 10, 10), np.nan)
    for repeat in range(2):
        for ring in range(10):
            if not result["valid_ring"].iloc[ring]:
                continue
            alpha = means.copy()
            if not supplied_alpha:
                while True:
                    alpha = expected_rng.normal(means, errors)
                    if np.all(alpha >= 0):
                        break
            realization = (
                counts
                if supplied_counts
                else expected_rng.multinomial(
                    int(round(counts.sum())), counts / counts.sum()
                )
            )
            regional_cover = regional_draws[repeat]
            correction = (
                regional_cover
                * result["Kreg"].iloc[ring].to_numpy()
                / np.sum(regional_cover * result["Kloc"].iloc[ring].to_numpy())
            )
            weighted = realization / alpha
            expected[repeat, ring] = (
                weighted / weighted.sum() * (1 + correction.sum()) - correction
            )
    np.testing.assert_array_equal(result["samples"], expected)
    assert generator.bit_generator.state == expected_rng.bit_generator.state
    np.testing.assert_array_equal(alpha_draws, np.broadcast_to(means, (2, 10, 10)))
    np.testing.assert_array_equal(count_draws, np.broadcast_to(counts, (2, 10, 10)))


def test_local_error_disabled_preserves_regional_random_draws() -> None:
    local, regional, params, rings = load_love_example()
    params = {**params, "error": False}
    table = normalise_parameters(params["ppes"], list(local.columns[1:]))
    means, errors = table["ppe"].to_numpy(), table["ppe.error"].to_numpy()
    counts = regional.iloc[0, 1:].to_numpy(dtype=float)
    generator = np.random.default_rng(51)
    before = copy.deepcopy(generator.bit_generator.state)
    LOVEr(local, regional, params, rings, 10, repeats=2, rng=generator, stochastic=True)
    expected_rng = np.random.default_rng(51)
    for _ in range(2):
        while True:
            alpha = expected_rng.normal(means, errors)
            if np.all(alpha >= 0):
                break
        expected_rng.multinomial(
            int(round(counts.sum())), counts / counts.sum(), size=1
        )
    assert generator.bit_generator.state != before
    assert generator.bit_generator.state == expected_rng.bit_generator.state
