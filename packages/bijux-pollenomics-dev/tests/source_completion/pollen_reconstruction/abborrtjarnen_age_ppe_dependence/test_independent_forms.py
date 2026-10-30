"""Analytical controls for age-population weighting and closure derivatives."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import csv
from fractions import Fraction
import gzip
import io
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from .independent_quadratic_forms import (
    BINS,
    TAXON_IDS,
    Array,
    compare_forms,
    gradients,
    quadratic_forms,
    scalar_axes,
)
from .independent_sources import Inputs, component_axis, read_ledger


def test_closure_gradient_matches_exact_scalar_quotient_derivative() -> None:
    c = [
        Fraction(1, 10),
        Fraction(2, 10),
        Fraction(3, 10),
        Fraction(1, 4),
        Fraction(3, 20),
    ]
    ppe = np.array([2, 3, 4, 5, 1.0])
    sd = np.array([0.2, 0.3, 0.4, 0.5, 0])
    result = gradients(np.array([list(map(float, c)) * 4]), ppe, sd)
    exact = [
        [float(c[i] * (c[j] - int(i == j)) / 10) for j in range(4)] for i in range(5)
    ]
    np.testing.assert_allclose(result[0, :5], exact, rtol=0, atol=1e-17)
    np.testing.assert_allclose(
        result.reshape(1, 4, 5, 4).sum(axis=2), 0, rtol=0, atol=1e-17
    )


def test_poaceae_zero_parameter_sd_retains_positive_output_variance() -> None:
    cover = np.array([[0.2] * 20])
    result = quadratic_forms(cover, np.ones(5), np.array([0.1] * 4 + [0]))
    assert np.trace(result[4]) > 0
    assert np.trace(result[4]) == pytest.approx(4 * (0.2 * 0.2 * 0.1) ** 2)


def test_contrast_is_formed_before_outer_product() -> None:
    row = [0.1, 0.2, 0.3, 0.25, 0.15] * 4
    result = quadratic_forms(
        np.array([row, row]), np.ones(5), np.array([0.1] * 4 + [0])
    )
    assert np.trace(result[0]) > 0
    assert not result[20:].any()
    assert scalar_axes()[20] == {
        "kind": "contrast",
        "younger_window_id": 3,
        "older_window_id": 4,
        "taxon": "Betula",
        "native_taxon_id": 29,
    }


def test_unequal_chain_complete_counts_use_population_not_chain_weighting() -> None:
    a = [0.1, 0.2, 0.3, 0.25, 0.15] * 4
    b = [0.3, 0.1, 0.2, 0.3, 0.1] * 4
    ppe, sd = np.ones(5), np.array([0.1] * 4 + [0])
    expected = (
        2 * quadratic_forms(np.array([a]), ppe, sd)
        + quadratic_forms(np.array([b]), ppe, sd)
    ) / 3
    pooled = quadratic_forms(np.array([a, a, b]), ppe, sd)
    np.testing.assert_allclose(pooled, expected, rtol=1e-15, atol=1e-18)
    wrong = (
        quadratic_forms(np.array([a]), ppe, sd)
        + quadratic_forms(np.array([b]), ppe, sd)
    ) / 2
    assert np.max(np.abs(pooled - wrong)) > 1e-5


def test_q_correspondence_is_separate_from_exact_certificate_feasibility() -> None:
    expected = np.ones((50, 4, 4)) * 1e-4
    assert compare_forms(expected.copy(), expected) == 0
    corrupted = expected.copy()
    corrupted[0, 1, 2] += 1e-12
    with pytest.raises(ValueError, match="independent cover derivatives"):
        compare_forms(corrupted, expected)
    with pytest.raises(ValueError, match="axes/domain"):
        compare_forms(expected[:49], expected)


@pytest.mark.parametrize(
    "cover", [np.zeros((1, 20)), np.full((1, 20), np.nan), np.ones((1, 19))]
)
def test_invalid_saved_cover_domain_refuses(cover: Array) -> None:
    with pytest.raises(ValueError):
        gradients(cover, np.ones(5), np.array([0.1] * 4 + [0]))


@pytest.fixture
def ledger_control() -> tuple[list[dict[str, str]], dict[str, Any]]:
    rows = []
    support: dict[int, Counter[str]] = {b: Counter() for b in BINS}
    for seed in (11, 17):
        for native in range(2, 5):
            complete = not (seed == 17 and native == 4)
            row = {
                "seed": str(seed),
                "native_row": str(native),
                "complete": str(int(complete)),
            }
            for i, b in enumerate(BINS):
                defined = complete or b != 9
                status = "defined" if defined else "empty_native_window"
                support[b][status] += 1
                row[f"bin_{b}_status"] = status
                row[f"bin_{b}_sample_ids"] = f"[{i + 1}]" if defined else "[]"
                row[f"bin_{b}_sample_count"] = "1" if defined else "0"
                for taxon in TAXON_IDS:
                    row[f"cover_{b}_{taxon}"] = "0.2" if defined else ""
            rows.append(row)
    reference = {
        "component_axis": component_axis(),
        "sample_accounts": [{"sample_id": i} for i in range(1, 108)],
        "requested_draws": 6,
        "complete_draws": 5,
        "undefined_draws": 1,
        "chain_summaries": [
            {"seed": 11, "requested_draws": 3, "complete_draws": 3},
            {"seed": 17, "requested_draws": 3, "complete_draws": 2},
        ],
        "support_by_window": {
            str(b): {"status_counts": dict(support[b]), "probability_denominator": 6}
            for b in BINS
        },
    }
    return rows, reference


def encoded(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return gzip.compress(output.getvalue().encode())


def test_saved_ledger_preserves_unequal_chain_populations(
    ledger_control: tuple[list[dict[str, str]], dict[str, Any]],
) -> None:
    rows, reference = ledger_control
    observed = read_ledger(encoded(rows), reference, chain_rows=3, first_native_row=2)
    assert observed.rows == 6 and observed.covers.shape == (5, 20)
    assert observed.chains == {11: 3, 17: 2}


@pytest.mark.parametrize(
    "corruption", ["identity", "mask", "axis", "denominator", "member", "duplicate_row"]
)
def test_saved_ledger_corruptions_refuse(
    ledger_control: tuple[list[dict[str, str]], dict[str, Any]], corruption: str
) -> None:
    rows, reference = deepcopy(ledger_control)
    if corruption == "identity":
        rows[1]["native_row"] = "9"
    elif corruption == "mask":
        rows[-1]["complete"] = "1"
    elif corruption == "axis":
        reference["component_axis"][0]["native_taxon_id"] = 999
    elif corruption == "denominator":
        reference["complete_draws"] = 4
    elif corruption == "member":
        rows[0]["bin_3_sample_ids"] = "[999]"
    else:
        rows[-1] = dict(rows[-2])
    with pytest.raises(ValueError):
        read_ledger(encoded(rows), reference, chain_rows=3, first_native_row=2)


def test_mutated_qualified_input_refuses(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    path.write_bytes(b"{}")
    bound = Inputs({}, {}, b"", {path: b"{}"}, {})
    bound.unchanged()
    path.write_bytes(b'{"changed":true}')
    with pytest.raises(ValueError, match="input changed"):
        bound.unchanged()
