"""Check source-rate semantics and complete conditional scoring populations."""

from __future__ import annotations

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.posterior import (
    physical_ages,
    score_draws,
)


def test_innovations_are_transformed_before_age_integration() -> None:
    states = np.asarray([[0, 2, 10, 0.5], [-52, 2, 10, 0.5]], dtype=float)
    actual = physical_ages(states, np.asarray([0, 2.5, 5, 10]), 0, 5)
    np.testing.assert_array_equal(actual, [[0, 15, 30, 80], [-52, -37, -22, 28]])


def test_native_section_support_is_distinct_from_requested_sample_range() -> None:
    states = np.asarray([[0, *([1] * 51), 0.3]], dtype=float)
    actual = physical_ages(states, np.asarray([648, 896, 903]), 648, 5)
    np.testing.assert_array_equal(actual, [[0, 248, 255]])
    with pytest.raises(ValueError, match="beyond the saved model"):
        physical_ages(states, np.asarray([903.1]), 648, 5)


@pytest.mark.parametrize("memory", [0, 1, -0.1, np.nan])
def test_invalid_native_memory_is_refused(memory: float) -> None:
    with pytest.raises(ValueError, match="support|Finite"):
        physical_ages(np.asarray([[0, 2, 10, memory]]), np.asarray([0]), 0, 5)


def test_shared_draws_preserve_empty_bins_and_signed_ages() -> None:
    ages = np.asarray([[0, 500], [499, 499], [-1, 500]], dtype=float)
    counts = np.asarray([[1, 0], [0, 1]], dtype=np.int64)
    predictions = np.asarray([[[1, 0], [0, 1]], [[0, 1], [1, 0]]], dtype=float)
    scores, population, support = score_draws(ages, counts, predictions, (0, 1))
    np.testing.assert_array_equal(scores[0], [0, 1])
    assert np.all(np.isnan(scores[1:]))
    np.testing.assert_array_equal(
        support, [[[1, 1], [1, 1]], [[2, 2], [0, 0]], [[0, 0], [1, 1]]]
    )
    assert population == {
        "requested_draws": 3,
        "complete_four_bin_draws": 1,
        "incomplete_draws": 2,
        "empty_draw_bins": {"0": 1, "1": 1},
        "nonempty_zero_mass_draw_bins": {"0": 0, "1": 0},
        "negative_age_cells": 1,
        "ages_above_50000_bp": 0,
    }


def test_present_zero_mass_is_separate_from_an_empty_bin() -> None:
    scores, population, support = score_draws(
        np.asarray([[0, 500]], dtype=float),
        np.asarray([[0, 0], [0, 1]], dtype=np.int64),
        np.asarray([[[1, 0], [0, 1]]], dtype=float),
        (0, 1),
    )
    assert np.all(np.isnan(scores))
    np.testing.assert_array_equal(support, [[[1, 0], [1, 1]]])
    assert population["empty_draw_bins"] == {"0": 0, "1": 0}
    assert population["nonempty_zero_mass_draw_bins"] == {"0": 1, "1": 0}


def test_fractional_counts_and_nonclosed_predictions_are_refused() -> None:
    ages = np.asarray([[0]], dtype=float)
    with pytest.raises(ValueError, match="nonnegative counts"):
        score_draws(ages, np.asarray([[0.5, 0.5]]), np.asarray([[[0.5, 0.5]]]), (0,))
    with pytest.raises(ValueError, match="not closed"):
        score_draws(
            ages, np.asarray([[1, 1]], dtype=np.int64), np.asarray([[[0.2, 0.2]]]), (0,)
        )
