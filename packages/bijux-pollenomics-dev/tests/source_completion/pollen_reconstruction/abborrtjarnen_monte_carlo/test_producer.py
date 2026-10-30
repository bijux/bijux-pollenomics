"""Preserve empirical-zero and invariant-target precision distinctions."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence.quadratic_forms import (
    scalar_axes,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_monte_carlo import (
    batch_means,
    inputs,
    producer,
)


def test_constant_observed_indicator_has_no_claim_of_zero_target_error() -> None:
    result = producer.probability_fields(16000, 16000, 0)
    assert result["complete_probability_mcse"] == 0
    assert (
        result["indicator_status"]
        == "empirically_constant_indicator_insufficient_transitions"
    )
    varied = producer.probability_fields(16000, 15999, 1e-8)
    assert (
        varied["indicator_status"] == "observed_indicator_variation_no_mixing_guarantee"
    )


def test_all_fifty_zero_variance_records_remain_empirical_diagnostics() -> None:
    result = producer.scalar_records(
        np.full(20, 0.2), np.zeros(50), batch_means.scalar_map()
    )
    assert len(result) == 50
    assert all(row["mcse"] == 0 for row in result)
    assert all(
        row["mcse_status"] == "empirically_zero_batch_variation_not_zero_target_error"
        for row in result
    )
    assert all(row["empirical_mean"] == 0 for row in result[20:])


def test_positive_standard_error_and_negative_variance_domains() -> None:
    assert producer.square_root(0.25) == 0.5
    for value in (-1e-30, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            producer.square_root(value)


def test_prospective_estimands_and_no_adaptive_gate_are_explicit() -> None:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads((repository / inputs.PROTOCOL).read_text())
    assert (
        "exactly defined empirical summaries"
        in protocol["estimands"]["finite_saved_population"]
    )
    assert "mu_pi=E_pi[I_C c]/P_pi(C)" in protocol["estimands"]["invariant_target"]
    assert (
        "not uncertainty about an exactly defined finite-ledger average"
        in protocol["estimands"]["finite_saved_population"]
    )
    design = protocol["batch_design"]
    assert (
        design["batch_size"] * design["batches_per_chain"]
        == design["rows_per_chain"]
        == 16000
    )
    assert protocol["convergence_or_precision_gate_adopted"] is False
    assert protocol["raw_count_or_age_inputs_read"] is False


def test_complete_synthetic_consumer_keeps_masked_clock_and_all_comparisons() -> None:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads((repository / inputs.PROTOCOL).read_text())
    mask = np.ones((2, 16000), dtype=bool)
    mask[1, -1] = False
    covers = np.full((2, 16000, 20), 0.2)
    block = (np.arange(16000) // 128) % 2
    for window in range(4):
        covers[:, :, window * 5] += block * 0.05
        covers[:, :, window * 5 + 3] -= block * 0.05
    covers[1, -1] = np.nan
    chains = [
        batch_means.prepare(values, defined, 128)
        for values, defined in zip(covers, mask, strict=True)
    ]
    observed = np.concatenate([a[m] for a, m in zip(covers, mask, strict=True)])
    mean = observed.mean(axis=0)
    scalar_mean = batch_means.scalar_map() @ mean
    source = {
        "chain_summaries": [
            {"seed": seed, "conditional_mean": a[m].mean(axis=0).tolist()}
            for seed, a, m in zip(inputs.SEEDS, covers, mask, strict=True)
        ],
        "conditional_on_complete": {
            "mean": mean.tolist(),
            "conditional_standard_deviation": [0.1] * 20,
            "contrasts": [
                {**identity, "mean_difference": value, "standard_deviation": 0.1}
                for identity, value in zip(
                    scalar_axes()[20:], scalar_mean[20:], strict=True
                )
            ],
        },
    }
    result = producer.summarize(chains, source, protocol)
    assert [row["complete"] for row in result["chains"]] == [16000, 15999]
    assert result["chains"][1]["batch_native_row_ranges"][-1] == [19374, 19501]
    assert result["pooled"]["undefined"] == 1
    assert result["summary"]["scalar_records"] == 200
    assert (
        len(result["pooled"]["scalars"])
        == len(result["chain_difference"]["scalars"])
        == 50
    )
    assert all(row["mcse"] == 0 for row in result["pooled"]["scalars"][20:])
    assert (
        result["chains"][0]["indicator_status"]
        == "empirically_constant_indicator_insufficient_transitions"
    )
    assert result["chains"][1]["complete_probability_mcse"] > 0
    assert result["pooled"]["scalars"][0]["mcse_to_mixture_spread_ratio"] > 0
